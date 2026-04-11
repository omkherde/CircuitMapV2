# CircuitMap — Implementation Changelog

**Last updated:** 2026-04-11  
**Implemented by:** Claude Code (claude-sonnet-4-6)  
**Scope:** Developer A — Backend & Agent Core (`backend/` directory)

---

## Anthropic Rate-Limit Optimization — 2026-04-11

**Scope:** Reduce Anthropic token usage and model-turn count so live runs stay under tight org limits.

### Changes Made

| # | File(s) | Change |
|---|---------|--------|
| 1 | `backend/agent/prompts.py` | Replaced the long PRD-verbatim system prompt with a shorter operational prompt that preserves the reporting contract but explicitly tells the model to batch independent tool calls, avoid retries, and keep reasoning concise. |
| 2 | `backend/agent/tools_schema.py` | Shortened all tool and field descriptions to reduce repeated schema tokens on every Anthropic request. Also lowered default optional payload sizes for literature and cognitive-association requests. |
| 3 | `backend/agent/tools.py` | Added model-facing result compaction so Claude now receives only the fields needed for follow-up reasoning instead of the full raw tool payloads. Frontend SSE events still receive the richer full payloads. |
| 4 | `backend/agent/tools.py` | Lowered default `top_n` / `top_k` fallback values for optional tool outputs to reduce both tool payload size and follow-up prompt size. |
| 5 | `backend/agent/loop.py` | Reduced default Anthropic settings from `claude-opus-4-6`, `MAX_TOOL_CALLS=20`, and `max_tokens=4096` to smaller low-usage defaults: `claude-sonnet-4-6`, `MAX_TOOL_CALLS=5`, and `CLAUDE_MAX_OUTPUT_TOKENS=1024`. |
| 6 | `backend/agent/loop.py` | Added a small rate-limit retry path for Anthropic `429`s with configurable backoff, so the app waits once instead of immediately burning more requests through manual retries. |
| 7 | `backend/agent/loop.py` | Stopped replaying full assistant pre-tool reasoning back into the Anthropic conversation history; tool-use turns now preserve only the `tool_use` blocks needed for continuity. |
| 8 | `backend/agent/loop.py` | Tightened the initial user prompt and continuation prompts so the agent is explicitly steered toward fewer turns and fewer duplicate calls. |
| 9 | `backend/.env`, `backend/.env.example` | Added low-usage Anthropic tuning variables: `CLAUDE_MAX_OUTPUT_TOKENS`, `CLAUDE_MAX_API_RETRIES`, and `CLAUDE_RATE_LIMIT_BACKOFF_SECONDS`, and updated the default model/tool-call settings to match the optimized path. |

### Verification

- Backend Python compile check passed after the Anthropic loop and tool compaction changes.
- Frontend `npm run build` passed unchanged after the backend-only optimization pass.
- The optimized Anthropic defaults are now configurable entirely through `backend/.env` without further code edits.

## Live Config De-Hardcoding — 2026-04-11

**Scope:** Remove live-mode baked-in UI values and serve them from backend config, while intentionally keeping demo fixtures hardcoded.

### Changes Made

| # | File(s) | Change |
|---|---------|--------|
| 1 | `backend/main.py`, `backend/models/responses.py` | Added `/api/config` and a typed config response so the frontend can fetch live UI strings and the indication catalog from the backend instead of embedding them in React code. |
| 2 | `backend/.env`, `backend/.env.example` | Moved live-mode app text, form labels, confidence labels, and supported indication options into environment-driven config values. |
| 3 | `frontend/src/types/index.ts`, `frontend/src/api/client.ts`, `frontend/src/hooks/useAppConfig.ts`, `frontend/src/hooks/index.ts` | Added typed app-config support and a frontend config-loading hook. |
| 4 | `frontend/src/App.tsx` | Wired the app to load live config before rendering the live UI and now sets the browser document title from fetched config instead of a baked-in product string. |
| 5 | `frontend/src/components/Header.tsx`, `frontend/src/components/InputPanel.tsx`, `frontend/src/components/ConfidencePanel.tsx` | Removed live-mode hardcoded text and indication options from the header, input form, and confidence panel. These components now render from fetched config and show skeleton states while config is loading. |
| 6 | `frontend/src/hooks/useAgentSession.ts` | Removed hardcoded confidence labels from session initialization and now hydrates them from backend config. |
| 7 | `frontend/index.html` | Removed the baked-in app title so the runtime config can own the live-mode page title. |

### Notes

- Demo fixtures in `frontend/src/mocks/demoEvents.ts` and demo metadata remain intentionally hardcoded per request.

## Target Resolution Hardening — 2026-04-11

**Scope:** Prevent live sessions from stalling or going blank when drug-name or SMILES target resolution fails.

### Changes Made

| # | File(s) | Change |
|---|---------|--------|
| 1 | `backend/services/chembl_service.py` | Added faster failover behavior for target resolution, including explicit unresolved-target results when ChEMBL and PubChem are unavailable instead of returning only a raw error blob. |
| 2 | `backend/services/chembl_service.py` | Added a PubChem canonicalization path that can rescue SMILES and variant drug names by resolving them to candidate names before retrying ChEMBL target lookup. |
| 3 | `backend/services/chembl_service.py` | Added a configurable `TARGET_RESOLUTION_TIMEOUT_SECONDS` timeout to keep live sessions from hanging too long on external chemistry services. |
| 4 | `backend/agent/tools.py` | Preserved `resolve_target` notes and fallback metadata in the compact model-facing payload so unresolved-target sessions still have enough information to generate a final report. |
| 5 | `backend/agent/loop.py` | The agent loop now stores failed `resolve_target` outputs too, which allows the fallback report path to render a limitations-focused report instead of ending with an empty report panel. |
| 6 | `backend/agent/prompts.py`, `backend/agent/loop.py` | Taught the agent and fallback report builder to stop anatomy analysis when the target cannot be resolved and to finish with an explicit unresolved-target explanation. |
| 7 | `backend/.env`, `backend/.env.example` | Added the new target-resolution timeout config. |

### Verification

- Local service smoke tests confirmed:
  - known drug-name fallback still resolves (`donepezil` → `ACHE`)
  - arbitrary drug names now return an explicit unresolved-target result instead of an empty hard failure
  - arbitrary SMILES now return an explicit unresolved-target result instead of an empty hard failure when external chemistry services are unavailable

## Debugging Continuation — 2026-04-11

**Scope:** End-to-end backend/frontend debugging continuation from the failed AI-agent run.

### Changes Made

| # | File(s) | Change |
|---|---------|--------|
| 1 | `backend/services/ahba_service.py` | Replaced the broken `abagen.get_expression_data(atlas=None)` path with a direct donor-averaged AHBA microarray loader. Brain-expression calls now work from the cached donor files already in `backend/cache/ahba_data/`. |
| 2 | `backend/services/neurosynth_service.py` | Added curated offline disease-map templates and PNG generation for supported indications when the Neurosynth dataset is missing. Disease-map requests no longer hard-fail in offline/dev mode. |
| 3 | `backend/services/rag_service.py` | Removed the runtime dependency on downloading the Hugging Face embedding model at query time. Literature search now falls back to local lexical ranking over the cached Chroma documents. |
| 4 | `backend/services/chembl_service.py` | Hardened live ChEMBL lookup error handling and added bundled fallback target profiles for common/demo molecules so network failures no longer crash target resolution. |
| 5 | `backend/main.py` | Fixed SSE completion by emitting an actual `done` event before closing the stream. Also switched `/api/health` to real cache-readiness checks instead of fragile in-memory flags. |
| 6 | `backend/services/pdf_service.py` | Updated PDF rendering to understand normalized report-section keys, so live/fallback reports now populate the PDF body instead of producing near-empty exports. |
| 7 | `backend/agent/loop.py` | Fixed multiple agent-loop control-flow bugs: tool-limit wrap-up now actually gets a follow-up turn, skipped `tool_use` blocks receive synthetic `tool_result`s, `max_tokens` responses continue instead of aborting, and a deterministic fallback report/PDF path now runs if the model does not return the required final marker/headers. |
| 8 | `backend/models/responses.py` | Added `neurosynth_loaded` to the health response shape to match the improved backend health payload. |
| 9 | `frontend/src/types/index.ts`, `frontend/src/components/ReportPanel.tsx`, `frontend/src/utils/parseReport.ts`, `frontend/src/mocks/demoEvents.ts` | Aligned the frontend report schema and labels with the backend’s real report sections (`off_target_risk`, `preclinical_validation`, etc.) while keeping legacy/demo compatibility. |
| 10 | `frontend/src/hooks/useAgentStream.ts` | Prevented normal SSE shutdown from being surfaced as a false “Connection to server lost” error when the stream closes cleanly. |
| 11 | `frontend/package-lock.json`, `frontend/node_modules` | Installed the missing UI/runtime packages already declared in `package.json` so the current frontend source tree builds again. |
| 12 | `frontend/src/components/ReportPanel.tsx` | Resolved the file’s stale unmerged git state after reconciling its section mapping with the fixed backend report contract. |

### Verification

- Backend Python compile check passed for all modified backend modules.
- `get_expression_map('HIF1A')` succeeded using the local AHBA cache and generated `backend/sessions/smoke/expression.png`.
- `get_disease_map('alzheimer')` succeeded via the offline fallback template and generated `backend/sessions/smoke/disease.png`.
- `search_literature('Chaetocin Alzheimer', 3)` returned results from the local Chroma cache without needing Hugging Face downloads.
- `compute_overlap(...)` succeeded on generated expression/disease maps.
- PDF generation succeeded with normalized report-section keys.
- `/api/health` returned healthy cache status through FastAPI `TestClient`.
- SSE stream smoke test confirmed `event: done` is now emitted correctly.
- Frontend `npm run build` passed after dependency sync.
- Frontend `npm run lint` passed with 2 existing `react-refresh/only-export-components` warnings in `frontend/src/components/ui/badge.tsx` and `frontend/src/components/ui/button.tsx`.
- Live external smoke checks passed for:
  - ChEMBL target resolution for `Chaetocin`
  - Anthropic credential/auth path with `.env` loaded
  - Backend agent loop with `MAX_TOOL_CALLS=5`, which now emits `report_ready` and `pdf_ready` through the fallback-report path even under forced wrap-up conditions

### Notes

- The offline disease-map and target-resolution fallbacks are resilience features for dev/offline execution; when real external datasets/services are available, the live paths are still preferred.
- The frontend lint warnings are non-blocking and were left unchanged because they are unrelated to the integration failures.

## Integration Pass — 2026-04-11

**Scope:** Frontend ↔ Backend integration audit and fixes.

### Bugs Fixed

| # | File | Bug | Fix |
|---|------|-----|-----|
| 1 | `backend/requirements.txt` | `uuid==1.30` is not a real PyPI package (Python `uuid` is stdlib). `pip install` would fail. | Removed the line. |
| 2 | `backend/agent/loop.py` | `_parse_report_sections()` emitted raw PRD headers (`"Executive Summary"`) but frontend `ReportPanel` expected snake_case keys (`executive_summary`). Report panel was always blank in live mode. | Added `HEADER_TO_KEY` normalization map; all 11 PRD sections now map to the correct frontend keys. |
| 3 | `backend/agent/loop.py` | `confidence_update` SSE events were never emitted during a live run, so the Confidence Panel stayed PENDING permanently. | Added `_extract_confidence_events()` that parses the `Confidence Assessment` report section after `report_ready` and emits one `confidence_update` event per dimension. |
| 4 | `backend/main.py` | `/api/demo/{scenario}` response was missing `drug_query`, `query_type`, `indication` fields that `useAgentSession.ts` reads to populate form state. | Added those three fields (pulled from `DEMO_METADATA` dict). Also centralized the scenario metadata to ensure consistency with `precompute_demo.py`. |
| 5 | `frontend/src/hooks/useAgentSession.ts` | Backend streams hundreds of tiny `agent_thought` chunks; every chunk became its own `<TraceEntry>` div, making the trace unreadable. | Consecutive `agent_thought` events are now merged into the previous entry (content concatenation) before the switch-case handling. |
| 6 | `frontend/src/hooks/useAgentSession.ts` | `demoMetadata` used Clozapine/Ketamine for schizophrenia/depression, but `precompute_demo.py` runs Tolcapone/Vorinostat (per PRD). Drug shown in form during demo was wrong. | Updated to Tolcapone / Vorinostat / Major depressive disorder. |
| 7 | `frontend/src/mocks/demoEvents.ts` | Fallback mock events for schizophrenia and depression used wrong drugs. PDF URL used `demo-alzheimers` (hyphen) but backend uses `demo_alzheimers` (underscore). | Updated mock drug names and corrected URL separator. |
| 8 | `frontend/src/App.tsx` | Export PDF button shown after demo completes, but no actual PDF exists (precompute_demo.py generates one only if run). Click would 404. | Button is now hidden when `state.isDemo === true`. |
| 9 | `backend/.env` | File was missing. Server wouldn't start without `ANTHROPIC_API_KEY`. | Created with placeholder and clear TODO comment. |
| 10 | `frontend/.env` | File was missing. Created from `.env.example` with `VITE_API_BASE_URL=` (empty = use Vite proxy). | Created. |

### No-action items (verified OK)

- **Tailwind v4 config**: `tailwind.config.ts` is unused by Tailwind v4, but all custom classes (`bg-background`, `animate-fade-in`, etc.) are defined directly in `src/index.css` via raw CSS. Harmless.
- **SSE CORS**: `EventSource` uses GET; no preflight needed. Backend CORS is configured correctly.
- **Vite proxy**: `vite.config.ts` proxies `/api → localhost:8000`. `VITE_API_BASE_URL=` (empty) means all API calls go through the proxy, which correctly forwards SSE.
- **PDF download**: `ExportButton` creates a same-origin `<a href="/api/report/...">` which the Vite proxy forwards to the backend. Works in dev.

---

## Status: BACKEND COMPLETE

All Developer A files have been implemented. The backend is ready for:
1. Environment setup (create venv, `pip install -r requirements.txt`)
2. Data preloading (run the 4 scripts in order)
3. Server startup (`python main.py` from `backend/`)

---

## Files Created

### Configuration
- [x] `backend/requirements.txt` — All dependencies pinned with `==` (exact versions from techstack.md)
- [x] `backend/.env.example` — All environment variables documented

### Models
- [x] `backend/models/__init__.py`
- [x] `backend/models/requests.py` — `ValidateRequest`, `QueryType`, `DemoScenario` Pydantic models
- [x] `backend/models/responses.py` — `ValidateResponse`, `HealthResponse`, `DemoResponse`, `TraceEventType`

### Services
- [x] `backend/services/__init__.py`
- [x] `backend/services/chembl_service.py` — ChEMBL drug target resolution with PubChem fallback
- [x] `backend/services/ahba_service.py` — AHBA expression data via abagen, PNG generation (Agg backend set)
- [x] `backend/services/neurosynth_service.py` — Disease maps + curated cognitive associations lookup
- [x] `backend/services/correlation_service.py` — Pearson correlation + 1000-perm null (seed=42)
- [x] `backend/services/rag_service.py` — ChromaDB PubMed RAG search
- [x] `backend/services/pdf_service.py` — ReportLab A4 PDF with all 11 sections + brain maps

### Agent Core
- [x] `backend/agent/__init__.py`
- [x] `backend/agent/prompts.py` — Verbatim system prompt from PRD §6.2
- [x] `backend/agent/tools_schema.py` — All 6 tool schemas verbatim from PRD §6.3
- [x] `backend/agent/tools.py` — Async bridge wrapping sync services in ThreadPoolExecutor
- [x] `backend/agent/loop.py` — Full agentic loop: streaming, tool_use handling, report parsing, PDF trigger

### Application
- [x] `backend/main.py` — FastAPI with CORS, all 6 endpoints, SSE via `sse_starlette`

### Scripts
- [x] `backend/scripts/preload_ahba.py` — Download ~500MB AHBA data (run before hackathon)
- [x] `backend/scripts/preload_neurosynth.py` — Download Neurosynth database + build pickle
- [x] `backend/scripts/build_rag_store.py` — Fetch PubMed abstracts + build ChromaDB
- [x] `backend/scripts/precompute_demo.py` — Run all 3 demo scenarios and cache results

### Directory Skeleton
- [x] `backend/cache/ahba_data/` — Populated by `preload_ahba.py`
- [x] `backend/cache/chroma_db/` — Populated by `build_rag_store.py`
- [x] `backend/cache/neurosynth_data/` — Populated by `preload_neurosynth.py`
- [x] `backend/cache/demo/` — Populated by `precompute_demo.py`
- [x] `backend/sessions/` — Runtime session storage (auto-created per session)

---

## Files NOT Created (Developer B scope)

Everything under `frontend/` is Developer B's responsibility per `split.md`.

---

## Next Steps for Continuation

### Step 1: Environment Setup (do this first)
```bash
cd /Users/amalsameel/yconic/backend
python3.11 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

Verify:
```bash
python -c "import anthropic, fastapi, abagen, nilearn, neurosynth, chromadb, chembl_webresource_client; print('All imports OK')"
```

### Step 2: Create .env
```bash
cp .env.example .env
# Edit .env and add your ANTHROPIC_API_KEY
```

### Step 3: Run Data Preloading Scripts (takes 1-2 hours total, needs internet)
```bash
cd backend
python scripts/preload_ahba.py          # ~15 min, ~500MB
python scripts/preload_neurosynth.py    # ~10 min
python scripts/build_rag_store.py       # ~30 min
```

### Step 4: Test Each Service
```bash
python -c "from services.chembl_service import resolve_target; print(resolve_target('Donepezil', 'name'))"
python -c "from services.ahba_service import get_expression_map; print(get_expression_map('COMT','test'))"
python -c "from services.neurosynth_service import get_disease_map; print(get_disease_map('alzheimer','test'))"
python -c "from services.rag_service import search_literature; print(search_literature('SUV39H1 Alzheimer'))"
```

### Step 5: Start the Server
```bash
python main.py
# OR: uvicorn main:app --host 0.0.0.0 --port 8000 --reload
curl http://localhost:8000/api/health
```

### Step 6: Precompute Demo Scenarios (night before hackathon)
```bash
python scripts/precompute_demo.py
# Takes 10-30 minutes. Requires API key and all data loaded.
```

### Step 7: Frontend (Developer B)
Developer B should scaffold `frontend/` per `split.md`. The API contract is unchanged from `prd.md §7`.

---

## Known Issues / Watch Points

1. **`abagen.get_expression_data` first call is slow** (~30-60 seconds) — the expression cache is loaded once at module level. Subsequent calls are instant.

2. **Neurosynth pickle compatibility** — If `pickle.load` fails, the service falls back to loading from raw `.txt` files. Both paths are implemented.

3. **matplotlib Agg backend** — `matplotlib.use('Agg')` is set at the top of both `ahba_service.py` and `neurosynth_service.py`. If you import these in tests, import order matters. Always import them before any GUI matplotlib.

4. **ChEMBL rate limiting** — ChEMBL's REST API can be slow (5-30 seconds per query). This is handled by running in `ThreadPoolExecutor` (non-blocking for FastAPI).

5. **RAG store empty** — If `build_rag_store.py` hasn't been run, `search_literature` returns a graceful error dict (not an exception). The agent handles this gracefully.

6. **CORS for SSE** — The `EventSourceResponse` uses GET, so no CORS preflight. CORS middleware is configured to expose all necessary headers.

7. **PDF path** — `pdf_service.py` uses `os.path.abspath()` for all image paths. If session images don't exist, they are skipped gracefully in the PDF.

8. **Demo map serving** — `/api/maps/demo_{scenario}/expression.png` is served by stripping the `demo_` prefix to look up `{scenario}_expression.png` in the demo cache dir.

---

## API Contract (for Developer B reference)

| Endpoint | Method | Status |
|---|---|---|
| `/api/validate` | POST | ✅ Implemented |
| `/api/stream/{session_id}` | GET SSE | ✅ Implemented |
| `/api/demo/{scenario}` | GET | ✅ Implemented |
| `/api/maps/{session_id}/{map_type}.png` | GET | ✅ Implemented |
| `/api/report/{session_id}/download` | GET | ✅ Implemented |
| `/api/health` | GET | ✅ Implemented |

SSE event types emitted: `agent_thought`, `tool_call`, `tool_result`, `brain_map`, `overlap_score`, `report_ready`, `pdf_ready`, `error`

Note: `confidence_update` events are NOT emitted by the current loop implementation.  
The agent emits confidence assessments inline in `agent_thought` text.  
If Developer B needs `confidence_update` as a discrete SSE event, add parsing in `agent/loop.py`  
by scanning thought text for "CONFIDENCE" keywords and emitting the event.
