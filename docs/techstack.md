# CircuitMap — Tech Stack & Architecture Reference

**Version:** 1.0  
**Date:** April 11, 2026  
**For:** Claude Code / Developer handoff  
**Read prd.md first.** This document assumes full familiarity with the PRD.

---

## 1. Architecture Overview

CircuitMap is a two-process application:

- **Backend:** Python FastAPI server running the agentic loop, all scientific data tools, and PDF generation
- **Frontend:** React + TypeScript SPA connecting via REST + SSE (Server-Sent Events)

There is no database. Sessions are held in memory. Brain map images are written to a temp directory per session. ChromaDB runs as an embedded local vector store (no server process required).

```
Browser (React SPA)
    │
    ├── POST /api/validate ──────────────────► FastAPI backend
    │                                              │
    └── GET /api/stream/{id} (SSE) ◄──────────────┤
                                                   │
                                              Agentic Loop
                                              (Claude tool_use)
                                                   │
                              ┌────────────────────┼────────────────────┐
                              ▼                    ▼                    ▼
                         ChEMBL API          abagen + AHBA         ChromaDB
                         PubChem API         nilearn               (PubMed RAG)
                                             Neurosynth
                                             scipy
```

---

## 2. Python Backend Stack

### 2.1 Python Version
```
Python 3.11.9
```
Do NOT use 3.12+ — abagen has dependency conflicts with numpy in 3.12.

### 2.2 Core Dependencies (exact versions)

```txt
# requirements.txt

# AI / Agent
anthropic==0.49.0

# Web server
fastapi==0.115.6
uvicorn[standard]==0.34.0
python-multipart==0.0.20
sse-starlette==2.2.1

# Data validation
pydantic==2.10.4
python-dotenv==1.0.1

# Scientific computing
numpy==1.26.4
pandas==2.2.3
scipy==1.14.1

# Neuroimaging
nibabel==5.3.2
nilearn==0.10.4
abagen==0.1.1
matplotlib==3.9.4

# ChEMBL / chemistry
chembl_webresource_client==0.10.9
requests==2.32.3

# Neurosynth
neurosynth==0.3.7

# RAG / Vector store
chromadb==0.6.3
sentence-transformers==3.3.1

# PDF generation
reportlab==4.2.5
Pillow==11.0.0

# Bioinformatics (PubMed access)
biopython==1.84

# Utilities
httpx==0.28.1
aiofiles==24.1.0
uuid==1.30
```

### 2.3 Installation
```bash
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt
```

---

## 3. Frontend Stack

### 3.1 Node Version
```
Node.js 20.18.0 LTS
npm 10.8.2
```

### 3.2 Core Dependencies
```json
{
  "dependencies": {
    "react": "^18.3.1",
    "react-dom": "^18.3.1",
    "axios": "^1.7.9",
    "@tanstack/react-query": "^5.62.7",
    "clsx": "^2.1.1",
    "tailwind-merge": "^2.5.5"
  },
  "devDependencies": {
    "@types/react": "^18.3.17",
    "@types/react-dom": "^18.3.5",
    "@vitejs/plugin-react": "^4.3.4",
    "typescript": "^5.7.2",
    "vite": "^6.0.5",
    "tailwindcss": "^3.4.17",
    "autoprefixer": "^10.4.20",
    "postcss": "^8.4.49"
  }
}
```

### 3.3 Scaffold Command
```bash
cd frontend
npm create vite@latest . -- --template react-ts
npm install
npm install axios @tanstack/react-query clsx tailwind-merge
npm install -D tailwindcss autoprefixer postcss
npx tailwindcss init -p
```

---

## 4. Project Directory Structure

```
circuitmap/
├── backend/
│   ├── main.py                        # FastAPI app, route definitions, CORS
│   ├── agent/
│   │   ├── __init__.py
│   │   ├── loop.py                    # Agentic loop — the core engine
│   │   ├── tools.py                   # Tool implementation functions
│   │   ├── tools_schema.py            # Claude tool JSON schemas (6 tools)
│   │   └── prompts.py                 # System prompt (exact text from PRD §6.2)
│   ├── services/
│   │   ├── __init__.py
│   │   ├── chembl_service.py          # ChEMBL + PubChem lookups
│   │   ├── ahba_service.py            # abagen AHBA queries + nilearn visualization
│   │   ├── neurosynth_service.py      # Neurosynth queries + parcellation
│   │   ├── correlation_service.py     # Spatial correlation + null permutation
│   │   ├── rag_service.py             # ChromaDB vector store + PubMed retrieval
│   │   └── pdf_service.py             # ReportLab PDF generation
│   ├── models/
│   │   ├── __init__.py
│   │   ├── requests.py                # Pydantic input models
│   │   └── responses.py               # Pydantic SSE event models
│   ├── cache/
│   │   ├── ahba_data/                 # Pre-downloaded AHBA dataset (~500MB)
│   │   │   └── (populated by preload_ahba.py)
│   │   ├── chroma_db/                 # Persistent ChromaDB vector store
│   │   │   └── (populated by build_rag_store.py)
│   │   ├── neurosynth_data/           # Pre-downloaded Neurosynth database
│   │   │   └── (populated by preload_neurosynth.py)
│   │   └── demo/                      # Pre-computed demo scenarios
│   │       ├── alzheimers.json        # Full trace + report for Scenario 1
│   │       ├── schizophrenia.json     # Full trace + report for Scenario 2
│   │       ├── depression.json        # Full trace + report for Scenario 3
│   │       ├── alzheimers_expression.png
│   │       ├── alzheimers_disease.png
│   │       ├── schizophrenia_expression.png
│   │       ├── schizophrenia_disease.png
│   │       ├── depression_expression.png
│   │       └── depression_disease.png
│   ├── sessions/                      # Runtime: per-session temp storage
│   │   └── {session_id}/
│   │       ├── expression.png
│   │       └── disease.png
│   ├── scripts/
│   │   ├── preload_ahba.py            # RUN THIS BEFORE HACKATHON — downloads ~500MB
│   │   ├── preload_neurosynth.py      # RUN THIS BEFORE HACKATHON — downloads database
│   │   ├── build_rag_store.py         # RUN THIS BEFORE HACKATHON — builds ChromaDB
│   │   └── precompute_demo.py         # RUN THIS BEFORE HACKATHON — runs 3 scenarios
│   ├── requirements.txt
│   └── .env.example
├── frontend/
│   ├── src/
│   │   ├── main.tsx                   # React entry point
│   │   ├── App.tsx                    # Root component, layout
│   │   ├── components/
│   │   │   ├── Header.tsx             # CircuitMap wordmark + demo badge
│   │   │   ├── InputPanel.tsx         # Left panel: drug input form
│   │   │   ├── ReasoningTrace.tsx     # Center panel: streaming trace
│   │   │   ├── TraceEntry.tsx         # Single trace line with type styling
│   │   │   ├── BrainMaps.tsx          # Right panel: map images + overlap score
│   │   │   ├── OverlapScore.tsx       # r value + percentile bar + badge
│   │   │   ├── ConfidencePanel.tsx    # Three-row confidence display
│   │   │   ├── ReportPanel.tsx        # Parsed report sections renderer
│   │   │   └── ExportButton.tsx       # PDF export button + download trigger
│   │   ├── hooks/
│   │   │   ├── useAgentSession.ts     # POST /api/validate, get session_id
│   │   │   └── useAgentStream.ts      # SSE connection, parse events, update state
│   │   ├── types/
│   │   │   └── index.ts               # All TypeScript interfaces
│   │   ├── api/
│   │   │   └── client.ts              # Axios instance, base URL config
│   │   └── utils/
│   │       └── parseReport.ts         # Parse agent report text into sections
│   ├── public/
│   │   └── logo.svg                   # CircuitMap logo
│   ├── index.html
│   ├── package.json
│   ├── tailwind.config.ts
│   ├── vite.config.ts
│   └── tsconfig.json
├── prd.md
├── techstack.md
└── README.md
```

---

## 5. Environment Variables

### backend/.env.example
```bash
# REQUIRED — get from console.anthropic.com
ANTHROPIC_API_KEY=sk-ant-...

# OPTIONAL — adjust paths if needed
AHBA_DATA_DIR=./cache/ahba_data
CHROMA_DB_DIR=./cache/chroma_db
NEUROSYNTH_DATA_DIR=./cache/neurosynth_data
DEMO_CACHE_DIR=./cache/demo
SESSIONS_DIR=./sessions

# OPTIONAL — server config
HOST=0.0.0.0
PORT=8000
CORS_ORIGINS=http://localhost:5173,http://localhost:3000

# OPTIONAL — agent behavior
MAX_TOOL_CALLS=20
SESSION_TIMEOUT_SECONDS=300
CLAUDE_MODEL=claude-opus-4-6

# OPTIONAL — RAG config
RAG_TOP_K=5
EMBEDDING_MODEL=all-MiniLM-L6-v2
```

### frontend/.env
```bash
VITE_API_BASE_URL=http://localhost:8000
```

---

## 6. FastAPI Application (main.py)

```python
# backend/main.py — Complete structure

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, StreamingResponse
from sse_starlette.sse import EventSourceResponse
import uvicorn, os

from models.requests import ValidateRequest, DemoScenario
from agent.loop import run_agent_session
from services.pdf_service import generate_pdf

app = FastAPI(title="CircuitMap API", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=os.getenv("CORS_ORIGINS", "http://localhost:5173").split(","),
    allow_methods=["*"],
    allow_headers=["*"],
)

# In-memory session store — ephemeral, no persistence
sessions: dict = {}

@app.get("/api/health")
async def health():
    return {"status": "ok"}

@app.post("/api/validate")
async def validate(req: ValidateRequest):
    # Create session, start background agent task
    # Return session_id immediately
    pass

@app.get("/api/stream/{session_id}")
async def stream(session_id: str):
    # Return EventSourceResponse connected to session's async queue
    pass

@app.get("/api/report/{session_id}/download")
async def download_report(session_id: str):
    # Return PDF FileResponse
    pass

@app.get("/api/demo/{scenario}")
async def demo(scenario: DemoScenario):
    # Return pre-computed demo data
    pass

@app.get("/api/maps/{session_id}/{map_type}.png")
async def serve_map(session_id: str, map_type: str):
    # Serve brain map PNG from sessions directory
    pass

if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
```

---

## 7. Agentic Loop Implementation (agent/loop.py)

```python
# backend/agent/loop.py — Exact implementation pattern

import anthropic
import asyncio
from agent.tools_schema import TOOLS
from agent.prompts import SYSTEM_PROMPT
from agent.tools import execute_tool

client = anthropic.Anthropic()

async def run_agent_session(session_id: str, drug_query: str, query_type: str, 
                             indication: str, event_queue: asyncio.Queue):
    """
    Main agentic loop. Runs until agent produces final report or hits tool call limit.
    Emits SSE events to event_queue throughout.
    """
    
    messages = [
        {
            "role": "user",
            "content": f"Validate this CNS drug target for the following indication.\n\nDrug input: {drug_query}\nInput type: {query_type}\nDisease indication: {indication}\n\nBegin your investigation."
        }
    ]
    
    tool_call_count = 0
    MAX_TOOL_CALLS = int(os.getenv("MAX_TOOL_CALLS", 20))
    
    while tool_call_count < MAX_TOOL_CALLS:
        # Stream the response
        full_text = ""
        tool_uses = []
        stop_reason = None
        
        with client.messages.stream(
            model=os.getenv("CLAUDE_MODEL", "claude-opus-4-6"),
            max_tokens=4096,
            system=SYSTEM_PROMPT,
            tools=TOOLS,
            messages=messages
        ) as stream:
            for event in stream:
                if hasattr(event, 'type'):
                    if event.type == 'content_block_delta':
                        if hasattr(event.delta, 'text'):
                            full_text += event.delta.text
                            # Emit agent thought chunks
                            await event_queue.put({
                                "type": "agent_thought",
                                "content": event.delta.text
                            })
            
            # Get final message after streaming
            final_message = stream.get_final_message()
            stop_reason = final_message.stop_reason
            
            # Extract tool uses from content blocks
            for block in final_message.content:
                if block.type == "tool_use":
                    tool_uses.append(block)
        
        # Append assistant message to history
        messages.append({
            "role": "assistant",
            "content": final_message.content
        })
        
        if stop_reason == "end_turn":
            # Agent is done — parse report and emit
            await _handle_report_complete(full_text, session_id, event_queue)
            break
        
        if stop_reason == "tool_use" and tool_uses:
            # Execute all tool calls
            tool_results = []
            for tool_use in tool_uses:
                tool_call_count += 1
                
                # Emit tool call event
                await event_queue.put({
                    "type": "tool_call",
                    "tool": tool_use.name,
                    "input": tool_use.input
                })
                
                # Execute the tool
                result = await execute_tool(
                    tool_name=tool_use.name,
                    tool_input=tool_use.input,
                    session_id=session_id,
                    event_queue=event_queue
                )
                
                tool_results.append({
                    "type": "tool_result",
                    "tool_use_id": tool_use.id,
                    "content": str(result)
                })
            
            # Append tool results to conversation
            messages.append({
                "role": "user",
                "content": tool_results
            })
    
    # Signal stream end
    await event_queue.put({"type": "done"})
```

---

## 8. Tool Implementations (services/)

### 8.1 chembl_service.py

```python
# Uses chembl_webresource_client

from chembl_webresource_client.new_client import new_client

def resolve_by_name(drug_name: str) -> dict:
    """
    Query ChEMBL by drug name. Returns target data.
    Falls back to PubChem if ChEMBL returns nothing.
    """
    molecule = new_client.molecule
    activity = new_client.activity
    target = new_client.target
    
    # Search for molecule by name
    mols = molecule.filter(pref_name__iexact=drug_name).only(['molecule_chembl_id', 'pref_name'])
    
    if not mols:
        # Try synonym search
        mols = molecule.filter(molecule_synonyms__synonym__iexact=drug_name)
    
    if not mols:
        return {"error": f"No ChEMBL entry found for '{drug_name}'"}
    
    mol_id = mols[0]['molecule_chembl_id']
    
    # Get activities for this molecule — CNS targets only
    activities = activity.filter(
        molecule_chembl_id=mol_id,
        standard_type__in=['Ki', 'IC50', 'Kd'],
        target_organism='Homo sapiens'
    ).only(['target_chembl_id', 'standard_type', 'standard_value', 'standard_units'])
    
    # For each activity, get target info
    # Filter to protein targets with known gene names
    # Return top 3 by binding affinity (lowest nM = strongest)
    pass

def resolve_by_smiles(smiles: str) -> dict:
    """
    Query ChEMBL by SMILES using similarity search (85% threshold).
    """
    molecule = new_client.molecule
    results = molecule.filter(
        smiles__flexmatch=smiles
    ).only(['molecule_chembl_id', 'pref_name'])
    # Then proceed as resolve_by_name with the found chembl_id
    pass
```

### 8.2 ahba_service.py

```python
# Uses abagen and nilearn

import abagen
import nilearn
from nilearn import plotting, image
import matplotlib.pyplot as plt
import numpy as np

AHBA_DATA_DIR = os.getenv("AHBA_DATA_DIR", "./cache/ahba_data")

def get_expression_map(gene_name: str, session_id: str) -> dict:
    """
    Query Allen Human Brain Atlas for gene expression across brain regions.
    Returns top 10 regions and path to Nilearn visualization PNG.
    
    Atlas: Desikan-Killiany 68-region parcellation (DK atlas)
    abagen uses this as default when no atlas is specified.
    """
    
    # Load pre-downloaded AHBA data
    # abagen.fetch_microarray returns a DataFrame: samples × genes
    expression = abagen.get_expression_data(
        atlas=None,  # Uses DK parcellation by default
        data_dir=AHBA_DATA_DIR,
        return_donors=False  # Aggregate across donors
    )
    
    # expression is a regions × genes DataFrame
    # Extract the target gene column
    if gene_name not in expression.columns:
        return {"error": f"Gene {gene_name} not found in AHBA dataset"}
    
    gene_expr = expression[gene_name]
    
    # Convert to percentile ranks
    from scipy import stats
    percentiles = stats.rankdata(gene_expr) / len(gene_expr) * 100
    
    # Get top 10 regions
    top_indices = np.argsort(percentiles)[::-1][:10]
    top_regions = [
        {
            "region": expression.index[i],
            "percentile": round(float(percentiles[i]), 1),
            "raw_expression": round(float(gene_expr.iloc[i]), 4)
        }
        for i in top_indices
    ]
    
    # Generate Nilearn visualization
    image_path = _generate_expression_image(gene_expr, session_id)
    
    # Store parcellated values for correlation
    parcellated_values = dict(zip(expression.index, gene_expr.values))
    
    map_id = f"{session_id}_expression_{gene_name}"
    
    return {
        "gene_name": gene_name,
        "map_id": map_id,
        "top_regions": top_regions,
        "atlas": "Desikan-Killiany 68-region",
        "n_samples": len(expression),
        "image_path": image_path,
        "parcellated_values": parcellated_values
    }

def _generate_expression_image(gene_expr: pd.Series, session_id: str) -> str:
    """
    Generate a Nilearn axial slice PNG of brain expression.
    Uses the DK atlas NIfTI file to project parcellated values.
    """
    # Load DK atlas NIfTI (bundled with nilearn)
    from nilearn.datasets import fetch_atlas_destrieux_2009
    # Note: Use Desikan-Killiany equivalent or the closest nilearn atlas
    
    # Project expression values onto atlas parcels
    # Generate plot with nilearn.plotting.plot_stat_map
    # Save as PNG 640x400 at 150 DPI
    
    output_path = f"./sessions/{session_id}/expression.png"
    os.makedirs(f"./sessions/{session_id}", exist_ok=True)
    
    fig, ax = plt.subplots(figsize=(8, 5))
    # ... plotting code ...
    plt.savefig(output_path, dpi=150, bbox_inches='tight', facecolor='white')
    plt.close()
    
    return output_path
```

### 8.3 neurosynth_service.py

```python
# Uses neurosynth Python library

import neurosynth
from neurosynth.base.dataset import Dataset
from neurosynth.analysis import decode

NEUROSYNTH_DATA_DIR = os.getenv("NEUROSYNTH_DATA_DIR", "./cache/neurosynth_data")

# Load dataset once at startup — expensive operation
_dataset = None

def get_dataset() -> Dataset:
    global _dataset
    if _dataset is None:
        _dataset = Dataset(
            os.path.join(NEUROSYNTH_DATA_DIR, "database.txt"),
            os.path.join(NEUROSYNTH_DATA_DIR, "features.txt")
        )
        _dataset.add_images(os.path.join(NEUROSYNTH_DATA_DIR, "images"))
    return _dataset

def get_disease_map(indication: str, session_id: str) -> dict:
    """
    Get Neurosynth meta-analytic map for a clinical indication.
    Returns top regions and map NIfTI projected to DK parcellation.
    """
    dataset = get_dataset()
    
    # Map indication strings to Neurosynth feature terms
    INDICATION_MAP = {
        "alzheimer's disease": "alzheimer",
        "parkinson's disease": "parkinson",
        "schizophrenia": "schizophrenia",
        "major depressive disorder": "depression",
        "bipolar disorder": "bipolar",
        "ptsd": "posttraumatic",
        "epilepsy": "epilepsy",
        "als": "amyotrophic",
        "huntington's disease": "huntington",
        "treatment-resistant depression": "depression",
        "anxiety disorders": "anxiety",
        "frontotemporal dementia": "frontotemporal",
    }
    
    term = INDICATION_MAP.get(indication.lower(), indication.lower().split()[0])
    
    # Run meta-analysis for the term
    from neurosynth.analysis.meta import MetaAnalysis
    ma = MetaAnalysis(dataset, ids=dataset.get_studies(features=term))
    results = ma.run()
    
    # Get the 'pAgF' (posterior probability) map
    stat_map = results.get_image('pAgF')
    
    # Parcellate to DK atlas for correlation
    parcellated = _parcellate_to_dk(stat_map)
    
    # Generate PNG visualization
    image_path = _generate_disease_image(stat_map, session_id, term)
    
    map_id = f"{session_id}_disease_{term}"
    
    # Get top regions
    top_regions = sorted(parcellated.items(), key=lambda x: x[1], reverse=True)[:10]
    
    return {
        "indication": indication,
        "neurosynth_term": term,
        "map_id": map_id,
        "top_regions": [{"region": r, "activation": round(v, 4)} for r, v in top_regions],
        "n_studies": len(dataset.get_studies(features=term)),
        "image_path": image_path,
        "parcellated_values": dict(parcellated)
    }

def get_cognitive_associations(regions: list, top_n: int = 8) -> dict:
    """
    Neurosynth reverse inference: given brain regions, what cognitive functions?
    Uses the decoder to find highest-correlated Neurosynth terms.
    """
    dataset = get_dataset()
    decoder = decode.Decoder(dataset)
    
    # Create a binary mask for the specified regions using DK atlas
    mask = _regions_to_mask(regions)
    
    # Decode — returns correlation of each feature with the mask
    results = decoder.decode(mask, save=None)
    
    # Return top_n terms with their correlation values
    top_terms = results.nlargest(top_n)
    
    return {
        "queried_regions": regions,
        "cognitive_associations": [
            {"term": term, "correlation": round(corr, 3)}
            for term, corr in top_terms.items()
        ]
    }
```

### 8.4 correlation_service.py

```python
# Spatial Pearson correlation with spin-test null distribution

import numpy as np
from scipy import stats

# In-memory store of maps for the session
_map_store: dict = {}

def store_map(map_id: str, parcellated_values: dict):
    """Store parcellated map values keyed by map_id for later correlation."""
    _map_store[map_id] = parcellated_values

def compute_overlap(map1_id: str, map2_id: str, label: str) -> dict:
    """
    Compute Pearson r between two parcellated brain maps.
    Run 1000 permutations to generate null distribution.
    
    Scientific note: We use simple permutation (not spin test) for hackathon
    speed. Spin test (Vasa et al. 2018) is the gold standard but requires
    surface coordinates. Flag this as a limitation in the report.
    """
    
    if map1_id not in _map_store or map2_id not in _map_store:
        return {"error": "One or both map IDs not found. Ensure tool calls succeeded."}
    
    map1 = _map_store[map1_id]
    map2 = _map_store[map2_id]
    
    # Align on common regions
    common_regions = sorted(set(map1.keys()) & set(map2.keys()))
    
    if len(common_regions) < 20:
        return {"error": f"Only {len(common_regions)} common regions — insufficient for correlation"}
    
    vec1 = np.array([map1[r] for r in common_regions])
    vec2 = np.array([map2[r] for r in common_regions])
    
    # Observed correlation
    r_obs, p_obs = stats.pearsonr(vec1, vec2)
    
    # Null distribution: permute map2 values 1000 times
    null_rs = []
    rng = np.random.default_rng(seed=42)  # Fixed seed for reproducibility
    for _ in range(1000):
        vec2_perm = rng.permutation(vec2)
        r_null, _ = stats.pearsonr(vec1, vec2_perm)
        null_rs.append(r_null)
    
    null_rs = np.array(null_rs)
    percentile = int(np.sum(null_rs < r_obs) / len(null_rs) * 100)
    
    # Interpretation thresholds
    if percentile >= 75:
        interpretation = "strong"
    elif percentile >= 50:
        interpretation = "moderate"
    else:
        interpretation = "weak"
    
    return {
        "r": round(float(r_obs), 3),
        "p_value": round(float(p_obs), 4),
        "percentile": percentile,
        "null_mean": round(float(null_rs.mean()), 3),
        "null_std": round(float(null_rs.std()), 3),
        "n_regions": len(common_regions),
        "interpretation": interpretation,
        "label": label,
        "note": "Null distribution from 1000 regional permutations (seed=42). Not a spatial autocorrelation-corrected spin test."
    }
```

### 8.5 rag_service.py

```python
# ChromaDB RAG store for PubMed abstracts

import chromadb
from chromadb.utils import embedding_functions
from Bio import Entrez

CHROMA_DB_DIR = os.getenv("CHROMA_DB_DIR", "./cache/chroma_db")
EMBEDDING_MODEL = os.getenv("EMBEDDING_MODEL", "all-MiniLM-L6-v2")

# Target genes to pre-download PubMed abstracts for
PRELOAD_GENES = [
    "SUV39H1", "COMT", "HDAC2", "HDAC1", "G9a", "EHMT2",
    "BDNF", "DNMT3A", "KDM5C", "MAOA", "SLC6A4", "DRD2"
]

# Initialize ChromaDB client once
_chroma_client = None
_collection = None

def get_collection():
    global _chroma_client, _collection
    if _collection is None:
        _chroma_client = chromadb.PersistentClient(path=CHROMA_DB_DIR)
        ef = embedding_functions.SentenceTransformerEmbeddingFunction(
            model_name=EMBEDDING_MODEL
        )
        _collection = _chroma_client.get_or_create_collection(
            name="pubmed_abstracts",
            embedding_function=ef,
            metadata={"hnsw:space": "cosine"}
        )
    return _collection

def search_literature(query: str, top_k: int = 5) -> dict:
    """
    Search pre-embedded PubMed abstracts using semantic similarity.
    """
    collection = get_collection()
    
    results = collection.query(
        query_texts=[query],
        n_results=min(top_k, 10),
        include=["documents", "metadatas", "distances"]
    )
    
    abstracts = []
    for i, doc in enumerate(results["documents"][0]):
        meta = results["metadatas"][0][i]
        abstracts.append({
            "title": meta.get("title", "Unknown"),
            "authors": meta.get("authors", "Unknown"),
            "journal": meta.get("journal", "Unknown"),
            "year": meta.get("year", "Unknown"),
            "pmid": meta.get("pmid", "Unknown"),
            "abstract": doc[:500] + "..." if len(doc) > 500 else doc,
            "similarity": round(1 - results["distances"][0][i], 3)
        })
    
    return {
        "query": query,
        "results": abstracts,
        "total_results": len(abstracts),
        "source": "PubMed RAG store (pre-embedded)"
    }
```

---

## 9. Pre-Event Setup Scripts (Run Before Hackathon)

### scripts/preload_ahba.py
```python
"""
RUN THIS BEFORE THE HACKATHON.
Downloads Allen Human Brain Atlas microarray data (~500MB).
Run on home WiFi — NOT hackathon WiFi.
Time: ~10-15 minutes.
"""
import abagen
import os

DATA_DIR = "./cache/ahba_data"
os.makedirs(DATA_DIR, exist_ok=True)

print("Downloading AHBA microarray data... (~500MB, ~10-15 min)")

# This downloads all 6 donor datasets
files = abagen.fetch_microarray(
    data_dir=DATA_DIR,
    donors='all',
    verbose=True
)

print(f"Downloaded {len(files)} files to {DATA_DIR}")
print("Pre-loading expression data for demo genes...")

# Pre-compute expression for demo genes to verify working
from services.ahba_service import get_expression_map
for gene in ['SUV39H1', 'COMT', 'HDAC2']:
    result = get_expression_map(gene, session_id='preload_test')
    print(f"  {gene}: top region = {result['top_regions'][0]['region']} "
          f"({result['top_regions'][0]['percentile']}th percentile)")

print("AHBA preload complete.")
```

### scripts/preload_neurosynth.py
```python
"""
RUN THIS BEFORE THE HACKATHON.
Downloads Neurosynth database files.
Time: ~5-10 minutes.
"""
import neurosynth
from neurosynth.base.dataset import Dataset

DATA_DIR = "./cache/neurosynth_data"
os.makedirs(DATA_DIR, exist_ok=True)

print("Downloading Neurosynth database...")
neurosynth.utils.download(data_dir=DATA_DIR, unpack=True)

print("Building Neurosynth dataset...")
dataset = Dataset(
    os.path.join(DATA_DIR, "database.txt"),
    os.path.join(DATA_DIR, "features.txt")
)
dataset.save(os.path.join(DATA_DIR, "dataset.pkl"))

print("Verifying disease maps...")
for term in ['alzheimer', 'schizophrenia', 'depression']:
    studies = dataset.get_studies(features=term)
    print(f"  {term}: {len(studies)} studies found")

print("Neurosynth preload complete.")
```

### scripts/build_rag_store.py
```python
"""
RUN THIS BEFORE THE HACKATHON.
Fetches PubMed abstracts for target genes and builds ChromaDB.
Requires internet connection.
Time: ~20-30 minutes.
"""
from Bio import Entrez
import chromadb
from chromadb.utils import embedding_functions

Entrez.email = "team@circuitmap.ai"

GENES = ['SUV39H1', 'COMT', 'HDAC2', 'HDAC1', 'G9a', 'EHMT2',
         'BDNF', 'DNMT3A', 'KDM5C', 'MAOA', 'SLC6A4', 'DRD2']

DISEASE_TERMS = ['alzheimer', 'schizophrenia', 'depression', 
                 'parkinson', 'bipolar', 'epilepsy']

def fetch_pubmed_abstracts(query: str, max_results: int = 50) -> list:
    handle = Entrez.esearch(db="pubmed", term=query, retmax=max_results)
    record = Entrez.read(handle)
    ids = record["IdList"]
    
    if not ids:
        return []
    
    handle = Entrez.efetch(db="pubmed", id=ids, rettype="abstract", retmode="xml")
    records = Entrez.read(handle)
    
    abstracts = []
    for article in records["PubmedArticle"]:
        try:
            medline = article["MedlineCitation"]
            article_data = medline["Article"]
            abstract_text = str(article_data.get("Abstract", {}).get("AbstractText", ""))
            title = str(article_data.get("ArticleTitle", ""))
            pmid = str(medline["PMID"])
            
            if abstract_text and len(abstract_text) > 100:
                abstracts.append({
                    "text": f"{title}\n\n{abstract_text}",
                    "title": title,
                    "pmid": pmid,
                })
        except:
            continue
    
    return abstracts

# Build ChromaDB collection
client = chromadb.PersistentClient(path="./cache/chroma_db")
ef = embedding_functions.SentenceTransformerEmbeddingFunction(
    model_name="all-MiniLM-L6-v2"
)
collection = client.get_or_create_collection(
    name="pubmed_abstracts",
    embedding_function=ef
)

for gene in GENES:
    for disease in DISEASE_TERMS:
        query = f"{gene} {disease} brain"
        abstracts = fetch_pubmed_abstracts(query, max_results=20)
        
        for i, ab in enumerate(abstracts):
            doc_id = f"{gene}_{disease}_{ab['pmid']}"
            try:
                collection.add(
                    documents=[ab["text"]],
                    ids=[doc_id],
                    metadatas=[{"gene": gene, "disease": disease, "pmid": ab["pmid"], "title": ab["title"]}]
                )
            except:
                pass  # Skip duplicates
        
        print(f"  {gene} + {disease}: {len(abstracts)} abstracts indexed")

print(f"RAG store complete. Total documents: {collection.count()}")
```

### scripts/precompute_demo.py
```python
"""
RUN THIS THE NIGHT BEFORE THE HACKATHON.
Runs all 3 demo scenarios with the live agent and saves outputs.
Requires ANTHROPIC_API_KEY to be set.
Time: ~10-15 minutes.
"""
# Runs Scenarios 1, 2, 3 from the PRD
# Saves full trace events, report JSON, and brain map PNGs to ./cache/demo/
```

---

## 10. React Frontend Implementation

### 10.1 TypeScript Types (src/types/index.ts)
```typescript
export type QueryType = 'name' | 'smiles';
export type DemoScenario = 'alzheimers' | 'schizophrenia' | 'depression';
export type ConfidenceLevel = 'HIGH' | 'MODERATE' | 'LOW' | 'PENDING';

export type TraceEventType = 
  | 'agent_thought' 
  | 'tool_call' 
  | 'tool_result' 
  | 'confidence_update'
  | 'brain_map'
  | 'overlap_score'
  | 'report_ready'
  | 'pdf_ready'
  | 'error';

export interface TraceEvent {
  type: TraceEventType;
  content?: string;
  tool?: string;
  input?: Record<string, unknown>;
  summary?: string;
  map_type?: 'expression' | 'disease';
  image_url?: string;
  r?: number;
  percentile?: number;
  dimension?: string;
  level?: ConfidenceLevel;
  rationale?: string;
  report_sections?: ReportSections;
  pdf_url?: string;
  filename?: string;
  message?: string;
  timestamp: number;
}

export interface ReportSections {
  executive_summary: string;
  molecular_target_profile: string;
  brain_expression_analysis: string;
  functional_circuit_context: string;
  target_pathology_overlap: string;
  off_target_risk_assessment: string;
  literature_evidence_summary: string;
  recommended_clinical_endpoints: string;
  confidence_assessment: string;
  preclinical_validation_recommendations: string;
  data_sources_and_limitations: string;
}

export interface ConfidenceDimension {
  dimension: 'target_resolution' | 'circuit_alignment' | 'literature_support';
  label: string;
  level: ConfidenceLevel;
  rationale: string;
}

export interface SessionState {
  sessionId: string | null;
  status: 'idle' | 'running' | 'complete' | 'error';
  mode: 'live' | 'demo';
  traceEvents: TraceEvent[];
  expressionMapUrl: string | null;
  diseaseMapUrl: string | null;
  overlapScore: { r: number; percentile: number; label: string } | null;
  confidence: ConfidenceDimension[];
  report: ReportSections | null;
  pdfUrl: string | null;
  pdfFilename: string | null;
  error: string | null;
}
```

### 10.2 SSE Hook (src/hooks/useAgentStream.ts)
```typescript
import { useEffect, useRef } from 'react';
import type { TraceEvent } from '../types';

export function useAgentStream(
  sessionId: string | null,
  onEvent: (event: TraceEvent) => void
) {
  const eventSourceRef = useRef<EventSource | null>(null);

  useEffect(() => {
    if (!sessionId) return;

    const url = `${import.meta.env.VITE_API_BASE_URL}/api/stream/${sessionId}`;
    const eventSource = new EventSource(url);
    eventSourceRef.current = eventSource;

    // Handle each event type
    const eventTypes: TraceEvent['type'][] = [
      'agent_thought', 'tool_call', 'tool_result', 'confidence_update',
      'brain_map', 'overlap_score', 'report_ready', 'pdf_ready', 'error'
    ];

    eventTypes.forEach(eventType => {
      eventSource.addEventListener(eventType, (e: MessageEvent) => {
        const data = JSON.parse(e.data) as TraceEvent;
        onEvent({ ...data, type: eventType });
      });
    });

    eventSource.onerror = () => {
      eventSource.close();
    };

    return () => {
      eventSource.close();
    };
  }, [sessionId, onEvent]);
}
```

### 10.3 Vite Config (vite.config.ts)
```typescript
import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

export default defineConfig({
  plugins: [react()],
  server: {
    port: 5173,
    proxy: {
      '/api': {
        target: 'http://localhost:8000',
        changeOrigin: true,
      }
    }
  }
})
```

### 10.4 Tailwind Config (tailwind.config.ts)
```typescript
import type { Config } from 'tailwindcss'

export default {
  content: ['./index.html', './src/**/*.{js,ts,jsx,tsx}'],
  theme: {
    extend: {
      fontFamily: {
        mono: ['JetBrains Mono', 'Fira Code', 'monospace'],
      },
      colors: {
        trace: {
          thought: '#374151',    // gray-700
          tool: '#1d4ed8',       // blue-700
          result: '#15803d',     // green-700
          flag: '#b45309',       // amber-700
        }
      }
    },
  },
  plugins: [],
} satisfies Config
```

---

## 11. PDF Generation (services/pdf_service.py)

```python
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import mm
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Image, Table, TableStyle
from reportlab.lib import colors
from reportlab.lib.enums import TA_LEFT, TA_CENTER

def generate_pdf(session_id: str, report_sections: dict, 
                 expression_map_path: str, disease_map_path: str,
                 target_gene: str, indication: str, overlap_score: dict) -> str:
    """
    Generate a professional PDF report.
    Returns path to the generated PDF.
    """
    
    output_path = f"./sessions/{session_id}/report_{target_gene}_{indication.replace(' ', '_')}.pdf"
    
    doc = SimpleDocTemplate(
        output_path,
        pagesize=A4,
        rightMargin=20*mm,
        leftMargin=20*mm,
        topMargin=20*mm,
        bottomMargin=20*mm
    )
    
    styles = getSampleStyleSheet()
    
    # Custom styles
    title_style = ParagraphStyle('Title', parent=styles['Heading1'], 
                                  fontSize=20, spaceAfter=6)
    section_style = ParagraphStyle('Section', parent=styles['Heading2'],
                                    fontSize=13, spaceBefore=12, spaceAfter=4,
                                    textColor=colors.HexColor('#1d4ed8'))
    body_style = ParagraphStyle('Body', parent=styles['Normal'],
                                 fontSize=10, leading=14)
    disclaimer_style = ParagraphStyle('Disclaimer', parent=styles['Normal'],
                                       fontSize=8, textColor=colors.grey,
                                       fontName='Helvetica-Oblique')
    
    story = []
    
    # Header
    story.append(Paragraph("CircuitMap", title_style))
    story.append(Paragraph(f"CNS Target Validation Report", styles['Heading2']))
    story.append(Paragraph(f"Target: {target_gene} | Indication: {indication}", body_style))
    story.append(Paragraph(f"Generated: {datetime.now().strftime('%B %d, %Y')}", body_style))
    story.append(Spacer(1, 10*mm))
    
    # Brain maps side by side
    if expression_map_path and disease_map_path and os.path.exists(expression_map_path):
        img_data = [
            [Image(expression_map_path, width=80*mm, height=50*mm),
             Image(disease_map_path, width=80*mm, height=50*mm)]
        ]
        img_table = Table(img_data, colWidths=[85*mm, 85*mm])
        story.append(img_table)
        story.append(Spacer(1, 5*mm))
    
    # Overlap score
    if overlap_score:
        story.append(Paragraph(
            f"Target-Pathology Overlap: r = {overlap_score['r']} "
            f"({overlap_score['percentile']}th percentile)",
            styles['Heading3']
        ))
        story.append(Spacer(1, 5*mm))
    
    # All 11 report sections
    section_map = {
        'executive_summary': 'Executive Summary',
        'molecular_target_profile': 'Molecular Target Profile',
        'brain_expression_analysis': 'Brain Expression Analysis',
        'functional_circuit_context': 'Functional Circuit Context',
        'target_pathology_overlap': 'Target-Pathology Overlap',
        'off_target_risk_assessment': 'Off-Target Risk Assessment',
        'literature_evidence_summary': 'Literature Evidence Summary',
        'recommended_clinical_endpoints': 'Recommended Clinical Endpoints',
        'confidence_assessment': 'Confidence Assessment',
        'preclinical_validation_recommendations': 'Pre-Clinical Validation Recommendations',
        'data_sources_and_limitations': 'Data Sources & Limitations',
    }
    
    for key, title in section_map.items():
        if key in report_sections and report_sections[key]:
            story.append(Paragraph(title, section_style))
            story.append(Paragraph(report_sections[key], body_style))
            story.append(Spacer(1, 4*mm))
    
    # Footer disclaimer
    story.append(Spacer(1, 8*mm))
    story.append(Paragraph(
        "DISCLAIMER: This report represents pre-clinical computational evidence only. "
        "It is not intended for clinical use, does not constitute medical advice, and "
        "does not replace clinical trials or regulatory review. All findings should be "
        "validated through established experimental methods before clinical application.",
        disclaimer_style
    ))
    
    doc.build(story)
    return output_path
```

---

## 12. Development Commands

### Backend
```bash
# Start backend dev server (with auto-reload)
cd backend
uvicorn main:app --reload --port 8000

# Run pre-event setup scripts (do this before hackathon)
python scripts/preload_ahba.py          # ~15 min, ~500MB
python scripts/preload_neurosynth.py    # ~10 min
python scripts/build_rag_store.py       # ~30 min
python scripts/precompute_demo.py       # ~15 min (needs ANTHROPIC_API_KEY)

# Test individual services
python -c "from services.ahba_service import get_expression_map; print(get_expression_map('SUV39H1', 'test'))"
python -c "from services.rag_service import search_literature; print(search_literature('SUV39H1 Alzheimer hippocampus'))"
```

### Frontend
```bash
# Start frontend dev server
cd frontend
npm run dev   # Runs on http://localhost:5173

# Build for production
npm run build

# Type check
npm run tsc --noEmit
```

---

## 13. Critical Pre-Hackathon Checklist

Run these the night before the event. Do NOT rely on event WiFi for large downloads.

- [ ] `python scripts/preload_ahba.py` — AHBA dataset downloaded and verified
- [ ] `python scripts/preload_neurosynth.py` — Neurosynth database downloaded
- [ ] `python scripts/build_rag_store.py` — ChromaDB built with PubMed abstracts
- [ ] `ANTHROPIC_API_KEY` set in backend/.env
- [ ] `python scripts/precompute_demo.py` — All 3 demo scenarios cached
- [ ] Demo scenario 1 (SUV39H1/Alzheimer's) loads correctly
- [ ] Brain map PNGs visible at `/cache/demo/alzheimers_expression.png`
- [ ] PDF export working for demo scenario 1
- [ ] Frontend running at localhost:5173 with backend proxy working
- [ ] SSE stream visible in browser DevTools Network tab
- [ ] Laptop HDMI adapter packed
- [ ] Backup screenshots of each demo scenario saved as fallback

---

## 14. Fallback Strategy

If any live component fails during the demo, execute this hierarchy:

1. **Primary:** Live agent run with real API calls (full agentic loop)
2. **Fallback A:** Demo mode — load pre-computed Scenario 1 with playback simulation
3. **Fallback B:** Static screenshots of the complete UI loaded in a browser tab
4. **Never:** Debug live in front of judges. Switch to the next fallback immediately.

The demo should be bullet-proof because:
- All AHBA data is local (no external dependency)
- ChromaDB is local (no external dependency)
- Only ChEMBL API, Neurosynth queries, and Anthropic API require internet
- Demo mode requires only Anthropic API (for playback of pre-recorded trace) or fully offline from cache
