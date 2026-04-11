# CircuitMap

**CircuitMap** is an autonomous AI agent that validates CNS drug targets by computationally mapping the path from a candidate molecule to its brain circuit impact. It replaces a process that typically takes 6 weeks and $150,000–$200,000 with a 4-minute agentic run.

---

## The Problem

95% of CNS clinical trials fail, primarily due to poor target selection — not bad chemistry. Existing tools stop at the protein (Schrödinger) or at target identification (BenevolentAI). No tool bridges the gap to circuit-level brain mapping and disease anatomy.

---

## How It Works

Given a **drug compound** (name or SMILES) and a **disease indication**, CircuitMap runs an autonomous Claude-powered agent that orchestrates six scientific tools:

| Step | Tool | Data Source |
|------|------|-------------|
| 1 | **resolve_target** | ChEMBL + PubChem — resolves molecule to primary protein target |
| 2 | **get_brain_expression** | Allen Human Brain Atlas (AHBA) — regional gene expression across 6 human donors |
| 3 | **get_disease_map** | Neurosynth v7 — coordinate-density meta-analysis across 14,371 neuroimaging studies |
| 4 | **compute_overlap** | Spatial Pearson correlation with 1,000-permutation null distribution |
| 5 | **get_cognitive_associations** | Neurosynth reverse inference — TF-IDF weighted term aggregation |
| 6 | **search_literature** | ChromaDB semantic search over 447 pre-embedded PubMed abstracts |

The agent synthesizes all findings into a structured **11-section Target Validation Report** with PDF export.

---

## Architecture

```
frontend/               React + TypeScript SPA (Vite)
  ├─ InputPanel         Drug/indication form + demo launcher
  ├─ ReasoningTrace     Live SSE stream of agent thoughts and tool calls
  ├─ BrainVisualization Side-by-side / overlay brain map viewer
  ├─ ConfidencePanel    3-dimension confidence assessment
  └─ ReportDrawer       Full 11-section report with PDF export

backend/                FastAPI + Python 3.11
  ├─ main.py            REST + SSE endpoints
  ├─ agent/             Claude tool-use loop, schemas, prompts
  └─ services/
       ├─ chembl_service.py      Drug → target resolution
       ├─ ahba_service.py        AHBA expression maps (MNI spatial parcellation)
       ├─ neurosynth_service.py  Disease maps + reverse inference (v7 dataset)
       ├─ correlation_service.py Spatial Pearson r + permutation testing
       ├─ rag_service.py         ChromaDB + sentence-transformers semantic search
       └─ pdf_service.py         ReportLab A4 PDF generation
```

**Data flow:**
1. `POST /api/validate` → creates session, starts agent loop as async background task
2. `GET /api/stream/{session_id}` → SSE stream of live agent events
3. Frontend renders reasoning trace, brain map images, overlap score, and final report in real time

---

## Quick Start

### Prerequisites

- Python 3.11 (required — dependency conflicts in 3.12)
- Node.js 18+
- An Anthropic API key

### Backend

```bash
cd backend
python3.11 -m venv venv
source venv/bin/activate          # Windows: venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env
# Edit .env — set ANTHROPIC_API_KEY
uvicorn main:app --reload --workers 1
```

> Run with `--workers 1`. The in-memory session and correlation stores are not process-safe across multiple workers.

### Frontend

```bash
cd frontend
npm install
npm run dev        # → http://localhost:5173
```

Vite proxies `/api` to `localhost:8000` automatically.

---

## Data Preloading

The backend works without any data preloaded — all services have offline fallbacks. For full functionality, run the data scripts once before use:

```bash
cd backend

# Download 6-donor AHBA microarray dataset (~500 MB, ~15 min)
python scripts/preload_ahba.py

# Download Neurosynth v7 dataset — 14,371 studies, 3,228 terms, 507,891 activations (~10 min)
python scripts/preload_neurosynth.py

# Fetch PubMed abstracts and build ChromaDB vector store with sentence-transformers (~30 min)
python scripts/build_rag_store.py
```

For the demo scenarios (optional):
```bash
# Run all 3 demo scenarios and cache results + PDFs
python scripts/precompute_demo.py
```

---

## API Reference

| Method | Path | Description |
|--------|------|-------------|
| `POST` | `/api/validate` | Start an agent validation session |
| `GET` | `/api/stream/{session_id}` | SSE stream of live agent events |
| `GET` | `/api/demo/{scenario}` | Pre-computed demo (`alzheimers` / `schizophrenia` / `depression`) |
| `GET` | `/api/maps/{session_id}/{type}.png` | Serve brain map PNG (`expression` or `disease`) |
| `GET` | `/api/report/{session_id}/download` | Download PDF report |
| `GET` | `/api/health` | Data-cache readiness check |
| `GET` | `/api/config` | Live UI configuration from environment |

### SSE Event Types

| Event | Description |
|-------|-------------|
| `agent_thought` | Claude reasoning text (chunked) |
| `tool_call` | Tool invocation with inputs |
| `tool_result` | Tool completion summary |
| `brain_map` | Brain map ready — includes `image_url` and `top_regions` |
| `overlap_score` | Spatial correlation result — `r`, `percentile`, `label` |
| `confidence_update` | Per-dimension confidence level and rationale |
| `report_ready` | Full 11-section report payload |
| `pdf_ready` | PDF available at `pdf_url` |
| `error` | Agent or tool error |
| `done` | Session complete |

---

## Demo Scenarios

Three pre-built scenarios are available from the UI with no API key or data required:

| Scenario | Drug | Target | Indication |
|----------|------|--------|------------|
| `alzheimers` | Chaetocin | SUV39H1 (H3K9 methyltransferase) | Alzheimer's disease |
| `schizophrenia` | Tolcapone | COMT (catechol-O-methyltransferase) | Schizophrenia |
| `depression` | Vorinostat | HDAC2 (histone deacetylase 2) | Major depressive disorder |

Demo scenarios include full reasoning traces, brain maps, spatial correlation, confidence assessment, and PDF export.

---

## Scientific Methods

### Target Resolution
ChEMBL REST API with PubChem SMILES canonicalization as fallback. Returns primary target, binding affinity (Ki/IC50), mechanism of action, and off-target flags.

### Brain Expression (AHBA)
Allen Human Brain Atlas microarray data from 6 human donors. Expression values are donor-averaged, then spatially parcellated to 20 canonical MNI ROI coordinates using inverse-distance weighted averaging within a 15 mm radius.

### Disease Maps (Neurosynth v7)
Studies are selected by TF-IDF weight > 0.001 for the disease term. For each ROI, activation count across those studies is normalized to [0, 1]. This is equivalent to the classic forward-inference (P(activation | term)) approach.

### Spatial Correlation
Pearson *r* between expression and disease vectors across 20 ROIs, with significance estimated from a 1,000-permutation null distribution (seed=42). Reports both *r* and empirical percentile.

### Reverse Inference (Cognitive Associations)
For each queried brain region, activations within 10 mm in the Neurosynth coordinate table are found. TF-IDF weights across all relevant studies are summed per term and the top terms returned.

### Literature Search
Semantic similarity via `all-MiniLM-L6-v2` (sentence-transformers) against 447 pre-embedded PubMed abstracts in ChromaDB. Falls back to lexical token-overlap scoring when the embedding model is unavailable.

---

## Key Design Decisions

**Why 20 ROI coordinates?** A curated set covering hippocampus, prefrontal cortex, amygdala, striatum, thalamus, cerebellum, entorhinal cortex, anterior cingulate, insula, and parietal/occipital regions provides sufficient spatial coverage for CNS target validation while keeping correlation computation fast and reproducible.

**Why open data sources over proprietary?** Peer-reviewed, open data (AHBA, Neurosynth, ChEMBL) provides reproducibility and regulatory defensibility. Every correlation can be independently replicated.

**Why 1,000-permutation null?** Scientifically appropriate for establishing spatial significance without spin-test precomputation overhead. See Arnatkevičiūtė et al. (2021).

**Why `--workers 1`?** The in-memory session store (`sessions` dict) and correlation map store (`_map_store` dict) are module-level singletons. Multiple Uvicorn workers would create separate processes with isolated stores, causing session lookups to fail. A task queue (Celery/Redis) would fix this for production.

---

## Data Sources

| Dataset | Reference | Size |
|---------|-----------|------|
| Allen Human Brain Atlas | Hawrylycz et al., *Nature* 2012 | ~500 MB |
| Neurosynth v7 | Yarkoni et al., *Nature Methods* 2011 | ~40 MB |
| ChEMBL | Mendez et al., *Nucleic Acids Research* 2019 | Live API |
| PubMed RAG | 447 curated CNS abstracts | ~10 MB |

---

## Documentation

| File | Contents |
|------|----------|
| `docs/prd.md` | Full Product Requirements Document |
| `docs/techstack.md` | Pinned dependency rationale and architecture details |
| `docs/CHANGELOG.md` | Implementation log |
| `docs/split.md` | Developer work-split specification |
