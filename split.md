# CircuitMap - Two Developer Work Split

## Overview
This document outlines the work distribution between two developers for the CircuitMap CNS drug target validation agent.

---

## Developer A: Backend & Agent Core

**Directory Ownership:** `backend/` (all files)

### Phase 0: Environment Setup (2 hours)
- [ ] Create project directory structure
- [ ] Create `requirements.txt` with pinned versions
- [ ] Create `.env.example` with all environment variables
- [ ] Verify Python 3.11 environment and imports

### Phase 1: Pre-Event Scripts
- [ ] `scripts/preload_ahba.py` - Download AHBA data (~500MB)
- [ ] `scripts/preload_neurosynth.py` - Download Neurosynth database
- [ ] `scripts/build_rag_store.py` - Build ChromaDB with PubMed abstracts
- [ ] `scripts/precompute_demo.py` - Generate all 3 demo scenarios

### Phase 2: Services Layer
Build in order with `if __name__ == "__main__"` test blocks:

1. [ ] **`services/chembl_service.py`**
   - `resolve_target(query, query_type)` function
   - ChEMBL + PubChem fallback lookup

2. [ ] **`services/ahba_service.py`**
   - `get_expression_map(gene_name, session_id)` function
   - Set `matplotlib.use('Agg')` FIRST
   - Generate regional bar chart PNG

3. [ ] **`services/neurosynth_service.py`**
   - `get_disease_map(indication, session_id)` function
   - `get_cognitive_associations(regions, top_n)` function

4. [ ] **`services/correlation_service.py`**
   - `store_parcellated_map(map_id, values)` function
   - `compute_overlap(map1_id, map2_id, label)` function
   - 1000 permutation null distribution (seed=42)

5. [ ] **`services/rag_service.py`**
   - `search_literature(query, top_k)` function
   - ChromaDB PersistentClient singleton

6. [ ] **`services/pdf_service.py`**
   - `generate_pdf(session_id, report_sections, maps, target, indication)` function
   - ReportLab A4 format with all 11 report sections

### Phase 3: Agent Core
- [ ] **`agent/prompts.py`** - System prompt from PRD §6.2
- [ ] **`agent/tools_schema.py`** - All 6 tool schemas from PRD §6.3
- [ ] **`agent/tools.py`** - Bridge between Claude tool calls and services
- [ ] **`agent/loop.py`** - Main agentic loop with streaming

### Phase 4: FastAPI Application
- [ ] **`models/requests.py`** - `ValidateRequest`, `QueryType`, `DemoScenario`
- [ ] **`models/responses.py`** - SSE event Pydantic models
- [ ] **`main.py`** - FastAPI app with all endpoints:
  - `POST /api/validate`
  - `GET /api/stream/{session_id}`
  - `GET /api/demo/{scenario}`
  - `GET /api/maps/{session_id}/{map_type}.png`
  - `GET /api/report/{session_id}/download`
  - `GET /api/health`

### Files Owned
```
backend/
├── main.py
├── requirements.txt
├── .env.example
├── agent/
│   ├── __init__.py
│   ├── loop.py
│   ├── tools.py
│   ├── tools_schema.py
│   └── prompts.py
├── services/
│   ├── __init__.py
│   ├── chembl_service.py
│   ├── ahba_service.py
│   ├── neurosynth_service.py
│   ├── correlation_service.py
│   ├── rag_service.py
│   └── pdf_service.py
├── models/
│   ├── __init__.py
│   ├── requests.py
│   └── responses.py
├── scripts/
│   ├── preload_ahba.py
│   ├── preload_neurosynth.py
│   ├── build_rag_store.py
│   └── precompute_demo.py
├── cache/
└── sessions/
```

### Testing Commands
```bash
python -c "from services.chembl_service import resolve_target; print(resolve_target('Donepezil', 'name'))"
python -c "from services.ahba_service import get_expression_map; print(get_expression_map('COMT','test'))"
python -c "from services.neurosynth_service import get_disease_map; print(get_disease_map('alzheimer','test'))"
python -c "from services.rag_service import search_literature; print(search_literature('SUV39H1 Alzheimer'))"
curl http://localhost:8000/api/health
```

---

## Developer B: Frontend & Integration

**Directory Ownership:** `frontend/` (all files)

### Phase 0: Frontend Scaffold (2 hours)
- [ ] Initialize Vite + React + TypeScript project
- [ ] Install dependencies: axios, @tanstack/react-query, clsx, tailwind-merge
- [ ] Configure Tailwind CSS with custom colors for trace events
- [ ] Configure Vite proxy for `/api` to `localhost:8000`
- [ ] Create `.env` with `VITE_API_BASE_URL`

### Phase 1: Types & API Client
- [ ] **`src/types/index.ts`** - All TypeScript interfaces:
  - `TraceEvent`, `TraceEventType`
  - `ConfidenceLevel`, `ConfidenceDimension`
  - `ReportSections`, `SessionState`
  - `QueryType`, `DemoScenario`

- [ ] **`src/api/client.ts`** - Axios instance with base URL

### Phase 2: Core Hooks
- [ ] **`src/hooks/useAgentSession.ts`**
  - `startSession(drug_query, query_type, indication)`
  - `loadDemo(scenario)`

- [ ] **`src/hooks/useAgentStream.ts`**
  - Connect to SSE endpoint
  - Parse events with named event listeners
  - Handle all 9 event types
  - Cleanup on unmount

### Phase 3: UI Components
Build in order:

1. [ ] **`src/components/Header.tsx`**
   - "CircuitMap" wordmark (20px, weight 600)
   - Demo mode badge (amber, top-right)

2. [ ] **`src/components/InputPanel.tsx`**
   - Drug molecule text input (monospace for SMILES)
   - Radio toggle: "Drug name" | "SMILES"
   - Disease indication dropdown (12 options)
   - "Validate Target" primary button
   - "Load Demo" secondary button

3. [ ] **`src/components/TraceEntry.tsx`**
   - Single trace line with type-based styling
   - Fade-in animation (150ms)

4. [ ] **`src/components/ReasoningTrace.tsx`**
   - Container for trace entries (320px height, scroll)
   - Auto-scroll to bottom
   - Pulsing dot indicator while thinking

5. [ ] **`src/components/BrainMaps.tsx`**
   - Two panels side by side
   - Gray placeholder before images load
   - Smooth fade-in on load (300ms)

6. [ ] **`src/components/OverlapScore.tsx`**
   - r value display
   - Percentile badge with color coding
   - Animated bar fill

7. [ ] **`src/components/ConfidencePanel.tsx`**
   - Three rows with badges
   - Collapsed initially, expands on first update

8. [ ] **`src/components/ReportPanel.tsx`**
   - Render all 11 report sections
   - Scrollable container

9. [ ] **`src/components/ExportButton.tsx`**
   - "Export Report PDF" button
   - Triggers download

### Phase 4: App Integration
- [ ] **`src/utils/parseReport.ts`** - Parse agent report into 11 sections
- [ ] **`src/App.tsx`** - Three-panel layout, wire all components
- [ ] Demo mode playback at 800ms intervals

### Files Owned
```
frontend/
├── index.html
├── package.json
├── vite.config.ts
├── tailwind.config.ts
├── tsconfig.json
├── .env
├── public/
│   └── logo.svg
└── src/
    ├── main.tsx
    ├── App.tsx
    ├── index.css
    ├── components/
    │   ├── Header.tsx
    │   ├── InputPanel.tsx
    │   ├── ReasoningTrace.tsx
    │   ├── TraceEntry.tsx
    │   ├── BrainMaps.tsx
    │   ├── OverlapScore.tsx
    │   ├── ConfidencePanel.tsx
    │   ├── ReportPanel.tsx
    │   └── ExportButton.tsx
    ├── hooks/
    │   ├── useAgentSession.ts
    │   └── useAgentStream.ts
    ├── types/
    │   └── index.ts
    ├── api/
    │   └── client.ts
    └── utils/
        └── parseReport.ts
```

### Testing
- Use mock data until backend is ready
- Test SSE with browser DevTools Network tab
- Verify auto-scroll behavior
- Test demo mode playback timing

---

## Shared Interface Contract

### API Endpoints

| Endpoint | Method | Request | Response |
|----------|--------|---------|----------|
| `/api/validate` | POST | `{ drug_query, query_type, indication }` | `{ session_id, stream_url, mode }` |
| `/api/stream/{session_id}` | GET | - | SSE stream |
| `/api/demo/{scenario}` | GET | - | Pre-computed demo data |
| `/api/maps/{session_id}/{map_type}.png` | GET | - | PNG image |
| `/api/report/{session_id}/download` | GET | - | PDF file |
| `/api/health` | GET | - | `{ status, ahba_loaded, chroma_loaded }` |

### SSE Event Types

| Event | Data Fields |
|-------|-------------|
| `agent_thought` | `content`, `timestamp` |
| `tool_call` | `tool`, `input`, `timestamp` |
| `tool_result` | `tool`, `summary`, `result?`, `timestamp` |
| `brain_map` | `map_type`, `map_id`, `image_url`, `top_regions`, `timestamp` |
| `overlap_score` | `r`, `percentile`, `label`, `interpretation`, `timestamp` |
| `confidence_update` | `dimension`, `level`, `rationale`, `timestamp` |
| `report_ready` | `report_sections`, `timestamp` |
| `pdf_ready` | `pdf_url`, `filename`, `timestamp` |
| `error` | `message`, `recoverable`, `timestamp` |

---

## Sync Schedule

### Day 1 End-of-Day
- **Dev A**: Backend health endpoint working, chembl + ahba services tested
- **Dev B**: Frontend scaffold done, types defined, input form working with mock
- **Integration test**: Frontend can hit `/api/health`

### Day 2 Morning
- **Dev A**: All services complete, basic SSE streaming working
- **Dev B**: All components built, SSE hook ready
- **Integration test**: Frontend connects to SSE and displays events

### Day 2 Afternoon
- **Dev A**: Full agent loop working, demo mode cached
- **Dev B**: Full UI complete, demo mode playback working
- **Integration test**: Full end-to-end demo scenario

---

## Rules

1. **Never cross directory boundaries** - Dev A stays in `backend/`, Dev B stays in `frontend/`
2. **Don't modify the interface contract** without syncing
3. **Use feature branches**: `dev-a/backend`, `dev-b/frontend`
4. **Merge to main only after sync**
