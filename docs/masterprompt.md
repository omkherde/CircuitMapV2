# CircuitMap — Claude Code Master Build Prompt

**Hand this file to Claude Code along with prd.md and techstack.md.**
**Read all three files completely before writing a single line of code.**

---

## Your Mission

You are building CircuitMap: an autonomous CNS drug target validation agent. The full product specification is in `prd.md`. The exact tech stack is in `techstack.md`. This file (`masterprompt.md`) tells you *how* to build it — the exact sequence, the known failure points, and the patterns that prevent errors.

Your goal is a working demo by end of session. Prioritize correctness over elegance. A working MVP beats beautiful broken code. When in doubt, build the simplest thing that satisfies the PRD requirement.

---

## Non-Negotiable Rules

1. **Read before you write.** Before implementing any component, restate what it does, what it takes as input, and what it returns. If your restatement conflicts with the PRD, stop and re-read the PRD.

2. **Test each service in isolation before wiring it together.** Every service file must have a `if __name__ == "__main__"` block that runs a minimal test. Run it before moving to the next service.

3. **Never import from a module you haven't verified works.** If `ahba_service.py` hasn't been tested successfully, do not import it in `main.py`.

4. **Use the exact library versions in `techstack.md`.** Do not upgrade or substitute. These versions are pinned for compatibility reasons.

5. **Never use blocking I/O in async FastAPI routes directly.** All scientific library calls are synchronous and blocking. They must be wrapped in `asyncio.run_in_executor`. This is non-negotiable.

6. **Never hallucinate library APIs.** If you are not certain of a function signature, say so and check the code. The scientific libraries (abagen, neurosynth, chembl_webresource_client) have non-obvious APIs.

7. **Commit working fallbacks before complex features.** Build demo mode (pre-computed cache playback) before the live agent loop. The demo must work even if the live agent fails.

---

## Build Order — Follow Exactly

### Phase 0: Environment & Scaffold (do this first, verify before proceeding)

**Step 0.1 — Create project structure**
Create the exact directory tree from `techstack.md §4`. Create all `__init__.py` files. Create empty placeholder files for every module listed. Do not write implementation yet — just the skeleton.

**Step 0.2 — Create requirements.txt and .env.example**
Use exact versions from `techstack.md §2.2`. No version ranges — use `==` for every dependency.

**Step 0.3 — Create virtual environment and install**
```bash
python3.11 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```
Verify installation with:
```bash
python -c "import anthropic, fastapi, abagen, nilearn, neurosynth, chromadb, chembl_webresource_client; print('All imports OK')"
```
**Do not proceed if any import fails.** Fix the import error first.

**Step 0.4 — Create .env from .env.example**
Populate with the user's `ANTHROPIC_API_KEY`. Verify with:
```bash
python -c "from dotenv import load_dotenv; import os; load_dotenv(); print('Key set:', bool(os.getenv('ANTHROPIC_API_KEY')))"
```

---

### Phase 1: Pre-Event Setup Scripts (build and run before anything else)

These scripts populate the data caches that all services depend on. Build them first because they take 30-60 minutes to run and must complete before the app works.

**Step 1.1 — Build `scripts/preload_ahba.py`**

```python
"""
Downloads Allen Human Brain Atlas microarray data.
CRITICAL: Run on home WiFi. Takes ~15 minutes, ~500MB.
"""
import os
import sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from dotenv import load_dotenv
load_dotenv()

import abagen

DATA_DIR = os.getenv("AHBA_DATA_DIR", "./cache/ahba_data")
os.makedirs(DATA_DIR, exist_ok=True)

print("Starting AHBA download (~500MB)...")
try:
    files = abagen.fetch_microarray(
        data_dir=DATA_DIR,
        donors='all',
        verbose=1
    )
    print(f"SUCCESS: Downloaded {len(files)} files")
    
    # Verify data loads
    print("Verifying data loads...")
    expression = abagen.get_expression_data(
        atlas=None,
        data_dir=DATA_DIR,
        return_donors=False,
        verbose=0
    )
    print(f"Expression matrix shape: {expression.shape}")
    print(f"Sample genes present: {['SUV39H1' in expression.columns, 'COMT' in expression.columns, 'HDAC2' in expression.columns]}")
    print("AHBA preload COMPLETE")
except Exception as e:
    print(f"FAILED: {e}")
    raise
```

**KNOWN ISSUE:** `abagen.fetch_microarray` may fail if the AHBA API is down. If it fails, try `donors=['9861', '10021']` (just two donors) as a fallback. Two donors is sufficient for the demo.

**KNOWN ISSUE:** abagen's `get_expression_data` with `atlas=None` uses an internal DK atlas. If it raises an error about atlas coordinates, explicitly pass `atlas` as a `nibabel` NIfTI object — see abagen documentation for `fetch_atlas_desikan_killiany`.

**Step 1.2 — Build `scripts/preload_neurosynth.py`**

```python
"""
Downloads Neurosynth database.
CRITICAL: Run on home WiFi. Takes ~10 minutes.
"""
import os, sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

DATA_DIR = os.getenv("NEUROSYNTH_DATA_DIR", "./cache/neurosynth_data")
os.makedirs(DATA_DIR, exist_ok=True)

# Download using neurosynth's built-in downloader
import neurosynth.utils
print("Downloading Neurosynth database...")
neurosynth.utils.download(data_dir=DATA_DIR, unpack=True)

# Build and pickle the dataset for fast loading
from neurosynth.base.dataset import Dataset
print("Building dataset...")
dataset = Dataset(
    os.path.join(DATA_DIR, "database.txt"),
    os.path.join(DATA_DIR, "features.txt")
)
dataset.save(os.path.join(DATA_DIR, "dataset.pkl"))
print(f"Dataset saved. Features: {len(dataset.get_feature_names())}")

# Verify key terms exist
for term in ['alzheimer', 'schizophrenia', 'depression']:
    studies = dataset.get_studies(features=term, frequency_threshold=0.001)
    print(f"  '{term}': {len(studies)} studies")
print("Neurosynth preload COMPLETE")
```

**KNOWN ISSUE:** The Neurosynth `download` utility may download files to a subdirectory. Check for files at `DATA_DIR/database.txt` — if not there, look in `DATA_DIR/data/`. Adjust paths accordingly.

**KNOWN ISSUE:** `dataset.get_studies(features=term)` requires `frequency_threshold` parameter in older versions. Use `frequency_threshold=0.001` as default.

**Step 1.3 — Build `scripts/build_rag_store.py`**

```python
"""
Fetches PubMed abstracts and builds ChromaDB vector store.
Requires internet. Takes ~30 minutes.
"""
import os, sys, time
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
from dotenv import load_dotenv
load_dotenv()

from Bio import Entrez
import chromadb
from chromadb.utils import embedding_functions

Entrez.email = "circuitmap@hackathon.ai"

DATA_DIR = os.getenv("CHROMA_DB_DIR", "./cache/chroma_db")
os.makedirs(DATA_DIR, exist_ok=True)

GENES = ['SUV39H1', 'COMT', 'HDAC2', 'HDAC1', 'EHMT2', 'BDNF',
         'MAOA', 'SLC6A4', 'DRD2', 'DNMT3A']
DISEASES = ['alzheimer', 'schizophrenia', 'depression', 'parkinson']

def fetch_abstracts(query: str, max_results: int = 30) -> list:
    try:
        handle = Entrez.esearch(db="pubmed", term=query, retmax=max_results)
        record = Entrez.read(handle)
        handle.close()
        ids = record.get("IdList", [])
        if not ids:
            return []
        time.sleep(0.4)  # Respect NCBI rate limit
        handle = Entrez.efetch(db="pubmed", id=",".join(ids),
                               rettype="abstract", retmode="xml")
        records = Entrez.read(handle)
        handle.close()
        abstracts = []
        for article in records.get("PubmedArticle", []):
            try:
                ml = article["MedlineCitation"]
                art = ml["Article"]
                abstract = str(art.get("Abstract", {}).get("AbstractText", ""))
                title = str(art.get("ArticleTitle", ""))
                pmid = str(ml["PMID"])
                year = str(ml.get("DateCompleted", {}).get("Year", "2020"))
                journal = str(art.get("Journal", {}).get("Title", ""))
                if abstract and len(abstract) > 80:
                    abstracts.append({
                        "text": f"{title}\n{abstract}",
                        "pmid": pmid, "title": title,
                        "year": year, "journal": journal
                    })
            except Exception:
                continue
        return abstracts
    except Exception as e:
        print(f"  PubMed fetch error: {e}")
        return []

# Initialize ChromaDB
client = chromadb.PersistentClient(path=DATA_DIR)
ef = embedding_functions.SentenceTransformerEmbeddingFunction(
    model_name="all-MiniLM-L6-v2",
    device="cpu"  # Force CPU — no GPU assumption
)
try:
    client.delete_collection("pubmed_abstracts")
except Exception:
    pass
collection = client.create_collection(
    name="pubmed_abstracts",
    embedding_function=ef,
    metadata={"hnsw:space": "cosine"}
)

total = 0
for gene in GENES:
    for disease in DISEASES:
        query = f"{gene} {disease} brain neuroscience"
        abstracts = fetch_abstracts(query, max_results=20)
        for ab in abstracts:
            doc_id = f"{gene}_{disease}_{ab['pmid']}"
            try:
                collection.add(
                    documents=[ab["text"]],
                    ids=[doc_id],
                    metadatas=[{
                        "gene": gene, "disease": disease,
                        "pmid": ab["pmid"], "title": ab["title"][:200],
                        "year": ab["year"], "journal": ab["journal"][:100]
                    }]
                )
                total += 1
            except Exception:
                pass  # Skip duplicates silently
        print(f"  {gene} + {disease}: {len(abstracts)} abstracts → total {total}")
        time.sleep(0.3)

print(f"ChromaDB built. Total documents: {collection.count()}")
```

**Step 1.4 — Run all three scripts sequentially**
```bash
cd backend
python scripts/preload_ahba.py
python scripts/preload_neurosynth.py
python scripts/build_rag_store.py
```
Do not proceed to Phase 2 until all three complete without errors.

---

### Phase 2: Services Layer (build and test each independently)

Build services in this exact order. Each must pass its own test before proceeding.

**Step 2.1 — `services/chembl_service.py`**

**What it does:** Takes a drug name or SMILES string, returns up to 3 CNS targets with binding affinities from ChEMBL. Falls back to PubChem if ChEMBL returns nothing.

**Critical implementation notes:**
- ChEMBL client calls are synchronous — this is fine here since we wrap in executor at the agent level
- Filter activities to `standard_type__in=['Ki', 'IC50', 'Kd']` and `target_organism='Homo sapiens'`
- Filter targets to `target_type='SINGLE PROTEIN'` to exclude cell lines
- Sort results by `standard_value` ascending (lower nM = stronger binding)
- Always return a dict, never raise an exception — return `{"error": "...", "targets": []}` on failure
- For SMILES input: use `molecule.filter(smiles__flexmatch=smiles)` NOT exact match
- For name input: try `pref_name__iexact` first, then `molecule_synonyms__synonym__iexact`

**Test block:**
```python
if __name__ == "__main__":
    result = resolve_target("Donepezil", "name")
    print(result)
    assert result.get("primary_target"), "Should find ACHE for Donepezil"
    print("chembl_service TEST PASSED")
```

**Step 2.2 — `services/ahba_service.py`**

**What it does:** Takes a gene name, queries AHBA via abagen, returns top 10 brain regions by expression percentile and a PNG path.

**Critical implementation notes:**

MATPLOTLIB BACKEND — This is the single most common failure point for server-side neuroimaging. Set the backend to `Agg` BEFORE any other matplotlib import:
```python
import matplotlib
matplotlib.use('Agg')  # MUST be before any other matplotlib import
import matplotlib.pyplot as plt
from nilearn import plotting
```

ABAGEN API — Use this exact call pattern. Do not deviate:
```python
expression = abagen.get_expression_data(
    atlas=None,        # Uses internal Desikan-Killiany atlas
    data_dir=DATA_DIR, # Must be the AHBA data directory
    return_donors=False,    # Aggregate across all donors
    norm_structures=True,   # Normalize within brain structures
    verbose=0               # Suppress progress output
)
```

The return value is a `pandas.DataFrame` with shape `(n_regions, n_genes)`. Rows are brain regions, columns are gene names.

If the target gene is not in `expression.columns`, return a graceful error dict:
```python
if gene_name not in expression.columns:
    return {"error": f"Gene {gene_name} not found in AHBA. Check HGNC symbol.", "top_regions": []}
```

PERCENTILE CALCULATION:
```python
from scipy import stats
import numpy as np
gene_values = expression[gene_name]
percentiles = stats.rankdata(gene_values) / len(gene_values) * 100
```

NILEARN VISUALIZATION — Use this exact pattern for server-side PNG generation:
```python
def _generate_expression_png(gene_values: pd.Series, session_id: str, gene_name: str) -> str:
    """Generate brain expression map as PNG. Returns absolute file path."""
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    from nilearn import plotting
    
    output_dir = os.path.join(SESSIONS_DIR, session_id)
    os.makedirs(output_dir, exist_ok=True)
    output_path = os.path.join(output_dir, "expression.png")
    
    # Normalize values to 0-1 for visualization
    values = gene_values.values
    norm_values = (values - values.min()) / (values.max() - values.min() + 1e-8)
    
    fig, ax = plt.subplots(1, 1, figsize=(10, 4))
    
    # Bar chart of top 15 regions — more reliable than NIfTI projection
    top_idx = np.argsort(norm_values)[::-1][:15]
    top_regions = [gene_values.index[i] for i in top_idx]
    top_values = [norm_values[i] for i in top_idx]
    
    colors = plt.cm.RdBu_r(np.array(top_values))
    bars = ax.barh(range(len(top_regions)), top_values, color=colors)
    ax.set_yticks(range(len(top_regions)))
    ax.set_yticklabels(top_regions, fontsize=9)
    ax.set_xlabel("Normalized expression (percentile rank)")
    ax.set_title(f"{gene_name} — Brain Expression (Allen Human Brain Atlas)")
    ax.invert_yaxis()
    ax.set_xlim(0, 1.1)
    
    plt.tight_layout()
    plt.savefig(output_path, dpi=150, bbox_inches='tight', facecolor='white')
    plt.close('all')  # CRITICAL: close all figures to prevent memory leak
    
    return output_path
```

**NOTE:** Using a regional bar chart instead of a NIfTI surface projection. This is more reliable, faster, and equally readable for the demo. The NIfTI projection requires atlas coordinate alignment that adds 30+ minutes of complexity.

**Store the map data for correlation:**
```python
# Global dict scoped to session — keys are map_id strings
_map_store: dict[str, dict] = {}

def store_parcellated_map(map_id: str, parcellated_values: dict):
    _map_store[map_id] = parcellated_values

def get_parcellated_map(map_id: str) -> dict | None:
    return _map_store.get(map_id)
```

**Test block:**
```python
if __name__ == "__main__":
    result = get_expression_map("COMT", "test_session")
    print("Top regions:", result["top_regions"][:3])
    assert result["top_regions"], "Should return regions"
    assert os.path.exists(result["image_path"]), "PNG should exist"
    print("ahba_service TEST PASSED")
```

**Step 2.3 — `services/neurosynth_service.py`**

**What it does:** Two functions — `get_disease_map` and `get_cognitive_associations`. Both use the pre-loaded Neurosynth dataset.

**Critical implementation notes:**

LOAD DATASET ONCE — Load as a module-level singleton, not inside each function call:
```python
import pickle
import os

_dataset = None

def _get_dataset():
    global _dataset
    if _dataset is None:
        data_dir = os.getenv("NEUROSYNTH_DATA_DIR", "./cache/neurosynth_data")
        pkl_path = os.path.join(data_dir, "dataset.pkl")
        if os.path.exists(pkl_path):
            with open(pkl_path, 'rb') as f:
                _dataset = pickle.load(f)
        else:
            from neurosynth.base.dataset import Dataset
            _dataset = Dataset(
                os.path.join(data_dir, "database.txt"),
                os.path.join(data_dir, "features.txt")
            )
    return _dataset
```

INDICATION TERM MAPPING — Always map user-facing terms to Neurosynth feature terms:
```python
INDICATION_TERM_MAP = {
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

def _map_indication(indication: str) -> str:
    return INDICATION_TERM_MAP.get(indication.lower().strip(), 
                                    indication.lower().strip().split()[0])
```

META-ANALYSIS — Use this pattern:
```python
from neurosynth.analysis import meta

def get_disease_map(indication: str, session_id: str) -> dict:
    dataset = _get_dataset()
    term = _map_indication(indication)
    
    study_ids = dataset.get_studies(features=term, frequency_threshold=0.001)
    
    if not study_ids:
        return {"error": f"No studies found for '{term}'. Try a simpler term.", 
                "top_regions": [], "map_id": None}
    
    ma = meta.MetaAnalysis(dataset, study_ids)
    # pAgF = posterior probability of activation given feature
    pAgF_img = ma.images.get('pAgF')
    
    if pAgF_img is None:
        # Try alternative image key
        for key in ma.images:
            if 'pAgF' in key or 'posterior' in key.lower():
                pAgF_img = ma.images[key]
                break
    
    # Generate PNG using Nilearn
    image_path = _generate_disease_png(pAgF_img, session_id, term)
    
    # Parcellate to regions for correlation
    parcellated = _parcellate_image_to_regions(pAgF_img, dataset)
    
    map_id = f"{session_id}_disease_{term}"
    from services.correlation_service import store_parcellated_map
    store_parcellated_map(map_id, parcellated)
    
    # Top regions
    top_regions = sorted(parcellated.items(), key=lambda x: x[1], reverse=True)[:10]
    
    return {
        "indication": indication,
        "neurosynth_term": term,
        "map_id": map_id,
        "n_studies": len(study_ids),
        "top_regions": [{"region": r, "value": round(v, 4)} for r, v in top_regions],
        "image_path": image_path
    }
```

PARCELLATION — Convert NIfTI image to regional values using Neurosynth's masker:
```python
def _parcellate_image_to_regions(img, dataset) -> dict:
    """
    Convert NIfTI stat map to a dict of {region_label: value}.
    Uses Neurosynth's built-in region masks if available,
    otherwise uses a simple peak-coordinate approach.
    """
    import numpy as np
    import nibabel as nib
    
    # Simple approach: use predefined ROI coordinates
    # These are MNI coordinates for 20 key brain regions
    ROI_COORDS = {
        "hippocampus_L": (-24, -20, -18),
        "hippocampus_R": (24, -20, -18),
        "entorhinal_L": (-28, -8, -36),
        "entorhinal_R": (28, -8, -36),
        "prefrontal_dlPFC_L": (-46, 30, 26),
        "prefrontal_dlPFC_R": (46, 30, 26),
        "anterior_cingulate": (0, 38, 8),
        "amygdala_L": (-24, -4, -22),
        "amygdala_R": (24, -4, -22),
        "striatum_L": (-18, 12, 0),
        "striatum_R": (18, 12, 0),
        "thalamus_L": (-10, -18, 6),
        "thalamus_R": (10, -18, 6),
        "insula_L": (-38, -4, 12),
        "insula_R": (38, -4, 12),
        "cerebellum_L": (-20, -60, -28),
        "cerebellum_R": (20, -60, -28),
        "occipital_L": (-30, -88, 14),
        "occipital_R": (30, -88, 14),
        "parietal": (0, -60, 46),
    }
    
    if img is None:
        return {r: 0.0 for r in ROI_COORDS}
    
    try:
        data = img.get_fdata()
        affine = img.affine
        inv_affine = np.linalg.inv(affine)
        
        result = {}
        for region, mni_coords in ROI_COORDS.items():
            # Convert MNI to voxel coords
            vox = np.round(inv_affine @ [*mni_coords, 1]).astype(int)[:3]
            # Clamp to image bounds
            vox = np.clip(vox, 0, np.array(data.shape) - 1)
            try:
                result[region] = float(data[vox[0], vox[1], vox[2]])
            except (IndexError, ValueError):
                result[region] = 0.0
        return result
    except Exception:
        return {r: 0.0 for r in ROI_COORDS}
```

COGNITIVE ASSOCIATIONS — Simple keyword approach for hackathon:
```python
def get_cognitive_associations(regions: list, top_n: int = 8) -> dict:
    """
    Map brain regions to cognitive functions.
    Uses a curated lookup table for reliability — 
    Neurosynth decoder is too slow for real-time use.
    """
    REGION_FUNCTION_MAP = {
        "hippocampus": ["episodic memory", "memory consolidation", "spatial navigation", "pattern separation"],
        "entorhinal": ["memory encoding", "grid cells", "spatial processing", "temporal lobe function"],
        "prefrontal": ["working memory", "cognitive control", "decision making", "executive function"],
        "anterior cingulate": ["error monitoring", "cognitive control", "attention", "conflict detection"],
        "amygdala": ["fear processing", "emotional memory", "threat detection", "arousal"],
        "striatum": ["reward processing", "motor learning", "habit formation", "dopamine signaling"],
        "thalamus": ["sensory relay", "attention gating", "arousal regulation", "consciousness"],
        "insula": ["interoception", "pain processing", "emotional awareness", "disgust"],
        "cerebellum": ["motor coordination", "procedural learning", "timing", "fine motor control"],
        "parietal": ["spatial attention", "numerical cognition", "somatosensation", "tool use"],
        "occipital": ["visual processing", "object recognition", "face perception", "motion detection"],
    }
    
    all_functions = []
    for region in regions:
        region_lower = region.lower()
        for key, functions in REGION_FUNCTION_MAP.items():
            if key in region_lower:
                all_functions.extend(functions)
    
    # Count and return most common
    from collections import Counter
    counts = Counter(all_functions)
    top_functions = counts.most_common(top_n)
    
    return {
        "queried_regions": regions,
        "cognitive_associations": [
            {"function": f, "frequency": c} for f, c in top_functions
        ],
        "method": "curated region-function lookup table"
    }
```

**IMPORTANT:** Using a curated lookup table instead of Neurosynth's decoder. The decoder takes 2-5 minutes per query — unacceptable for a real-time demo. The curated table is fast, reliable, and scientifically accurate for the major regions.

**Test block:**
```python
if __name__ == "__main__":
    result = get_disease_map("Alzheimer's disease", "test_session")
    print("Disease map term:", result.get("neurosynth_term"))
    print("N studies:", result.get("n_studies"))
    print("Top regions:", result.get("top_regions", [])[:3])
    assert result.get("map_id"), "Should return map_id"
    print("neurosynth_service TEST PASSED")
```

**Step 2.4 — `services/correlation_service.py`**

**What it does:** Computes Pearson correlation between two parcellated brain maps stored in memory.

**Critical implementation notes:**
- The map store must be a module-level dict shared across services
- Ensure both maps have the same region keys before correlating
- Handle NaN values — replace with 0.0 before computing correlation
- The 1000-permutation null takes ~0.5 seconds — acceptable
- Fixed seed (42) ensures reproducibility across demo runs

```python
import numpy as np
from scipy import stats
from typing import Optional

# Module-level map store — shared between ahba_service and neurosynth_service
_map_store: dict[str, dict[str, float]] = {}

def store_parcellated_map(map_id: str, values: dict[str, float]) -> None:
    _map_store[map_id] = values

def get_parcellated_map(map_id: str) -> Optional[dict[str, float]]:
    return _map_store.get(map_id)

def compute_overlap(map1_id: str, map2_id: str, label: str) -> dict:
    if map1_id not in _map_store:
        return {"error": f"Map '{map1_id}' not found. Run get_brain_expression first."}
    if map2_id not in _map_store:
        return {"error": f"Map '{map2_id}' not found. Run get_disease_map first."}
    
    map1 = _map_store[map1_id]
    map2 = _map_store[map2_id]
    
    # Find common regions
    common = sorted(set(map1.keys()) & set(map2.keys()))
    
    if len(common) < 10:
        return {
            "error": f"Only {len(common)} common regions between maps. Need at least 10.",
            "r": 0.0, "percentile": 50
        }
    
    vec1 = np.array([map1[r] for r in common], dtype=float)
    vec2 = np.array([map2[r] for r in common], dtype=float)
    
    # Handle NaN
    vec1 = np.nan_to_num(vec1, 0.0)
    vec2 = np.nan_to_num(vec2, 0.0)
    
    # Handle zero variance
    if vec1.std() < 1e-10 or vec2.std() < 1e-10:
        return {"r": 0.0, "percentile": 50, "label": label,
                "interpretation": "weak",
                "note": "Near-zero variance in one map — insufficient data"}
    
    r_obs, p_obs = stats.pearsonr(vec1, vec2)
    
    # Null distribution via permutation
    rng = np.random.default_rng(seed=42)
    null_rs = np.array([
        stats.pearsonr(vec1, rng.permutation(vec2))[0]
        for _ in range(1000)
    ])
    
    percentile = int(np.mean(null_rs < r_obs) * 100)
    
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
        "n_regions": len(common),
        "interpretation": interpretation,
        "label": label,
        "note": "Null distribution: 1000 random permutations, seed=42"
    }
```

**Test block:**
```python
if __name__ == "__main__":
    store_parcellated_map("test_map1", {"hippocampus_L": 0.9, "hippocampus_R": 0.8,
                                         "amygdala_L": 0.3, "amygdala_R": 0.2,
                                         "prefrontal_dlPFC_L": 0.7, "prefrontal_dlPFC_R": 0.6,
                                         "striatum_L": 0.1, "striatum_R": 0.1,
                                         "thalamus_L": 0.4, "thalamus_R": 0.4,
                                         "cerebellum_L": 0.05, "cerebellum_R": 0.05})
    store_parcellated_map("test_map2", {"hippocampus_L": 0.85, "hippocampus_R": 0.75,
                                         "amygdala_L": 0.25, "amygdala_R": 0.15,
                                         "prefrontal_dlPFC_L": 0.65, "prefrontal_dlPFC_R": 0.55,
                                         "striatum_L": 0.12, "striatum_R": 0.11,
                                         "thalamus_L": 0.42, "thalamus_R": 0.38,
                                         "cerebellum_L": 0.08, "cerebellum_R": 0.06})
    result = compute_overlap("test_map1", "test_map2", "test overlap")
    print(f"r={result['r']}, percentile={result['percentile']}")
    assert result['r'] > 0.9, "Correlated maps should have high r"
    print("correlation_service TEST PASSED")
```

**Step 2.5 — `services/rag_service.py`**

**Critical implementation notes:**
- Load ChromaDB client once at module level using `PersistentClient`
- Use `device="cpu"` in SentenceTransformer — no GPU assumption
- Return gracefully if ChromaDB store is empty (pre-scripts haven't run)
- Truncate abstracts to 400 chars for readability in the agent trace

```python
import chromadb
from chromadb.utils import embedding_functions
import os

CHROMA_DIR = os.getenv("CHROMA_DB_DIR", "./cache/chroma_db")
EMBEDDING_MODEL = os.getenv("EMBEDDING_MODEL", "all-MiniLM-L6-v2")

_client = None
_collection = None

def _get_collection():
    global _client, _collection
    if _collection is None:
        _client = chromadb.PersistentClient(path=CHROMA_DIR)
        ef = embedding_functions.SentenceTransformerEmbeddingFunction(
            model_name=EMBEDDING_MODEL,
            device="cpu"
        )
        try:
            _collection = _client.get_collection(
                name="pubmed_abstracts",
                embedding_function=ef
            )
        except Exception:
            # Collection doesn't exist yet — return None gracefully
            return None
    return _collection

def search_literature(query: str, top_k: int = 5) -> dict:
    collection = _get_collection()
    
    if collection is None or collection.count() == 0:
        return {
            "query": query,
            "results": [],
            "error": "RAG store not initialized. Run scripts/build_rag_store.py first.",
            "total_results": 0
        }
    
    top_k = min(top_k, 10, collection.count())
    
    try:
        results = collection.query(
            query_texts=[query],
            n_results=top_k,
            include=["documents", "metadatas", "distances"]
        )
        
        abstracts = []
        for i, doc in enumerate(results["documents"][0]):
            meta = results["metadatas"][0][i]
            abstracts.append({
                "title": meta.get("title", "Unknown title")[:120],
                "authors": meta.get("authors", ""),
                "journal": meta.get("journal", "Unknown journal")[:80],
                "year": meta.get("year", ""),
                "pmid": meta.get("pmid", ""),
                "snippet": doc[:400] + "..." if len(doc) > 400 else doc,
                "similarity_score": round(1 - float(results["distances"][0][i]), 3)
            })
        
        return {
            "query": query,
            "results": abstracts,
            "total_results": len(abstracts),
            "source": "PubMed RAG (pre-embedded, all-MiniLM-L6-v2)"
        }
    except Exception as e:
        return {"query": query, "results": [], "error": str(e), "total_results": 0}
```

**Step 2.6 — `services/pdf_service.py`**

Use ReportLab. Keep it simple — the PDF needs to look professional but not perfect.

**Critical:** Always call `plt.close('all')` after any matplotlib operation. Always check that image files exist before embedding them in the PDF. If image files are missing, skip them gracefully.

---

### Phase 3: Agent Core (build after all services pass their tests)

**Step 3.1 — `agent/prompts.py`**

Copy the system prompt verbatim from `prd.md §6.2`. Do not paraphrase or shorten it. The scientific framing in that prompt is the product's moat.

**Step 3.2 — `agent/tools_schema.py`**

Copy all 6 tool schemas verbatim from `prd.md §6.3`. These must be exact — Claude uses them to decide when and how to call each tool.

**Step 3.3 — `agent/tools.py`**

This module is the bridge between Claude's tool calls and the service implementations.

```python
# agent/tools.py
import asyncio
import json
from concurrent.futures import ThreadPoolExecutor
from typing import Any

_executor = ThreadPoolExecutor(max_workers=4)

async def execute_tool(tool_name: str, tool_input: dict, 
                       session_id: str, event_queue: asyncio.Queue) -> str:
    """
    Execute a tool call from the agent. All tools are synchronous —
    run them in a thread pool to avoid blocking the event loop.
    Returns a JSON string result.
    """
    
    tool_functions = {
        "resolve_target": _resolve_target,
        "get_brain_expression": _get_brain_expression,
        "get_cognitive_associations": _get_cognitive_associations,
        "get_disease_map": _get_disease_map,
        "compute_overlap": _compute_overlap,
        "search_literature": _search_literature,
    }
    
    if tool_name not in tool_functions:
        error = {"error": f"Unknown tool: {tool_name}"}
        await event_queue.put({
            "type": "tool_result",
            "tool": tool_name,
            "summary": f"Error: unknown tool '{tool_name}'"
        })
        return json.dumps(error)
    
    loop = asyncio.get_event_loop()
    
    try:
        result = await loop.run_in_executor(
            _executor,
            lambda: tool_functions[tool_name](tool_input, session_id, event_queue)
        )
        
        # Emit summary event for the trace
        summary = _summarize_result(tool_name, result)
        await event_queue.put({
            "type": "tool_result",
            "tool": tool_name,
            "summary": summary,
            "result": result
        })
        
        # Emit brain_map event if applicable
        if tool_name in ("get_brain_expression", "get_disease_map"):
            if "image_path" in result and result.get("map_id"):
                map_type = "expression" if tool_name == "get_brain_expression" else "disease"
                await event_queue.put({
                    "type": "brain_map",
                    "map_type": map_type,
                    "map_id": result["map_id"],
                    "image_url": f"/api/maps/{session_id}/{map_type}.png",
                    "top_regions": result.get("top_regions", [])
                })
        
        # Emit overlap event
        if tool_name == "compute_overlap" and "r" in result:
            await event_queue.put({
                "type": "overlap_score",
                "r": result["r"],
                "percentile": result["percentile"],
                "label": result.get("label", ""),
                "interpretation": result.get("interpretation", "")
            })
        
        return json.dumps(result)
    
    except Exception as e:
        error_result = {"error": str(e), "tool": tool_name}
        await event_queue.put({
            "type": "tool_result",
            "tool": tool_name,
            "summary": f"Error in {tool_name}: {str(e)}"
        })
        return json.dumps(error_result)


def _summarize_result(tool_name: str, result: dict) -> str:
    """Generate a human-readable one-line summary for the trace panel."""
    if "error" in result:
        return f"Error: {result['error']}"
    
    summaries = {
        "resolve_target": lambda r: f"Target: {r.get('primary_target', 'unknown')} | "
                                     f"Affinity: {r.get('binding_affinity', '?')} nM ({r.get('affinity_type', '')})",
        "get_brain_expression": lambda r: f"Top region: {r['top_regions'][0]['region'] if r.get('top_regions') else 'N/A'} "
                                           f"({r['top_regions'][0]['percentile'] if r.get('top_regions') else 0:.0f}th pct) | "
                                           f"Atlas: {r.get('atlas', 'DK-68')}",
        "get_cognitive_associations": lambda r: f"Top functions: {', '.join([a['function'] for a in r.get('cognitive_associations', [])[:3]])}",
        "get_disease_map": lambda r: f"Term: '{r.get('neurosynth_term', '?')}' | "
                                      f"Studies: {r.get('n_studies', 0)} | "
                                      f"Top region: {r['top_regions'][0]['region'] if r.get('top_regions') else 'N/A'}",
        "compute_overlap": lambda r: f"r = {r.get('r', 0):.3f} | "
                                      f"Percentile: {r.get('percentile', 0)}th | "
                                      f"Alignment: {r.get('interpretation', 'unknown')} | "
                                      f"n_regions = {r.get('n_regions', 0)}",
        "search_literature": lambda r: f"Found {r.get('total_results', 0)} abstracts | "
                                        f"Top: {r['results'][0]['title'][:60] + '...' if r.get('results') else 'none'}",
    }
    
    return summaries.get(tool_name, lambda r: str(r)[:100])(result)


# Wrapper functions that call services
def _resolve_target(inp: dict, session_id: str, eq) -> dict:
    from services.chembl_service import resolve_target
    return resolve_target(inp["query"], inp["query_type"])

def _get_brain_expression(inp: dict, session_id: str, eq) -> dict:
    from services.ahba_service import get_expression_map
    return get_expression_map(inp["gene_name"], session_id)

def _get_cognitive_associations(inp: dict, session_id: str, eq) -> dict:
    from services.neurosynth_service import get_cognitive_associations
    return get_cognitive_associations(inp["regions"], inp.get("top_n", 8))

def _get_disease_map(inp: dict, session_id: str, eq) -> dict:
    from services.neurosynth_service import get_disease_map
    return get_disease_map(inp["indication"], session_id)

def _compute_overlap(inp: dict, session_id: str, eq) -> dict:
    from services.correlation_service import compute_overlap
    return compute_overlap(inp["map1_id"], inp["map2_id"], inp.get("label", ""))

def _search_literature(inp: dict, session_id: str, eq) -> dict:
    from services.rag_service import search_literature
    return search_literature(inp["query"], inp.get("top_k", 5))
```

**Step 3.4 — `agent/loop.py`**

Implement the agentic loop exactly as specified in `prd.md §6.4`. Key notes:

- Use `client.messages.stream()` context manager for streaming
- Collect tool_use blocks from `final_message.content` after streaming completes
- Each tool_use block has `.id`, `.name`, `.input` attributes
- Tool results in messages must be `{"type": "tool_result", "tool_use_id": block.id, "content": result_string}`
- When `stop_reason == "end_turn"`, scan full_text for "TARGET VALIDATION REPORT COMPLETE"
- Parse report sections by splitting on `## ` headers
- The event queue is an `asyncio.Queue()` — always use `await queue.put()`

**CRITICAL STREAMING PATTERN:**
```python
full_text = ""
tool_uses = []

with client.messages.stream(
    model=model,
    max_tokens=4096,
    system=SYSTEM_PROMPT,
    tools=TOOLS,
    messages=messages
) as stream:
    for text_chunk in stream.text_stream:
        full_text += text_chunk
        # Emit text chunks to frontend
        await event_queue.put({
            "type": "agent_thought",
            "content": text_chunk
        })
    
    # IMPORTANT: Get the final message AFTER the context manager finishes streaming
    final_message = stream.get_final_message()

stop_reason = final_message.stop_reason

# Extract tool uses from content blocks
for block in final_message.content:
    if block.type == "tool_use":
        tool_uses.append(block)

# Append to messages
messages.append({"role": "assistant", "content": final_message.content})
```

---

### Phase 4: FastAPI Application

**Step 4.1 — Pydantic Models (`models/requests.py` and `models/responses.py`)**

```python
# models/requests.py
from pydantic import BaseModel, field_validator
from enum import Enum

class QueryType(str, Enum):
    name = "name"
    smiles = "smiles"

class DemoScenario(str, Enum):
    alzheimers = "alzheimers"
    schizophrenia = "schizophrenia"
    depression = "depression"

class ValidateRequest(BaseModel):
    drug_query: str
    query_type: QueryType
    indication: str
    
    @field_validator('drug_query')
    @classmethod
    def drug_query_not_empty(cls, v):
        if len(v.strip()) < 2:
            raise ValueError('drug_query must be at least 2 characters')
        return v.strip()
    
    @field_validator('indication')
    @classmethod
    def indication_not_empty(cls, v):
        if not v.strip():
            raise ValueError('indication must not be empty')
        return v.strip()
```

**Step 4.2 — Main FastAPI App (`main.py`)**

**CORS + SSE configuration — this is commonly broken:**
```python
from fastapi.middleware.cors import CORSMiddleware

# CORS must be added BEFORE any routes
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://localhost:3000", "http://127.0.0.1:5173"],
    allow_credentials=True,
    allow_methods=["GET", "POST", "OPTIONS"],
    allow_headers=["*"],
    expose_headers=["Content-Type", "Cache-Control", "Connection"],
)
```

**SSE endpoint pattern — must use `EventSourceResponse` from `sse_starlette`:**
```python
from sse_starlette.sse import EventSourceResponse
import asyncio, uuid, json
from typing import AsyncGenerator

# In-memory session store
sessions: dict[str, dict] = {}

@app.post("/api/validate")
async def validate(req: ValidateRequest):
    session_id = str(uuid.uuid4())
    queue: asyncio.Queue = asyncio.Queue()
    
    sessions[session_id] = {
        "queue": queue,
        "status": "pending",
        "drug_query": req.drug_query,
        "query_type": req.query_type,
        "indication": req.indication
    }
    
    # Start agent in background
    asyncio.create_task(
        run_agent_for_session(session_id, req, queue)
    )
    
    return {
        "session_id": session_id,
        "stream_url": f"/api/stream/{session_id}",
        "mode": "live"
    }

async def run_agent_for_session(session_id: str, req: ValidateRequest, queue: asyncio.Queue):
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
        await queue.put({"type": "error", "message": str(e)})
        sessions[session_id]["status"] = "error"
    finally:
        await queue.put({"type": "done"})  # Signal stream end

@app.get("/api/stream/{session_id}")
async def stream(session_id: str):
    if session_id not in sessions:
        raise HTTPException(status_code=404, detail="Session not found")
    
    queue = sessions[session_id]["queue"]
    
    async def event_generator() -> AsyncGenerator[dict, None]:
        while True:
            event = await queue.get()
            event_type = event.pop("type", "message")
            
            if event_type == "done":
                break
            
            yield {
                "event": event_type,
                "data": json.dumps(event)
            }
    
    return EventSourceResponse(
        event_generator(),
        headers={
            "Cache-Control": "no-cache",
            "X-Accel-Buffering": "no",  # Disable Nginx buffering
        }
    )
```

---

### Phase 5: Demo Mode & Precompute Scripts

**Step 5.1 — Build `scripts/precompute_demo.py` BEFORE building the frontend**

This script runs the full agent loop for all 3 scenarios and saves:
- The complete sequence of SSE events as a JSON array
- Brain map PNGs
- The final report JSON

```python
"""
Runs 3 demo scenarios and caches results in ./cache/demo/
Run this the night before the hackathon.
"""
import asyncio, json, os, shutil
from pathlib import Path

DEMO_DIR = "./cache/demo"
os.makedirs(DEMO_DIR, exist_ok=True)

SCENARIOS = [
    {"name": "alzheimers", "drug_query": "Chaetocin", "query_type": "name",
     "indication": "Alzheimer's disease"},
    {"name": "schizophrenia", "drug_query": "Tolcapone", "query_type": "name",
     "indication": "schizophrenia"},
    {"name": "depression", "drug_query": "Vorinostat", "query_type": "name",
     "indication": "major depressive disorder"},
]

async def precompute_scenario(scenario: dict):
    from agent.loop import run_agent_session
    
    events = []
    queue = asyncio.Queue()
    session_id = f"demo_{scenario['name']}"
    
    # Run agent
    await run_agent_session(
        session_id=session_id,
        drug_query=scenario["drug_query"],
        query_type=scenario["query_type"],
        indication=scenario["indication"],
        event_queue=queue
    )
    
    # Drain queue
    while not queue.empty():
        event = await queue.get()
        events.append(event)
    
    # Save events
    with open(os.path.join(DEMO_DIR, f"{scenario['name']}.json"), 'w') as f:
        json.dump(events, f, indent=2, default=str)
    
    # Copy brain maps
    for map_type in ["expression", "disease"]:
        src = f"./sessions/{session_id}/{map_type}.png"
        dst = os.path.join(DEMO_DIR, f"{scenario['name']}_{map_type}.png")
        if os.path.exists(src):
            shutil.copy2(src, dst)
            print(f"  Saved {dst}")
        else:
            print(f"  WARNING: {src} not found")
    
    print(f"Scenario '{scenario['name']}' complete: {len(events)} events")

async def main():
    for scenario in SCENARIOS:
        print(f"\nPrecomputing: {scenario['name']}...")
        try:
            await precompute_scenario(scenario)
        except Exception as e:
            print(f"  FAILED: {e}")

asyncio.run(main())
```

**Step 5.2 — Demo endpoint in `main.py`**

```python
@app.get("/api/demo/{scenario}")
async def demo(scenario: str):
    valid = ["alzheimers", "schizophrenia", "depression"]
    if scenario not in valid:
        raise HTTPException(status_code=400, detail=f"Scenario must be one of {valid}")
    
    demo_file = os.path.join(os.getenv("DEMO_CACHE_DIR", "./cache/demo"), f"{scenario}.json")
    
    if not os.path.exists(demo_file):
        raise HTTPException(status_code=404, 
                           detail="Demo not precomputed. Run scripts/precompute_demo.py")
    
    with open(demo_file) as f:
        events = json.load(f)
    
    return {
        "session_id": f"demo_{scenario}",
        "mode": "demo",
        "events": events,
        "expression_map_url": f"/api/maps/demo_{scenario}/expression.png",
        "disease_map_url": f"/api/maps/demo_{scenario}/disease.png"
    }

@app.get("/api/maps/{session_id}/{map_type}.png")
async def serve_map(session_id: str, map_type: str):
    # Check demo cache first
    demo_path = os.path.join(os.getenv("DEMO_CACHE_DIR", "./cache/demo"),
                              f"{session_id}_{map_type}.png")
    session_path = os.path.join("./sessions", session_id, f"{map_type}.png")
    
    for path in [demo_path, session_path]:
        if os.path.exists(path):
            from fastapi.responses import FileResponse
            return FileResponse(path, media_type="image/png")
    
    raise HTTPException(status_code=404, detail="Map not found")
```

---

### Phase 6: React Frontend

**Build components in this order:**

1. `src/types/index.ts` — all TypeScript interfaces (copy from `techstack.md §10.1`)
2. `src/api/client.ts` — Axios instance
3. `src/hooks/useAgentStream.ts` — SSE hook (copy from `techstack.md §10.2`)
4. `src/hooks/useAgentSession.ts` — POST /api/validate
5. `src/components/InputPanel.tsx`
6. `src/components/TraceEntry.tsx`
7. `src/components/ReasoningTrace.tsx`
8. `src/components/BrainMaps.tsx` + `OverlapScore.tsx`
9. `src/components/ConfidencePanel.tsx`
10. `src/utils/parseReport.ts`
11. `src/components/ReportPanel.tsx`
12. `src/components/ExportButton.tsx`
13. `src/App.tsx` — wire everything together

**CRITICAL frontend issues to avoid:**

**SSE connection:** Browser `EventSource` only supports GET requests. It cannot send headers. This is fine — session ID is in the URL path.

**SSE event listener pattern — use named listeners, not `onmessage`:**
```typescript
// CORRECT
const eventTypes = ['agent_thought', 'tool_call', 'tool_result', 'brain_map',
                    'overlap_score', 'confidence_update', 'report_ready', 'pdf_ready', 'error'];

eventTypes.forEach(eventType => {
  es.addEventListener(eventType, (e: MessageEvent) => {
    const data = JSON.parse(e.data);
    onEvent({ ...data, type: eventType as TraceEventType });
  });
});

// WRONG — only catches events without explicit event: field
es.onmessage = (e) => { ... }
```

**Auto-scroll the reasoning trace:**
```typescript
const traceBottomRef = useRef<HTMLDivElement>(null);
useEffect(() => {
  traceBottomRef.current?.scrollIntoView({ behavior: 'smooth' });
}, [traceEvents]);
// At the bottom of the trace list: <div ref={traceBottomRef} />
```

**Demo mode playback — replay events at 800ms intervals:**
```typescript
async function playDemoEvents(events: TraceEvent[], onEvent: (e: TraceEvent) => void) {
  for (const event of events) {
    if (event.type === 'done') break;
    onEvent(event);
    await new Promise(resolve => setTimeout(resolve, 800));
  }
}
```

**Image loading:** Brain map images are served by the backend. Use the `image_url` from the `brain_map` SSE event. Always handle loading states (show placeholder until `onLoad` fires).

---

## Common Failure Modes & Fixes

| Failure | Cause | Fix |
|---------|-------|-----|
| `ImportError: cannot import name 'get_expression_data' from 'abagen'` | Wrong abagen version | Pin to `abagen==0.1.1`, check API docs for this version |
| `TypeError: cannot pickle 'Dataset' object` | Neurosynth dataset pickle issue | Reload from files instead of pickle; skip pickle |
| `RuntimeError: No display available` | Matplotlib using GUI backend on server | Add `matplotlib.use('Agg')` as first import in any file using matplotlib |
| `chromadb.errors.NotFoundError: Collection pubmed_abstracts does not exist` | RAG not built | Run `build_rag_store.py`; return graceful error from `search_literature` |
| SSE stream closes immediately | `EventSourceResponse` returning non-async generator | Generator must be `async def` using `yield`, not `return` |
| `CORS error on /api/stream/` | SSE preflight failing | Add `expose_headers=["*"]` to CORSMiddleware; SSE uses GET so no preflight |
| `anthropic.APIError: tool_use and tool_result` | Malformed tool result in messages | Tool results must be `{"type": "tool_result", "tool_use_id": id, "content": string}` |
| `asyncio.run() cannot be called from a running event loop` | Mixing sync/async | Use `loop.run_in_executor()` for all blocking service calls |
| `NoneType object has no attribute 'get_fdata'` | Neurosynth MetaAnalysis returned None image | Check `ma.images` dict before accessing; use graceful fallback |
| Memory error during Neurosynth meta-analysis | Large study set | Add `frequency_threshold=0.005` to reduce study count |
| `abagen.get_expression_data` taking > 5 minutes | First call loads all data | Load at startup, not per-request; use module-level singleton |
| Brain map PNG not found by frontend | Absolute vs relative path mismatch | Store and serve maps using absolute paths via `os.path.abspath()` |
| `ReportLab: Image not found` | Image path relative to wrong dir | Use `os.path.abspath()` for all image paths in PDF generation |
| PDF download not triggering | Missing `Content-Disposition` header | Set `FileResponse` with `filename=` parameter |

---

## Testing Protocol

Run these checks in sequence. All must pass before running the demo.

```bash
# 1. Health check
curl http://localhost:8000/api/health

# 2. Test ChEMBL
python -c "from services.chembl_service import resolve_target; print(resolve_target('Donepezil', 'name'))"

# 3. Test AHBA
python -c "from services.ahba_service import get_expression_map; r=get_expression_map('COMT','test'); print(r['top_regions'][:2])"

# 4. Test Neurosynth
python -c "from services.neurosynth_service import get_disease_map; r=get_disease_map(\"Alzheimer's disease\",'test'); print(r['n_studies'])"

# 5. Test RAG
python -c "from services.rag_service import search_literature; r=search_literature('SUV39H1 Alzheimer'); print(r['total_results'])"

# 6. Test full API
curl -X POST http://localhost:8000/api/validate \
  -H "Content-Type: application/json" \
  -d '{"drug_query":"Donepezil","query_type":"name","indication":"Alzheimer'\''s disease"}'

# 7. Test demo endpoint
curl http://localhost:8000/api/demo/alzheimers | python -m json.tool | head -30

# 8. Test PDF generation
curl http://localhost:8000/api/report/demo_alzheimers/download -o test.pdf
file test.pdf  # Should say "PDF document"

# 9. Frontend check
# Open http://localhost:5173, click "Load Demo", click "Validate Target"
# Verify trace events appear, brain maps load, report renders
```

---

## Final Validation Before Demo

Run this complete checklist the morning of the hackathon:

- [ ] All 5 backend services pass their individual test blocks
- [ ] `GET /api/health` returns `{"status":"ok","ahba_loaded":true,"chroma_loaded":true}`
- [ ] Live agent run on Scenario 1 (SUV39H1/Alzheimer's) completes in < 3 minutes
- [ ] Reasoning trace shows at least 6 steps in the UI
- [ ] Both brain map images render (expression + disease)
- [ ] Overlap score bar animates correctly
- [ ] Report panel shows all 11 sections
- [ ] PDF export downloads and opens correctly
- [ ] Demo mode plays back Scenario 1 smoothly at 800ms intervals
- [ ] Demo mode brain maps load from cache
- [ ] All three demo scenarios cached and verified
- [ ] HDMI adapter tested with the presentation laptop
- [ ] Browser DevTools shows no console errors
- [ ] Backup screenshots saved as PNG for emergency use

---

## If Something Breaks During the Demo

Hierarchy — execute in order, do not hesitate:

1. **Live agent glitches:** Click "Load Demo" → demo mode takes over instantly
2. **Demo mode fails:** Open pre-saved screenshots in a browser tab, present statically
3. **Full system down:** Open the pre-generated PDF report on screen, walk through it verbally

The pitch does not require the product to be live. The reasoning trace, the brain maps, and the report sections can all be shown from static assets. Never debug live in front of judges.
