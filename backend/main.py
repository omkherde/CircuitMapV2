"""
main.py — CircuitMap FastAPI application.

Endpoints:
  POST /api/validate        — Start an agent session
  GET  /api/stream/{id}     — SSE stream for a session
  GET  /api/demo/{scenario} — Pre-computed demo scenario
  GET  /api/maps/{id}/{type}.png — Serve brain map PNG
  GET  /api/report/{id}/download — Download PDF report
  GET  /api/health          — Health check
"""
import asyncio
import json
import os
import re
import time
import uuid
from pathlib import Path
from typing import AsyncGenerator

from dotenv import load_dotenv
load_dotenv()

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from sse_starlette.sse import EventSourceResponse
import uvicorn

# Allowlist regex for user-supplied path components to prevent traversal attacks
_SESSION_ID_RE = re.compile(r'^[a-zA-Z0-9_\-]{1,64}$')
_MAP_TYPE_ALLOWED = {"expression", "disease"}


def _validate_session_id(session_id: str) -> None:
    """Raise 400 if session_id contains anything outside [a-zA-Z0-9_-]."""
    if not _SESSION_ID_RE.match(session_id):
        raise HTTPException(status_code=400, detail="Invalid session_id")

from models.requests import ValidateRequest, DemoScenario
from models.responses import ValidateResponse, HealthResponse, AppConfigResponse

from contextlib import asynccontextmanager


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Manage application lifespan: startup and graceful shutdown."""
    yield
    # Graceful shutdown: close the thread-pool executor used by tools
    try:
        from agent.tools import _executor
        _executor.shutdown(wait=False)
    except Exception:
        pass


app = FastAPI(title="CircuitMap API", version="1.0.0", lifespan=lifespan)

# CORS must be added BEFORE any routes
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://localhost:3000",
        "http://127.0.0.1:5173",
        "http://127.0.0.1:3000",
    ],
    allow_credentials=True,
    allow_methods=["GET", "POST", "OPTIONS"],
    allow_headers=["*"],
    expose_headers=["Content-Type", "Cache-Control", "Connection"],
)

# In-memory session store — ephemeral, no persistence
sessions: dict[str, dict] = {}

SESSIONS_DIR = os.getenv("SESSIONS_DIR", "./sessions")
DEMO_CACHE_DIR = os.getenv("DEMO_CACHE_DIR", "./cache/demo")


def _env_text(name: str) -> str:
    return os.getenv(name, "").strip()


def _env_list(name: str) -> list[str]:
    raw = os.getenv(name, "")
    return [item.strip() for item in raw.split("|") if item.strip()]


def _get_live_app_config() -> dict:
    return {
        "header": {
            "app_name": _env_text("APP_DISPLAY_NAME"),
            "app_tagline": _env_text("APP_TAGLINE"),
            "system_status_label": _env_text("SYSTEM_STATUS_LABEL"),
        },
        "input_panel": {
            "title": _env_text("INPUT_PANEL_TITLE"),
            "drug_query_label": _env_text("DRUG_QUERY_LABEL"),
            "drug_name_placeholder": _env_text("DRUG_NAME_PLACEHOLDER"),
            "smiles_placeholder": _env_text("SMILES_PLACEHOLDER"),
            "query_type_labels": {
                "name": _env_text("QUERY_TYPE_NAME_LABEL"),
                "smiles": _env_text("QUERY_TYPE_SMILES_LABEL"),
            },
            "indication_label": _env_text("INDICATION_LABEL"),
            "indication_placeholder": _env_text("INDICATION_PLACEHOLDER"),
            "validate_button_label": _env_text("VALIDATE_BUTTON_LABEL"),
            "validating_button_label": _env_text("VALIDATING_BUTTON_LABEL"),
            "load_demo_button_label": _env_text("LOAD_DEMO_BUTTON_LABEL"),
            "indications": _env_list("LIVE_DISEASE_INDICATIONS"),
        },
        "confidence_panel": {
            "title": _env_text("CONFIDENCE_PANEL_TITLE"),
            "empty_state": _env_text("CONFIDENCE_EMPTY_STATE"),
            "dimension_labels": {
                "target_resolution": _env_text("CONFIDENCE_LABEL_TARGET_RESOLUTION"),
                "circuit_alignment": _env_text("CONFIDENCE_LABEL_CIRCUIT_ALIGNMENT"),
                "literature_support": _env_text("CONFIDENCE_LABEL_LITERATURE_SUPPORT"),
            },
        },
    }


# ── Health ────────────────────────────────────────────────────────────────────

@app.get("/api/config", response_model=AppConfigResponse)
async def app_config() -> dict:
    """Return live UI configuration so the frontend avoids baked-in values."""
    return _get_live_app_config()

@app.get("/api/health")
async def health() -> dict:
    """Health check. Indicates whether data caches are loaded."""
    ahba_loaded = False
    chroma_loaded = False
    neurosynth_loaded = False

    try:
        from services.ahba_service import ahba_data_ready
        ahba_loaded = ahba_data_ready()
    except Exception:
        pass

    try:
        from services.rag_service import rag_store_ready
        chroma_loaded = rag_store_ready()
    except Exception:
        pass

    try:
        from services.neurosynth_service import neurosynth_data_ready
        neurosynth_loaded = neurosynth_data_ready()
    except Exception:
        pass

    return {
        "status": "ok",
        "ahba_loaded": ahba_loaded,
        "chroma_loaded": chroma_loaded,
        "neurosynth_loaded": neurosynth_loaded,
    }


# ── Validate (start agent session) ───────────────────────────────────────────

@app.post("/api/validate", response_model=ValidateResponse)
async def validate(req: ValidateRequest) -> ValidateResponse:
    """Start an agent session. Returns session_id and stream_url immediately."""
    session_id = str(uuid.uuid4())
    queue: asyncio.Queue = asyncio.Queue()

    sessions[session_id] = {
        "queue": queue,
        "status": "pending",
        "drug_query": req.drug_query,
        "query_type": req.query_type.value,
        "indication": req.indication,
        "pdf_path": None,
        "consumers": 0,  # track active SSE consumers
    }

    # Start agent loop in background task
    asyncio.create_task(
        _run_agent_for_session(session_id, req, queue)
    )

    return ValidateResponse(
        session_id=session_id,
        stream_url=f"/api/stream/{session_id}",
        mode="live",
    )


async def _run_agent_for_session(
    session_id: str,
    req: ValidateRequest,
    queue: asyncio.Queue
) -> None:
    """Background task: runs the agent loop and feeds events to the queue."""
    from agent.loop import run_agent_session
    try:
        sessions[session_id]["status"] = "running"
        await run_agent_session(
            session_id=session_id,
            drug_query=req.drug_query,
            query_type=req.query_type.value,
            indication=req.indication,
            event_queue=queue
        )
        sessions[session_id]["status"] = "complete"
    except Exception as e:
        await queue.put({
            "type": "error",
            "message": str(e),
            "recoverable": False
        })
        sessions[session_id]["status"] = "error"
    finally:
        await queue.put({"type": "done", "timestamp": int(time.time())})  # Signal stream end
        # Evict this session's brain maps from the correlation store to prevent
        # unbounded memory growth under long-running single-worker deployments.
        try:
            from services.correlation_service import cleanup_session_maps
            cleanup_session_maps(session_id)
        except Exception:
            pass


# ── SSE Stream ────────────────────────────────────────────────────────────────

@app.get("/api/stream/{session_id}")
async def stream(session_id: str) -> EventSourceResponse:
    """SSE stream for a live agent session."""
    _validate_session_id(session_id)
    if session_id not in sessions:
        raise HTTPException(status_code=404, detail="Session not found")

    session = sessions[session_id]

    # Guard: reject a second simultaneous consumer to avoid event loss
    if session.get("consumers", 0) >= 1:
        raise HTTPException(
            status_code=409,
            detail="Another client is already streaming this session"
        )

    session["consumers"] = session.get("consumers", 0) + 1
    queue: asyncio.Queue = session["queue"]

    async def event_generator() -> AsyncGenerator[dict, None]:
        try:
            while True:
                try:
                    # Use a short timeout so we can send periodic keepalive pings
                    event = await asyncio.wait_for(queue.get(), timeout=15.0)
                except asyncio.TimeoutError:
                    # Send keepalive comment to prevent proxy timeouts
                    yield {"event": "ping", "data": json.dumps({"ts": int(time.time())})}
                    continue

                event_type = event.get("type", "message")
                data = {k: v for k, v in event.items() if k != "type"}

                if event_type == "done":
                    yield {
                        "event": "done",
                        "data": json.dumps(data, default=str)
                    }
                    break

                yield {
                    "event": event_type,
                    "data": json.dumps(data, default=str)
                }
        finally:
            # Release consumer slot so reconnects are possible after disconnect
            if session_id in sessions:
                sessions[session_id]["consumers"] = max(
                    0, sessions[session_id].get("consumers", 1) - 1
                )

    return EventSourceResponse(
        event_generator(),
        headers={
            "Cache-Control": "no-cache",
            "X-Accel-Buffering": "no",  # Disable Nginx buffering
        }
    )


# ── Demo ──────────────────────────────────────────────────────────────────────

# Demo scenario metadata — must match scripts/precompute_demo.py
DEMO_METADATA = {
    "alzheimers":    {"drug_query": "Chaetocin",  "query_type": "name", "indication": "Alzheimer's disease"},
    "schizophrenia": {"drug_query": "Tolcapone",  "query_type": "name", "indication": "schizophrenia"},
    "depression":    {"drug_query": "Vorinostat", "query_type": "name", "indication": "major depressive disorder"},
}

@app.get("/api/demo/{scenario}")
async def demo(scenario: DemoScenario) -> dict:
    """Return pre-computed demo data for frontend playback."""
    if scenario.value not in DEMO_METADATA:
        raise HTTPException(
            status_code=400,
            detail=f"Scenario must be one of {list(DEMO_METADATA.keys())}"
        )

    scenario_key = scenario.value
    demo_file = os.path.join(DEMO_CACHE_DIR, f"{scenario_key}.json")

    if not os.path.exists(demo_file):
        raise HTTPException(
            status_code=404,
            detail="Demo not precomputed. Run scripts/precompute_demo.py first."
        )

    with open(demo_file) as f:
        events = json.load(f)

    meta = DEMO_METADATA[scenario_key]
    return {
        "session_id": f"demo_{scenario_key}",
        "mode": "demo",
        "events": events,
        # Fields the frontend useAgentSession hook reads to populate form state
        "drug_query": meta["drug_query"],
        "query_type": meta["query_type"],
        "indication": meta["indication"],
        "expression_map_url": f"/api/maps/demo_{scenario_key}/expression.png",
        "disease_map_url":    f"/api/maps/demo_{scenario_key}/disease.png",
    }


# ── Brain Maps ────────────────────────────────────────────────────────────────

@app.get("/api/maps/{session_id}/{map_type}.png")
async def serve_map(session_id: str, map_type: str) -> FileResponse:
    """Serve brain map PNG. Checks demo cache first, then session dir."""
    # Validate both path components against allowlists before touching the filesystem
    _validate_session_id(session_id)
    if map_type not in _MAP_TYPE_ALLOWED:
        raise HTTPException(status_code=400, detail="map_type must be 'expression' or 'disease'")

    # Strip 'demo_' prefix for demo cache lookup
    demo_scenario = session_id.replace("demo_", "")
    # demo_scenario is derived from a validated session_id so it's already clean
    demo_path = os.path.join(DEMO_CACHE_DIR, f"{demo_scenario}_{map_type}.png")
    session_path = os.path.join(SESSIONS_DIR, session_id, f"{map_type}.png")

    for path in [demo_path, session_path]:
        if os.path.exists(path):
            return FileResponse(path, media_type="image/png")

    raise HTTPException(
        status_code=404,
        detail=f"Map '{map_type}' not found for session '{session_id}'"
    )


# ── Demo report sections (mirrors frontend demoEvents.ts) ─────────────────────

_DEMO_REPORT_SECTIONS: dict[str, dict] = {
    "alzheimers": {
        "executive_summary": (
            "Chaetocin, targeting SUV39H1 (Ki = 0.8 µM), shows promising circuit alignment with "
            "Alzheimer's disease pathology. The target is highly expressed in disease-affected regions "
            "including the hippocampus and entorhinal cortex, with a strong spatial correlation "
            "(r = 0.61, p89) to the disease atrophy pattern."
        ),
        "target_identification": (
            "Primary target: SUV39H1 (histone-lysine N-methyltransferase)\n"
            "Affinity: Ki = 0.8 µM\n"
            "Mechanism: Inhibits H3K9 trimethylation\n"
            "Source: ChEMBL bioactivity database"
        ),
        "expression_analysis": (
            "SUV39H1 shows enriched expression in limbic structures critical for memory:\n"
            "• Hippocampus: 98th percentile\n"
            "• Entorhinal cortex: 94th percentile\n"
            "• Prefrontal cortex: 87th percentile\n\n"
            "This expression pattern aligns with regions involved in memory formation and early "
            "Alzheimer's pathology."
        ),
        "spatial_overlap": (
            "Correlation coefficient: r = 0.61\n"
            "Percentile rank: 89th (compared to 1000 null permutations)\n\n"
            "This indicates that SUV39H1 expression is significantly higher in brain regions most "
            "affected by Alzheimer's disease, suggesting the target may engage disease-relevant "
            "neural circuits."
        ),
        "circuit_interpretation": (
            "The strong spatial overlap suggests Chaetocin could modulate epigenetic processes "
            "specifically in circuits affected by Alzheimer's. The hippocampal-entorhinal expression "
            "pattern is particularly relevant given these regions' role in episodic memory and their "
            "early vulnerability in AD progression."
        ),
        "off_target_risk": (
            "Chaetocin's therapeutic case is limited by multi-target activity and chemistry liabilities:\n"
            "• HIF1A pathway modulation may alter adaptive hypoxia responses\n"
            "• EHMT2/G9a inhibition broadens chromatin effects beyond SUV39H1\n"
            "• The epidithiodiketopiperazine scaffold may contribute ROS-mediated toxicity"
        ),
        "literature_context": (
            "Recent studies support SUV39H1's role in cognitive function:\n"
            "• Graff et al. (2012): H3K9 methylation regulates memory consolidation\n"
            "• Peleg et al. (2010): Histone modifications altered in aging hippocampus\n"
            "• Day & Bhattacharya (2019): Epigenetic mechanisms in Alzheimer's disease\n\n"
            "However, direct therapeutic evidence for SUV39H1 inhibition in AD is limited."
        ),
        "confidence_assessment": (
            "Target Resolution: HIGH - Well-characterized target with confirmed binding data\n"
            "Circuit Alignment: HIGH - Strong spatial correlation with disease pattern\n"
            "Literature Support: MODERATE - Mechanistic rationale exists but clinical validation lacking"
        ),
        "limitations": (
            "• In vitro binding data may not reflect in vivo target engagement\n"
            "• Blood-brain barrier penetration of Chaetocin unknown\n"
            "• Off-target effects on related methyltransferases not fully characterized\n"
            "• Spatial correlation does not prove causal therapeutic mechanism"
        ),
        "recommendations": (
            "• ADAS-Cog13 or equivalent episodic memory endpoint\n"
            "• Hippocampal MRI volumetry\n"
            "• Default mode network connectivity\n"
            "• Peripheral H3K9 methylation pharmacodynamic readout"
        ),
        "preclinical_validation": (
            "1. Evaluate BBB penetration and CNS pharmacokinetics\n"
            "2. Assess selectivity against related HMT enzymes\n"
            "3. Test in preclinical AD models for cognitive endpoints\n"
            "4. Consider prodrug strategies if CNS exposure is limited"
        ),
    },
    "schizophrenia": {
        "executive_summary": (
            "Tolcapone, a COMT inhibitor (Ki ≈ 1–10 nM), shows strong circuit alignment with "
            "schizophrenia pathology via prefrontal dopamine modulation. The Val158Met COMT "
            "polymorphism links target biology directly to disease susceptibility."
        ),
        "target_identification": (
            "Primary target: COMT (Catechol-O-methyltransferase)\n"
            "Affinity: Ki ≈ 1–10 nM\n"
            "Mechanism: Inhibits dopamine catabolism in prefrontal cortex\n"
            "Source: ChEMBL bioactivity database"
        ),
        "confidence_assessment": (
            "Target Resolution: HIGH - COMT well-characterized with confirmed binding data\n"
            "Circuit Alignment: HIGH - Val158Met polymorphism directly links COMT to schizophrenia PFC circuits\n"
            "Literature Support: HIGH - Extensive clinical evidence for COMT in schizophrenia"
        ),
        "limitations": (
            "• Liver toxicity risk limits systemic dosing\n"
            "• CNS penetration requires careful dose optimization\n"
            "• Peripheral COMT inhibition may confound central effects"
        ),
    },
    "depression": {
        "executive_summary": (
            "Vorinostat (HDAC inhibitor, IC50 ≈ 48 nM for HDAC2) shows moderate circuit alignment "
            "with major depressive disorder pathology. Epigenetic modulation in hippocampus and "
            "amygdala circuits relevant to mood regulation."
        ),
        "target_identification": (
            "Primary target: HDAC2 (Histone deacetylase 2)\n"
            "Affinity: IC50 ≈ 48 nM\n"
            "Mechanism: Pan-HDAC inhibition with HDAC1/2 preference\n"
            "Source: ChEMBL bioactivity database"
        ),
        "confidence_assessment": (
            "Target Resolution: MODERATE - HDAC2 is primary target but Vorinostat is pan-HDAC\n"
            "Circuit Alignment: MODERATE - Hippocampal/amygdala expression relevant but non-specific\n"
            "Literature Support: MODERATE - Preclinical evidence strong, clinical data limited"
        ),
        "limitations": (
            "• Pan-HDAC activity may produce broad off-target effects\n"
            "• Limited CNS penetration data for Vorinostat\n"
            "• Clinical evidence for HDAC inhibition in depression is preliminary"
        ),
    },
}

_DEMO_DRUG_MAP = {
    "alzheimers": ("Chaetocin", "SUV39H1", "Alzheimer's disease"),
    "schizophrenia": ("Tolcapone", "COMT", "Schizophrenia"),
    "depression": ("Vorinostat", "HDAC2", "Major depressive disorder"),
}

_DEMO_OVERLAP = {
    "alzheimers": {"r": 0.61, "percentile": 89, "label": "SUV39H1 expression vs Alzheimer's disease anatomy"},
    "schizophrenia": {"r": 0.74, "percentile": 94, "label": "COMT expression vs Schizophrenia anatomy"},
    "depression": {"r": 0.52, "percentile": 78, "label": "HDAC2 expression vs MDD anatomy"},
}


def _get_demo_pdf_path(scenario: str) -> str:
    """Return path where a demo PDF should be cached."""
    return os.path.join(DEMO_CACHE_DIR, f"{scenario}.pdf")


def _generate_demo_pdf(scenario: str) -> str:
    """Generate (and cache) a PDF for the given demo scenario. Returns file path."""
    from services.pdf_service import generate_pdf
    from datetime import date

    os.makedirs(DEMO_CACHE_DIR, exist_ok=True)

    _, target, indication = _DEMO_DRUG_MAP[scenario]
    report_sections = _DEMO_REPORT_SECTIONS[scenario]
    overlap = _DEMO_OVERLAP[scenario]

    expression_path = os.path.join(DEMO_CACHE_DIR, f"{scenario}_expression.png")
    disease_path = os.path.join(DEMO_CACHE_DIR, f"{scenario}_disease.png")

    # Use a stable session_id so the PDF lands in a predictable location
    pdf_session_id = f"demo_{scenario}"
    pdf_path = generate_pdf(
        session_id=pdf_session_id,
        report_sections=report_sections,
        target=target,
        indication=indication,
        expression_image_path=expression_path if os.path.exists(expression_path) else None,
        disease_image_path=disease_path if os.path.exists(disease_path) else None,
        overlap_score=overlap,
    )

    # Copy/move into demo cache so it survives session cleanup
    dest = _get_demo_pdf_path(scenario)
    import shutil
    shutil.copy2(pdf_path, dest)
    return dest


# ── PDF Download ──────────────────────────────────────────────────────────────

@app.get("/api/report/{session_id}/download")
async def download_report(session_id: str) -> FileResponse:
    """Download the generated PDF report for a session.

    For demo sessions (session_id starts with 'demo_') the PDF is served from
    the demo cache directory.  If no pre-generated file exists there, one is
    created on-the-fly from the hardcoded demo report sections so that Export
    PDF always works without needing precompute_demo.py to have been run.
    """
    _validate_session_id(session_id)

    # ── Demo session: check cache, then generate on-the-fly ──────────────────
    if session_id.startswith("demo_"):
        scenario = session_id[len("demo_"):]  # e.g. "alzheimers"
        if scenario in _DEMO_REPORT_SECTIONS:
            cached_pdf = _get_demo_pdf_path(scenario)
            if not os.path.exists(cached_pdf):
                try:
                    cached_pdf = await asyncio.get_running_loop().run_in_executor(
                        None, _generate_demo_pdf, scenario
                    )
                except Exception as exc:
                    raise HTTPException(
                        status_code=500,
                        detail=f"Failed to generate demo PDF: {exc}"
                    )
            _, drug, indication = _DEMO_DRUG_MAP[scenario]
            filename = f"CircuitMap_{drug}_{indication.replace(' ', '-')}.pdf"
            return FileResponse(
                path=cached_pdf,
                media_type="application/pdf",
                filename=filename,
                headers={"Content-Disposition": f"attachment; filename={filename}"}
            )

    # ── Live session: look for PDF in session directory ───────────────────────
    session_dir = os.path.join(SESSIONS_DIR, session_id)

    if not os.path.exists(session_dir):
        raise HTTPException(status_code=404, detail="Session not found")

    pdf_files = list(Path(session_dir).glob("*.pdf"))
    if not pdf_files:
        raise HTTPException(
            status_code=404,
            detail="PDF not yet generated for this session. Wait for 'pdf_ready' event."
        )

    pdf_path = str(pdf_files[0])
    filename = os.path.basename(pdf_path)

    return FileResponse(
        path=pdf_path,
        media_type="application/pdf",
        filename=filename,
        headers={"Content-Disposition": f"attachment; filename={filename}"}
    )


# ── Entry point ───────────────────────────────────────────────────────────────

if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host=os.getenv("HOST", "0.0.0.0"),
        port=int(os.getenv("PORT", "8000")),
        reload=True
    )
