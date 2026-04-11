# CircuitMap — Changelog

---

## 2026-04-11 — Export PDF for Demo Mode

**What changed:** Export PDF now works for all demo scenarios without requiring `precompute_demo.py` to have been run.

- `main.py`: `download_report` for `demo_*` sessions checks `cache/demo/{scenario}.pdf` first, then generates a PDF on-the-fly from bundled report sections if none exists, and caches the result.
- `scripts/precompute_demo.py`: also copies the session PDF to `cache/demo/{scenario}.pdf` alongside PNGs.

---

## 2026-04-11 — Brain Visualization UI Cleanup

- Removed Low/High color scale legends from the visualization panel (no functional value).
- Removed 3D render mode toggle — visualization is now 2D only (Side by Side / Overlay).

---

## 2026-04-11 — Real Neurosynth v7 Implementation

**What changed:** Neurosynth data loading and analysis completely rewritten for the v7 dataset format.

The old Neurosynth 0.3.x API (`database.txt` / `features.txt`, `get_studies_by_coordinate()`) no longer exists. The v7 dataset uses a completely different file format.

**New format:**
- `data-neurosynth_version-7_coordinates.tsv.gz` — 507,891 MNI activation coordinates
- `data-neurosynth_version-7_metadata.tsv.gz` — 14,371 study records
- `data-neurosynth_version-7_vocab-terms_source-abstract_type-tfidf_features.npz` — sparse TF-IDF matrix (14,371 × 3,228)
- `data-neurosynth_version-7_vocab-terms_vocabulary.txt` — 3,228 terms

**`scripts/preload_neurosynth.py`:** Rewritten with correct v7 download URLs. Builds and pickles a dict-format dataset with pre-computed coordinate arrays.

**`services/neurosynth_service.py`:**
- `_get_dataset()`: loads v7 pickle, computes `coord_arr` (507,891 × 3 numpy array) on first load.
- `_disease_map_v7()`: selects studies by TF-IDF weight > 0.001 for the indication term, counts activations within 10 mm of each ROI, normalises to [0, 1].
- `_reverse_inference()`: finds activations within 10 mm of query ROI coordinates, collects study IDs, sums TF-IDF term weights, returns top terms.
- Both functions fall back to curated offline templates when the dataset is not present.

---

## 2026-04-11 — Real Implementations for All Data Services

Replaced hardcoded/degraded implementations with real ones. All services retain offline fallbacks for demo mode.

**ChEMBL (`services/chembl_service.py`):**
- Live ChEMBL API is now attempted first; bundled offline profiles are a last resort, not the first check.
- Chaetocin primary target corrected to `SUV39H1`; `HIF1A` moved to off-targets (per PRD).

**AHBA (`services/ahba_service.py`):**
- Replaced fuzzy region-name string matching with MNI spatial nearest-neighbour parcellation.
- `_parcellate_by_mni_coords()`: inverse-distance weighted average of all AHBA samples within 15 mm of each ROI coordinate. Uses `mni_x/y/z` columns from `SampleAnnot.csv`.

**RAG (`services/rag_service.py`):**
- Semantic search restored as the primary path (sentence-transformers `all-MiniLM-L6-v2` + ChromaDB cosine distance).
- Lexical token-overlap scoring kept as offline fallback.

---

## 2026-04-11 — Code Quality, Security, and API Hardening

**Security:**
- `_validate_session_id()` added: allowlist regex `^[a-zA-Z0-9_\-]{1,64}$` applied to all session_id path parameters before filesystem access.
- Map type validated against `{"expression", "disease"}` allowlist.

**API:**
- `/api/validate` returns `ValidateResponse` Pydantic model with `session_id`, `stream_url`, `mode`.
- `/api/demo/{scenario}` uses `DemoScenario` enum annotation.
- SSE stream: 15-second keepalive pings, 409 on duplicate consumer connection.

**Cleanup:**
- `asyncio.get_event_loop()` → `asyncio.get_running_loop()` (Python 3.10+ deprecation).
- `_executor.shutdown(wait=False)` on app teardown via FastAPI `lifespan` context.
- `cleanup_session_maps(session_id)` removes correlation store entries when a session ends.

---

## 2026-04-11 — Tests, CI, and Dockerfile

- **`backend/tests/test_api.py`**: 13 pytest tests — health, validate, demo validation, path traversal guards, duplicate SSE consumer guard, correlation cleanup, Chaetocin target assertion.
- **`.github/workflows/ci.yml`**: Backend lint + import check + pytest; frontend lint + build.
- **`backend/Dockerfile`**: Python 3.11-slim, single-worker constraint documented.

---

## 2026-04-11 — Integration and Bug Fixes

| # | File | Fix |
|---|------|-----|
| 1 | `agent/loop.py` | Report section headers normalized from PRD prose (`"Executive Summary"`) to snake_case keys (`executive_summary`) matching the frontend `ReportPanel`. |
| 2 | `agent/loop.py` | `confidence_update` SSE events now emitted by parsing the Confidence Assessment report section after `report_ready`. |
| 3 | `main.py` | `/api/demo/{scenario}` response includes `drug_query`, `query_type`, `indication` fields for form state hydration. |
| 4 | `agent/loop.py` | `max_tokens` stop reason now continues the loop with a continuation prompt instead of aborting. |
| 5 | `agent/loop.py` | Fallback report path runs if the model does not return the required report headers within the tool-call limit. |
| 6 | `hooks/useAgentSession.ts` | Consecutive `agent_thought` SSE chunks merged into one trace entry instead of flooding the trace panel. |
| 7 | `mocks/demoEvents.ts` | PDF URL separator corrected (`demo_alzheimers` with underscore, not hyphen). |
