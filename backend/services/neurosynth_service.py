"""
neurosynth_service.py — Neurosynth meta-analytic brain maps and cognitive associations.

Two functions:
  - get_disease_map: Meta-analytic activation map for a disease/indication
  - get_cognitive_associations: Curated region-function lookup (fast, reliable)
"""
import os
import pickle
import tempfile

os.environ.setdefault(
    "MPLCONFIGDIR",
    os.path.join(tempfile.gettempdir(), "circuitmap-matplotlib")
)

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

import numpy as np

DATA_DIR = os.getenv("NEUROSYNTH_DATA_DIR", "./cache/neurosynth_data")
SESSIONS_DIR = os.getenv("SESSIONS_DIR", "./sessions")

# Singleton dataset
_dataset = None

INDICATION_TERM_MAP = {
    "alzheimer's disease": "alzheimer",
    "parkinson's disease": "parkinson",
    "schizophrenia": "schizophrenia",
    "major depressive disorder": "depression",
    "major depression": "depression",
    "bipolar disorder": "bipolar",
    "ptsd": "posttraumatic",
    "epilepsy": "epilepsy",
    "als": "amyotrophic",
    "huntington's disease": "huntington",
    "treatment-resistant depression": "depression",
    "anxiety disorders": "anxiety",
    "frontotemporal dementia": "frontotemporal",
}

# MNI coordinates for 20 key brain ROIs
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


def _roi_pattern(**overrides: float) -> dict[str, float]:
    """Build a complete ROI map with sensible defaults plus explicit overrides."""
    pattern = {region: 0.05 for region in ROI_COORDS}
    pattern.update(overrides)
    return pattern


CURATED_DISEASE_PATTERNS = {
    "alzheimer": _roi_pattern(
        hippocampus_L=1.0,
        hippocampus_R=0.98,
        entorhinal_L=0.96,
        entorhinal_R=0.94,
        parietal=0.72,
        prefrontal_dlPFC_L=0.58,
        prefrontal_dlPFC_R=0.58,
        anterior_cingulate=0.44,
        amygdala_L=0.55,
        amygdala_R=0.55,
        thalamus_L=0.30,
        thalamus_R=0.30,
    ),
    "schizophrenia": _roi_pattern(
        prefrontal_dlPFC_L=1.0,
        prefrontal_dlPFC_R=1.0,
        anterior_cingulate=0.84,
        hippocampus_L=0.72,
        hippocampus_R=0.72,
        thalamus_L=0.78,
        thalamus_R=0.78,
        striatum_L=0.70,
        striatum_R=0.70,
        insula_L=0.68,
        insula_R=0.68,
    ),
    "depression": _roi_pattern(
        anterior_cingulate=1.0,
        amygdala_L=0.90,
        amygdala_R=0.90,
        hippocampus_L=0.80,
        hippocampus_R=0.80,
        prefrontal_dlPFC_L=0.76,
        prefrontal_dlPFC_R=0.76,
        insula_L=0.66,
        insula_R=0.66,
        thalamus_L=0.40,
        thalamus_R=0.40,
    ),
    "parkinson": _roi_pattern(
        striatum_L=1.0,
        striatum_R=1.0,
        thalamus_L=0.72,
        thalamus_R=0.72,
        cerebellum_L=0.68,
        cerebellum_R=0.68,
        prefrontal_dlPFC_L=0.38,
        prefrontal_dlPFC_R=0.38,
    ),
    "bipolar": _roi_pattern(
        amygdala_L=1.0,
        amygdala_R=1.0,
        anterior_cingulate=0.84,
        prefrontal_dlPFC_L=0.74,
        prefrontal_dlPFC_R=0.74,
        hippocampus_L=0.56,
        hippocampus_R=0.56,
        striatum_L=0.52,
        striatum_R=0.52,
    ),
    "posttraumatic": _roi_pattern(
        amygdala_L=1.0,
        amygdala_R=1.0,
        hippocampus_L=0.84,
        hippocampus_R=0.84,
        anterior_cingulate=0.70,
        insula_L=0.66,
        insula_R=0.66,
        prefrontal_dlPFC_L=0.56,
        prefrontal_dlPFC_R=0.56,
    ),
    "epilepsy": _roi_pattern(
        hippocampus_L=1.0,
        hippocampus_R=1.0,
        amygdala_L=0.82,
        amygdala_R=0.82,
        thalamus_L=0.60,
        thalamus_R=0.60,
        insula_L=0.48,
        insula_R=0.48,
    ),
    "frontotemporal": _roi_pattern(
        prefrontal_dlPFC_L=1.0,
        prefrontal_dlPFC_R=1.0,
        insula_L=0.84,
        insula_R=0.84,
        amygdala_L=0.70,
        amygdala_R=0.70,
        anterior_cingulate=0.68,
    ),
}


def _get_dataset():
    """
    Load the Neurosynth v7 dataset.

    Returns a dict with keys:
      coords          — pd.DataFrame with columns [id, x, y, z]
      features        — scipy.sparse matrix (n_studies × n_terms), TF-IDF weights
      vocabulary      — list[str] mapping column index → term string
      study_ids       — list[str] mapping row index → study id
      study_id_to_idx — dict[str, int] reverse lookup
      coord_arr       — np.ndarray (N, 3) of all activation coordinates (fast lookup)
      coord_study_ids — list[str] study ID for each row in coord_arr
    """
    global _dataset
    if _dataset is not None:
        return _dataset

    pkl_path = os.path.join(DATA_DIR, "dataset.pkl")
    if not os.path.exists(pkl_path):
        return None

    try:
        with open(pkl_path, "rb") as fh:
            raw = pickle.load(fh)

        # Support both the new v7 dict format and any legacy object
        if not isinstance(raw, dict):
            return None

        import pandas as pd
        import scipy.sparse

        coords_df = raw["coords"]
        features  = raw["features"]
        vocab     = raw["vocabulary"]
        study_ids = raw["study_ids"]
        s2i       = raw["study_id_to_idx"]

        # Pre-compute coordinate array for fast spatial queries
        coord_arr = coords_df[["x", "y", "z"]].to_numpy(dtype=float)
        # Study-id label for every activation row
        id_col = next((c for c in coords_df.columns if c in ("id", "pmid", "study_id")), coords_df.columns[0])
        coord_study_ids = coords_df[id_col].astype(str).tolist()

        _dataset = {
            "coords":          coords_df,
            "features":        features,
            "vocabulary":      vocab,
            "study_ids":       study_ids,
            "study_id_to_idx": s2i,
            "coord_arr":       coord_arr,
            "coord_study_ids": coord_study_ids,
        }
        return _dataset
    except Exception:
        return None


def neurosynth_data_ready() -> bool:
    """Return True when the Neurosynth v7 dataset pickle is present on disk."""
    return os.path.exists(os.path.join(DATA_DIR, "dataset.pkl"))


def _map_indication(indication: str) -> str:
    """Map user-facing indication to Neurosynth feature term."""
    key = indication.lower().strip()
    if key in INDICATION_TERM_MAP:
        return INDICATION_TERM_MAP[key]
    # Try partial match
    for k, v in INDICATION_TERM_MAP.items():
        if k in key or key in k:
            return v
    # Default: take first word, lowercase
    return key.split()[0]


def get_disease_map(indication: str, session_id: str) -> dict:
    """
    Get Neurosynth meta-analytic activation map for a disease/indication.

    Primary path (v7 dataset loaded):
      - Find studies whose TF-IDF weight for the disease term exceeds threshold
      - For each of the 20 ROI coordinates, count activations within 10 mm
        across those studies and normalise to [0, 1]
      - This is a coordinate-density meta-analysis, equivalent to the classic
        Neurosynth forward-inference (P(activation | term)) approach

    Demo/offline fallback:
      - CURATED_DISEASE_PATTERNS — hand-coded ROI values

    Args:
        indication: Disease name (e.g., "Alzheimer's disease")
        session_id: Session ID for output file naming
    """
    term = _map_indication(indication)
    dataset = _get_dataset()

    if dataset is not None:
        result = _disease_map_v7(dataset, indication, term, session_id)
        if result is not None:
            return result

    # Fallback — curated templates
    fallback = _get_curated_disease_map(indication, term, session_id)
    if fallback is not None:
        return fallback

    return {
        "error": (
            "Neurosynth dataset not loaded and no curated template for this indication. "
            "Run scripts/preload_neurosynth.py to download the v7 dataset."
        ),
        "top_regions": [],
        "map_id": None,
    }


def _disease_map_v7(dataset: dict, indication: str, term: str, session_id: str) -> dict | None:
    """
    Build a disease activation map from Neurosynth v7 data.

    Methodology:
      1. Find the column index of `term` in the vocabulary.
      2. Select studies whose TF-IDF weight for that term > 0.001.
      3. For each ROI coordinate, count activations from those studies within
         10 mm and normalise to produce a [0, 1] activation-frequency map.
    """
    import numpy as np

    vocab = dataset["vocabulary"]
    features = dataset["features"]
    study_ids = dataset["study_ids"]
    coord_arr = dataset["coord_arr"]          # (N_acts, 3)
    coord_study_ids = dataset["coord_study_ids"]  # len == N_acts

    # Find matching term columns (partial match so "alzheimer" hits "alzheimer disease" etc.)
    term_cols = [i for i, t in enumerate(vocab) if term.lower() in t.lower()]
    if not term_cols:
        return None

    # Sum TF-IDF weights across matching columns
    import scipy.sparse
    if scipy.sparse.issparse(features):
        term_weights = np.asarray(features[:, term_cols].sum(axis=1)).flatten()
    else:
        term_weights = features[:, term_cols].sum(axis=1)

    # Studies with meaningful weight for this term
    threshold = 0.001
    relevant_mask = term_weights > threshold
    relevant_study_set = set(np.array(study_ids)[relevant_mask])

    if not relevant_study_set:
        return None

    # Filter activation coordinates to relevant studies
    relevant_act_mask = np.array([sid in relevant_study_set for sid in coord_study_ids])
    relevant_coords = coord_arr[relevant_act_mask]  # (M, 3)

    if len(relevant_coords) == 0:
        return None

    n_studies = int(relevant_mask.sum())

    # Count activations within 10 mm of each ROI
    parcellated: dict[str, float] = {}
    for roi_label, (rx, ry, rz) in ROI_COORDS.items():
        dists = np.sqrt(np.sum((relevant_coords - np.array([rx, ry, rz])) ** 2, axis=1))
        parcellated[roi_label] = float((dists <= 10.0).sum())

    # Normalise to [0, 1]
    max_val = max(parcellated.values()) or 1.0
    parcellated = {k: round(v / max_val, 4) for k, v in parcellated.items()}

    map_id = f"{session_id}_disease_{term}"
    image_path = _generate_disease_png_from_parcellated(parcellated, session_id, term)

    from services.correlation_service import store_parcellated_map
    store_parcellated_map(map_id, parcellated)

    top_regions = sorted(parcellated.items(), key=lambda x: x[1], reverse=True)[:10]

    return {
        "indication": indication,
        "neurosynth_term": term,
        "map_id": map_id,
        "n_studies": n_studies,
        "top_regions": [{"region": r, "value": v} for r, v in top_regions],
        "image_path": image_path,
        "source": f"Neurosynth v7 coordinate-density meta-analysis ({n_studies} studies)",
    }


def get_cognitive_associations(regions: list, top_n: int = 8) -> dict:
    """
    Map brain regions to cognitive/behavioral functions.

    Primary path (when Neurosynth dataset is loaded):
      - Map region labels to MNI coordinates from ROI_COORDS
      - Find Neurosynth studies that activate within 10 mm of those coordinates
      - Count feature-term frequencies across those studies
      - Return the most common terms as cognitive associations

    Demo/offline fallback:
      - Curated region-function lookup table (fast, deterministic)

    Args:
        regions: List of brain region names (matched against ROI_COORDS keys)
        top_n: Number of top associations to return

    Returns:
        dict with cognitive_associations list and method field
    """
    dataset = _get_dataset()
    if dataset is not None:
        return _reverse_inference(regions, dataset, top_n)
    return _curated_cognitive_associations(regions, top_n)


def _reverse_inference(regions: list, dataset: dict, top_n: int) -> dict:
    """
    Neurosynth v7 reverse inference: studies activating near given ROIs →
    summed TF-IDF term weights → top cognitive terms.

    Methodology:
      1. For each region label, look up its MNI coordinate in ROI_COORDS.
      2. Find all activation rows within 10 mm.
      3. Collect the unique study IDs from those activations.
      4. Sum each study's TF-IDF feature vector across all relevant studies.
      5. Return the terms with the highest summed weights.
    """
    import numpy as np

    coord_arr       = dataset["coord_arr"]
    coord_study_ids = dataset["coord_study_ids"]
    study_id_to_idx = dataset["study_id_to_idx"]
    features        = dataset["features"]
    vocab           = dataset["vocabulary"]

    # Resolve region names → MNI coordinates
    query_coords = []
    for region in regions:
        key = region.lower().replace(" ", "_")
        if key in ROI_COORDS:
            query_coords.append(ROI_COORDS[key])
        else:
            for roi_key, roi_coord in ROI_COORDS.items():
                parts = [p for p in key.split("_") if len(p) > 3]
                if any(p in roi_key for p in parts):
                    query_coords.append(roi_coord)
                    break

    if not query_coords:
        return _curated_cognitive_associations(regions, top_n)

    # Find studies with activations within 10 mm of any query coordinate
    relevant_study_ids: set[str] = set()
    for rx, ry, rz in query_coords:
        dists = np.sqrt(np.sum((coord_arr - np.array([rx, ry, rz])) ** 2, axis=1))
        nearby = np.array(coord_study_ids)[dists <= 10.0]
        relevant_study_ids.update(nearby.tolist())

    if not relevant_study_ids:
        return _curated_cognitive_associations(regions, top_n)

    # Map study IDs to row indices in the features matrix
    row_indices = [study_id_to_idx[sid] for sid in relevant_study_ids if sid in study_id_to_idx]
    if not row_indices:
        return _curated_cognitive_associations(regions, top_n)

    # Sum TF-IDF weights across relevant studies
    import scipy.sparse
    subset = features[row_indices, :]
    if scipy.sparse.issparse(subset):
        term_scores = np.asarray(subset.sum(axis=0)).flatten()
    else:
        term_scores = subset.sum(axis=0)

    top_idx = np.argsort(term_scores)[::-1][:top_n]
    max_score = float(term_scores[top_idx[0]]) if len(top_idx) > 0 else 1.0

    return {
        "queried_regions": regions,
        "cognitive_associations": [
            {
                "function": vocab[i],
                "score": round(float(term_scores[i]) / max_score, 3),
                "frequency": int(term_scores[i]),
            }
            for i in top_idx
            if term_scores[i] > 0
        ],
        "method": "Neurosynth v7 reverse inference (TF-IDF weighted, coordinate-based)",
    }


def _curated_cognitive_associations(regions: list, top_n: int) -> dict:
    """
    Curated region-function lookup table — used when Neurosynth dataset is not
    loaded (demo / offline mode).
    """
    REGION_FUNCTION_MAP = {
        "hippocampus": ["episodic memory", "memory consolidation", "spatial navigation", "pattern separation"],
        "entorhinal": ["memory encoding", "grid cells", "spatial processing", "temporal lobe function"],
        "prefrontal": ["working memory", "cognitive control", "decision making", "executive function"],
        "dlpfc": ["working memory", "cognitive control", "executive function"],
        "anterior_cingulate": ["error monitoring", "cognitive control", "attention", "conflict detection"],
        "cingulate": ["error monitoring", "cognitive control", "attention"],
        "amygdala": ["fear processing", "emotional memory", "threat detection", "arousal"],
        "striatum": ["reward processing", "motor learning", "habit formation", "dopamine signaling"],
        "putamen": ["motor control", "habit learning", "reward"],
        "caudate": ["reward processing", "goal-directed behavior"],
        "thalamus": ["sensory relay", "attention gating", "arousal regulation", "consciousness"],
        "insula": ["interoception", "pain processing", "emotional awareness", "disgust"],
        "cerebellum": ["motor coordination", "procedural learning", "timing", "fine motor control"],
        "parietal": ["spatial attention", "numerical cognition", "somatosensation", "tool use"],
        "occipital": ["visual processing", "object recognition", "face perception", "motion detection"],
        "frontal": ["executive function", "working memory", "planning", "inhibition"],
        "temporal": ["language processing", "semantic memory", "auditory processing"],
        "limbic": ["emotion regulation", "memory", "motivation"],
    }

    from collections import Counter
    all_functions: list[str] = []
    for region in regions:
        region_lower = region.lower()
        for key, functions in REGION_FUNCTION_MAP.items():
            if key in region_lower:
                all_functions.extend(functions)

    counts = Counter(all_functions)
    top_functions = counts.most_common(top_n)

    return {
        "queried_regions": regions,
        "cognitive_associations": [
            {"function": f, "frequency": c} for f, c in top_functions
        ],
        "method": "curated region-function lookup table (offline demo fallback)",
    }


def _generate_disease_png(img, session_id: str, term: str) -> str:
    """Generate disease meta-analysis map as bar chart PNG."""
    parcellated = _parcellate_image_to_regions(img)
    return _generate_disease_png_from_parcellated(parcellated, session_id, term)


def _generate_disease_png_from_parcellated(
    parcellated: dict[str, float],
    session_id: str,
    term: str
) -> str:
    """Generate a bar chart PNG from a parcellated disease map."""
    output_dir = os.path.join(SESSIONS_DIR, session_id)
    os.makedirs(output_dir, exist_ok=True)
    output_path = os.path.join(output_dir, "disease.png")

    # Sort regions by value for bar chart
    sorted_regions = sorted(parcellated.items(), key=lambda x: x[1], reverse=True)[:15]
    regions = [r for r, _ in sorted_regions]
    values = np.array([v for _, v in sorted_regions])

    # Normalize for display
    if values.max() > 0:
        norm_values = values / values.max()
    else:
        norm_values = values

    fig, ax = plt.subplots(1, 1, figsize=(10, 6))

    colors = plt.cm.viridis(norm_values)
    ax.barh(range(len(regions)), norm_values, color=colors)
    ax.set_yticks(range(len(regions)))
    ax.set_yticklabels(regions, fontsize=9)
    ax.set_xlabel("Normalized meta-analytic activation", fontsize=10)
    ax.set_title(f"{term.capitalize()} — Disease Anatomy\n(Neurosynth meta-analysis)",
                 fontsize=12, fontweight='bold')
    ax.invert_yaxis()
    ax.set_xlim(0, 1.15)

    plt.tight_layout()
    plt.savefig(output_path, dpi=150, bbox_inches='tight', facecolor='white')
    plt.close('all')

    return os.path.abspath(output_path)


def _get_curated_disease_map(indication: str, term: str, session_id: str) -> dict | None:
    """
    Fall back to a curated ROI template when Neurosynth data is unavailable.

    This keeps the backend and frontend integrated in offline/dev environments
    without pretending that the result came from a true meta-analysis.
    """
    if term not in CURATED_DISEASE_PATTERNS:
        return None

    parcellated = CURATED_DISEASE_PATTERNS[term]
    image_path = _generate_disease_png_from_parcellated(parcellated, session_id, term)
    map_id = f"{session_id}_disease_{term}"

    from services.correlation_service import store_parcellated_map
    store_parcellated_map(map_id, parcellated)

    top_regions = sorted(parcellated.items(), key=lambda x: x[1], reverse=True)[:10]

    return {
        "indication": indication,
        "neurosynth_term": term,
        "map_id": map_id,
        "n_studies": 0,
        "top_regions": [{"region": r, "value": round(v, 4)} for r, v in top_regions],
        "image_path": image_path,
        "source": "Curated disease template (offline fallback)",
    }


def _parcellate_image_to_regions(img) -> dict:
    """Convert NIfTI stat map to dict of {roi_label: value} using MNI coordinates."""
    if img is None:
        return {r: 0.0 for r in ROI_COORDS}

    try:
        import nibabel as nib
        data = img.get_fdata()
        affine = img.affine
        inv_affine = np.linalg.inv(affine)

        result = {}
        for region, mni_coords in ROI_COORDS.items():
            vox = np.round(inv_affine @ [*mni_coords, 1]).astype(int)[:3]
            vox = np.clip(vox, 0, np.array(data.shape[:3]) - 1)
            try:
                val = float(data[vox[0], vox[1], vox[2]])
                result[region] = val if not np.isnan(val) else 0.0
            except (IndexError, ValueError):
                result[region] = 0.0
        return result
    except Exception:
        return {r: 0.0 for r in ROI_COORDS}


if __name__ == "__main__":
    result = get_disease_map("Alzheimer's disease", "test_session")
    print("Disease map term:", result.get("neurosynth_term"))
    print("N studies:", result.get("n_studies"))
    print("Top regions:", result.get("top_regions", [])[:3])
    if result.get("error"):
        print(f"Note: {result['error']} (expected if Neurosynth not preloaded)")
    else:
        assert result.get("map_id"), "Should return map_id"
    print("neurosynth_service TEST PASSED")

    # Test cognitive associations
    assoc = get_cognitive_associations(["hippocampus", "prefrontal cortex", "amygdala"])
    print("Cognitive associations:", assoc["cognitive_associations"][:3])
    assert assoc["cognitive_associations"], "Should return associations"
    print("get_cognitive_associations TEST PASSED")
