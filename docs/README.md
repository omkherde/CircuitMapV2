# CircuitMap — CNS Drug Target Validation Agent

CircuitMap is an autonomous AI agent that validates CNS drug targets by
computationally mapping the path from a candidate molecule to its brain circuit
impact. It replaces a consultant-driven process that typically takes 6 weeks and
$150,000–$200,000 with a 4-minute agentic run.

---

## Problem

95% of CNS clinical trials fail, primarily due to poor target selection — not
bad chemistry. Existing tools stop at the protein (Schrödinger) or at target
identification (BenevolentAI). No tool bridges the gap to circuit-level brain
mapping and disease anatomy.

---

## How It Works

Given a **drug compound** (name or SMILES) and a **disease indication**, the
agent orchestrates six scientific tools in a Claude-powered loop:

1. **resolve_target** — Resolves the molecule to its primary protein target via ChEMBL + PubChem
2. **get_brain_expression** — Queries Allen Human Brain Atlas (AHBA) for regional gene expression
3. **get_disease_map** — Retrieves a Neurosynth meta-analytic disease activation map
4. **compute_overlap** — Computes spatial Pearson correlation between expression and disease maps
5. **get_cognitive_associations** — Performs reverse inference on cognitive associations
6. **search_literature** — Searches a pre-embedded PubMed RAG store for literature evidence

The agent synthesizes findings into a structured **11-section Target Validation
Report** with PDF export.

---

## Architecture

```
frontend/          React + TypeScript SPA (Vite)
  └─ Three-panel layout: input, live reasoning trace, brain maps + report

backend/           FastAPI + Python 3.11
  ├─ main.py       REST + SSE endpoints
  ├─ agent/        Claude tool-use loop, tool schemas, prompts
  └─ services/     ahba, neurosynth, chembl, correlation, rag, pdf
```

**Data flow:**
1. POST `/api/validate` → creates session, starts agent loop as background task
2. GET `/api/stream/{session_id}` → SSE stream of live agent events
3. Frontend renders reasoning trace, brain map images, overlap score, and final report in real time

**Offline fallbacks** are present for all external data sources (AHBA cached
donor files, Neurosynth curated templates, ChEMBL local target profiles, lexical
RAG fallback). The graceful degradation hierarchy is: live agent → demo mode →
static screenshots.

---

## Setup

### Prerequisites

- Python 3.11 (required — abagen/numpy conflict in 3.12)
- Node.js 18+
- An Anthropic API key

### Backend

```bash
cd backend
python -m venv venv
source venv/bin/activate          # Windows: venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env
# Edit .env — set ANTHROPIC_API_KEY at minimum
uvicorn main:app --reload --workers 1
```

> **Important:** Run with `--workers 1`. The in-memory session store and
> correlation map store are not process-safe under multiple workers.

#### (Optional) Pre-load data caches

```bash
# Download ~500 MB AHBA microarray data + build Neurosynth + ChromaDB RAG index
python scripts/preload_data.py

# Pre-compute demo scenarios (Alzheimer's, Schizophrenia, Depression)
python scripts/precompute_demo.py
```

### Frontend

```bash
cd frontend
npm install
npm run dev        # http://localhost:5173
```

---

## API Endpoints

| Method | Path | Description |
|--------|------|-------------|
| POST | `/api/validate` | Start an agent session |
| GET | `/api/stream/{session_id}` | SSE stream of live agent events |
| GET | `/api/demo/{scenario}` | Pre-computed demo (alzheimers / schizophrenia / depression) |
| GET | `/api/maps/{session_id}/{type}.png` | Serve brain map PNG |
| GET | `/api/report/{session_id}/download` | Download PDF report |
| GET | `/api/health` | Data-cache readiness check |
| GET | `/api/config` | Live UI configuration from environment |

---

## Demo Scenarios

| Scenario | Drug | Indication |
|----------|------|------------|
| `alzheimers` | Chaetocin (SUV39H1 inhibitor) | Alzheimer's disease |
| `schizophrenia` | Tolcapone (COMT inhibitor) | Schizophrenia |
| `depression` | Vorinostat (HDAC1 inhibitor) | Major depressive disorder |

---

## Key Design Decisions

- **Why 20 ROI coordinates?** A curated set of 20 canonical MNI coordinates
  covering hippocampus, prefrontal cortex, amygdala, striatum, thalamus,
  cerebellum, entorhinal cortex, anterior cingulate, insula, and parietal/
  occipital regions provides sufficient spatial coverage for CNS target
  validation while keeping correlation computation fast.

- **Why curated cognitive lookup table instead of the Neurosynth decoder?**
  The Neurosynth decoder requires a full 3D NIfTI image and a complete term
  co-activation database. The curated table offers deterministic, offline
  associations that are consistent across runs and do not depend on live
  Neurosynth data.

- **Why open data sources (AHBA, Neurosynth) over proprietary datasets?**
  Peer-reviewed, open data provides reproducibility and regulatory defensibility
  that proprietary black-box datasets (BenevolentAI, Insilico) cannot. Every
  correlation can be independently replicated.

- **1000-permutation null distribution (seed=42):** Scientifically appropriate
  for establishing spatial significance without requiring spin-test precomputation.
  See Arnatkevičiūtė et al. (2021) for the reference methodology.

---

## Documentation

| File | Contents |
|------|----------|
| `docs/prd.md` | Full Product Requirements Document |
| `docs/techstack.md` | Pinned dependency rationale |
| `docs/split.md` | Developer work-split specification |
| `docs/masterprompt.md` | AI-assisted implementation prompt |
| `docs/CHANGELOG.md` | Integration bug log and resolutions |
