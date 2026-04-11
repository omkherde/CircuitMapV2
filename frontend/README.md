# CircuitMap — Frontend

React + TypeScript SPA built with Vite. Connects to the CircuitMap FastAPI backend via REST and Server-Sent Events.

> For full project overview and backend setup, see the [root README](../README.md).

---

## Development

```bash
npm install
npm run dev        # → http://localhost:5173
```

Vite proxies `/api/*` to `http://localhost:8000` — start the backend first.

```bash
npm run build      # production build → dist/
npm run lint       # ESLint
```

---

## Layout

```
src/
  App.tsx                   Root layout — sidebar, main content, report drawer
  api/client.ts             Axios API client + helper functions
  hooks/
    useAgentSession.ts      Session state, demo playback, SSE wiring
    useAgentStream.ts       SSE connection management
    useAppConfig.ts         Fetches live UI config from /api/config
  components/
    InputPanel.tsx          Drug/indication form + demo scenario buttons
    BrainVisualizationCenter.tsx  Brain map viewer (side-by-side / overlay)
    ReasoningTracePanel.tsx Live agent thought + tool call trace
    SidebarConfidencePanel.tsx    3-dimension confidence display
    ReportDrawer.tsx        Slide-in 11-section report panel
    Header.tsx              App header with status indicator
  mocks/demoEvents.ts       Hardcoded fallback events for offline demo mode
  types/index.ts            All shared TypeScript types
```

---

## SSE Event Handling

The `useAgentStream` hook opens an `EventSource` connection to `/api/stream/{sessionId}`. Events are dispatched to `useAgentSession` which updates React state:

| Event type | State update |
|------------|-------------|
| `brain_map` | `expressionMap` or `diseaseMap` |
| `overlap_score` | `overlapScore` |
| `confidence_update` | `confidence[dimension]` |
| `report_ready` | `reportSections` |
| `pdf_ready` | `pdfUrl` |
| `done` | `phase → 'complete'` |

Consecutive `agent_thought` chunks are merged into a single trace entry before rendering.

---

## Demo Mode

Clicking a demo scenario button calls `loadDemo(scenario)`, which:
1. Fetches pre-computed events from `GET /api/demo/{scenario}`
2. If that fails (backend unavailable), falls back to hardcoded events in `mocks/demoEvents.ts`
3. Replays events at 800 ms intervals to simulate a live session

All demo scenarios include full reasoning traces, brain maps, correlation score, confidence ratings, report sections, and working PDF export.

---

## Environment

```
VITE_API_BASE_URL=    # empty = use Vite proxy (recommended for dev)
```

For production, set `VITE_API_BASE_URL` to the backend origin (e.g. `https://api.circuitmap.io`).
