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

from models.requests import ValidateRequest, DemoScenario
from models.responses import ValidateResponse, HealthResponse, AppConfigResponse

app = FastAPI(title="CircuitMap API", version="1.0.0")

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

@app.post("/api/validate")
async def validate(req: ValidateRequest) -> dict:
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
    }

    # Start agent loop in background task
    asyncio.create_task(
        _run_agent_for_session(session_id, req, queue)
    )

    return {
        "session_id": session_id,
        "stream_url": f"/api/stream/{session_id}",
        "mode": "live"
    }


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


# ── SSE Stream ────────────────────────────────────────────────────────────────

@app.get("/api/stream/{session_id}")
async def stream(session_id: str) -> EventSourceResponse:
    """SSE stream for a live agent session."""
    if session_id not in sessions:
        raise HTTPException(status_code=404, detail="Session not found")

    queue = sessions[session_id]["queue"]

    async def event_generator() -> AsyncGenerator[dict, None]:
        while True:
            try:
                event = await asyncio.wait_for(queue.get(), timeout=300.0)
            except asyncio.TimeoutError:
                yield {
                    "event": "error",
                    "data": json.dumps({
                        "message": "Session timeout. Please start a new validation.",
                        "recoverable": False
                    })
                }
                break

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
async def demo(scenario: str) -> dict:
    """Return pre-computed demo data for frontend playback."""
    if scenario not in DEMO_METADATA:
        raise HTTPException(
            status_code=400,
            detail=f"Scenario must be one of {list(DEMO_METADATA.keys())}"
        )

    demo_file = os.path.join(DEMO_CACHE_DIR, f"{scenario}.json")

    if not os.path.exists(demo_file):
        raise HTTPException(
            status_code=404,
            detail="Demo not precomputed. Run scripts/precompute_demo.py first."
        )

    with open(demo_file) as f:
        events = json.load(f)

    meta = DEMO_METADATA[scenario]
    return {
        "session_id": f"demo_{scenario}",
        "mode": "demo",
        "events": events,
        # Fields the frontend useAgentSession hook reads to populate form state
        "drug_query": meta["drug_query"],
        "query_type": meta["query_type"],
        "indication": meta["indication"],
        "expression_map_url": f"/api/maps/demo_{scenario}/expression.png",
        "disease_map_url":    f"/api/maps/demo_{scenario}/disease.png",
    }


# ── Brain Maps ────────────────────────────────────────────────────────────────

@app.get("/api/maps/{session_id}/{map_type}.png")
async def serve_map(session_id: str, map_type: str) -> FileResponse:
    """Serve brain map PNG. Checks demo cache first, then session dir."""
    if map_type not in ("expression", "disease"):
        raise HTTPException(status_code=400, detail="map_type must be 'expression' or 'disease'")

    # Strip 'demo_' prefix for demo cache lookup
    demo_scenario = session_id.replace("demo_", "")
    demo_path = os.path.join(DEMO_CACHE_DIR, f"{demo_scenario}_{map_type}.png")
    session_path = os.path.join(SESSIONS_DIR, session_id, f"{map_type}.png")

    for path in [demo_path, session_path]:
        if os.path.exists(path):
            return FileResponse(path, media_type="image/png")

    raise HTTPException(
        status_code=404,
        detail=f"Map '{map_type}' not found for session '{session_id}'"
    )


# ── PDF Download ──────────────────────────────────────────────────────────────

@app.get("/api/report/{session_id}/download")
async def download_report(session_id: str) -> FileResponse:
    """Download the generated PDF report for a session."""
    session_dir = os.path.join(SESSIONS_DIR, session_id)

    if not os.path.exists(session_dir):
        raise HTTPException(status_code=404, detail="Session not found")

    # Find any .pdf file in the session directory
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
