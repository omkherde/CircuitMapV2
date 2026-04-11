# CircuitMap — Two-Person Work Split

**Goal:** Divide the project so both developers can work in parallel with minimal merge conflicts.

---

## Person 1: Backend Engineer (Python)

**Focus:** FastAPI server, Claude agent loop, scientific data services

### Responsibilities

#### Core Agent System (`backend/agent/`)
- `loop.py` — Agentic loop implementation with Claude tool_use streaming
- `tools.py` — Tool execution dispatch and result formatting
- `tools_schema.py` — 6 tool JSON schemas (resolve_target, get_brain_expression, get_cognitive_associations, get_disease_map, compute_overlap, search_literature)
- `prompts.py` — System prompt from PRD §6.2

#### Scientific Services (`backend/services/`)
- `chembl_service.py` — ChEMBL + PubChem drug/target resolution
- `ahba_service.py` — Allen Human Brain Atlas queries via abagen + Nilearn visualization
- `neurosynth_service.py` — Neurosynth meta-analytic maps + cognitive decoding
- `correlation_service.py` — Spatial Pearson correlation + null permutation
- `rag_service.py` — ChromaDB vector store for PubMed abstracts
- `pdf_service.py` — ReportLab PDF generation

#### API Layer (`backend/`)
- `main.py` — FastAPI routes, CORS, session management
- `models/requests.py` — Pydantic input models
- `models/responses.py` — Pydantic SSE event models

#### Pre-Event Scripts (`backend/scripts/`)
- `preload_ahba.py` — Download AHBA dataset (~500MB)
- `preload_neurosynth.py` — Download Neurosynth database
- `build_rag_store.py` — Build ChromaDB with PubMed abstracts
- `precompute_demo.py` — Cache 3 demo scenarios

### Key Deliverables
1. Working `/api/validate` endpoint that starts agent session
2. Working `/api/stream/{id}` SSE endpoint emitting all event types
3. All 6 tools returning real data from scientific databases
4. PDF generation at `/api/report/{id}/download`
5. Demo mode with pre-computed scenarios

### Dependencies to Install
```bash
pip install anthropic fastapi uvicorn sse-starlette pydantic
pip install numpy pandas scipy nibabel nilearn abagen matplotlib
pip install chembl_webresource_client requests neurosynth
pip install chromadb sentence-transformers biopython reportlab pillow
```

---

## Person 2: Frontend Engineer (React/TypeScript)

**Focus:** React SPA, real-time UI, SSE event handling, visual polish

### Responsibilities

#### Core Components (`frontend/src/components/`)
- `Header.tsx` — CircuitMap wordmark + demo mode badge
- `InputPanel.tsx` — Drug input form (name/SMILES toggle, indication dropdown, validate button)
- `ReasoningTrace.tsx` — Streaming trace panel with auto-scroll
- `TraceEntry.tsx` — Single trace line with type-based styling (thought/tool_call/tool_result/confidence)
- `BrainMaps.tsx` — Side-by-side expression + disease map images
- `OverlapScore.tsx` — r value, percentile bar, color-coded badge
- `ConfidencePanel.tsx` — Three-row confidence display (target/circuit/literature)
- `ReportPanel.tsx` — Rendered report sections with markdown support
- `ExportButton.tsx` — PDF download trigger

#### Hooks (`frontend/src/hooks/`)
- `useAgentSession.ts` — POST /api/validate, manage session state
- `useAgentStream.ts` — SSE connection, parse events, update React state

#### Types & Utils (`frontend/src/`)
- `types/index.ts` — All TypeScript interfaces (TraceEvent, ReportSections, SessionState, etc.)
- `api/client.ts` — Axios instance with base URL config
- `utils/parseReport.ts` — Parse agent report text into section objects

#### Styling & Config
- `tailwind.config.ts` — Custom colors for trace types, fonts
- `App.tsx` — Three-panel layout (280px | flex | 340px)
- CSS animations for fade-in effects on trace entries and brain maps

### Key Deliverables
1. Three-panel layout matching PRD §8.1 wireframe
2. Real-time trace panel with color-coded event types
3. SSE integration that updates UI as events stream in
4. Brain map placeholders that swap to images when ready
5. Animated overlap score bar
6. Report panel that renders all 11 sections
7. Working PDF download button
8. Demo mode UI indicator

### Dependencies to Install
```bash
npm install react react-dom axios @tanstack/react-query clsx tailwind-merge
npm install -D typescript vite @vitejs/plugin-react tailwindcss autoprefixer postcss
```

---

## Shared Interfaces (Contract Between Frontend & Backend)

Both developers must agree on these SSE event formats before coding:

```typescript
// Event types emitted by backend, consumed by frontend
type TraceEventType =
  | 'agent_thought'      // { content: string }
  | 'tool_call'          // { tool: string, input: object }
  | 'tool_result'        // { tool: string, summary: string }
  | 'brain_map'          // { map_type: 'expression'|'disease', image_url: string }
  | 'overlap_score'      // { r: number, percentile: number, label: string }
  | 'confidence_update'  // { dimension: string, level: string, rationale: string }
  | 'report_ready'       // { report_sections: object }
  | 'pdf_ready'          // { pdf_url: string, filename: string }
  | 'error'              // { message: string, recoverable: boolean }
```

---

## Parallel Development Strategy

### Day 1: Foundation
- **Person 1:** Set up FastAPI skeleton, implement `resolve_target` and `get_brain_expression` tools
- **Person 2:** Scaffold React app, build InputPanel and ReasoningTrace components

### Day 2: Core Features
- **Person 1:** Complete remaining 4 tools, implement agentic loop with streaming
- **Person 2:** Implement SSE hook, BrainMaps component, OverlapScore visualization

### Day 3: Integration & Polish
- **Person 1:** PDF generation, demo mode caching, error handling
- **Person 2:** ReportPanel, ConfidencePanel, PDF download, UI polish

### Day 4: Demo Prep
- **Both:** End-to-end testing, pre-compute demo scenarios, rehearse presentation

---

## Communication Checkpoints

1. **After InputPanel + `/api/validate` done:** Test that form submission returns session_id
2. **After SSE streaming works:** Test that frontend receives agent_thought events
3. **After brain maps generate:** Test that image URLs load in BrainMaps component
4. **After report generation:** Test full end-to-end flow with PDF download

---

## Files That Should NOT Be Edited Simultaneously

To avoid merge conflicts:
- `backend/main.py` — Person 1 owns this
- `frontend/src/App.tsx` — Person 2 owns this
- `frontend/src/types/index.ts` — Agree on types early, then Person 2 owns

---

## Quick Reference: Who Owns What

| Area | Owner |
|------|-------|
| Python backend | Person 1 |
| Claude agent integration | Person 1 |
| Scientific libraries (abagen, nilearn, neurosynth) | Person 1 |
| React frontend | Person 2 |
| SSE event handling | Person 2 |
| UI/UX and styling | Person 2 |
| API contract (SSE events) | Both — agree first |
| Demo scenario content | Both — test together |
