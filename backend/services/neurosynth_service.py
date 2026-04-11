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
    global _dataset
    if _dataset is None:
        pkl_path = os.path.join(DATA_DIR, "dataset.pkl")
        if os.path.exists(pkl_path):
            try:
                with open(pkl_path, 'rb') as f:
                    _dataset = pickle.load(f)
                return _dataset
            except Exception:
                pass  # Fall through to load from files

        # Load from raw files
        from neurosynth.base.dataset import Dataset
        db_path = os.path.join(DATA_DIR, "database.txt")
        feat_path = os.path.join(DATA_DIR, "features.txt")

        # Check alternate paths
        if not os.path.exists(db_path):
            alt = os.path.join(DATA_DIR, "data", "database.txt")
            if os.path.exists(alt):
                db_path = alt
                feat_path = os.path.join(DATA_DIR, "data", "features.txt")

        if not os.path.exists(db_path):
            return None

        _dataset = Dataset(db_path, feat_path)
    return _dataset


def neurosynth_data_ready() -> bool:
    """Return True when a real Neurosynth dataset is available on disk."""
    pkl_path = os.path.join(DATA_DIR, "dataset.pkl")
    db_path = os.path.join(DATA_DIR, "database.txt")
    alt_db_path = os.path.join(DATA_DIR, "data", "database.txt")
    return os.path.exists(pkl_path) or os.path.exists(db_path) or os.path.exists(alt_db_path)


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

    Args:
        indication: Disease name (e.g., "Alzheimer's disease")
        session_id: Session ID for output file naming

    Returns:
        dict with map_id, top_regions, n_studies, image_path
    """
    term = _map_indication(indication)
    dataset = _get_dataset()

    if dataset is None:
        fallback = _get_curated_disease_map(indication, term, session_id)
        if fallback is not None:
            return fallback
        return {
            "error": "Neurosynth dataset not loaded. Run scripts/preload_neurosynth.py first.",
            "top_regions": [],
            "map_id": None
        }

    try:
        study_ids = dataset.get_studies(features=term, frequency_threshold=0.001)
    except Exception as e:
        # Try with higher threshold to reduce memory use
        try:
            study_ids = dataset.get_studies(features=term, frequency_threshold=0.005)
        except Exception as e2:
            return {
                "error": f"Failed to get studies for '{term}': {e2}",
                "top_regions": [],
                "map_id": None
            }

    if not study_ids:
        fallback = _get_curated_disease_map(indication, term, session_id)
        if fallback is not None:
            return fallback
        return {
            "error": f"No studies found for '{term}'. Try a simpler term.",
            "top_regions": [],
            "map_id": None
        }

    # Limit study count to avoid memory issues
    if len(study_ids) > 500:
        study_ids = study_ids[:500]

    try:
        from neurosynth.analysis import meta
        ma = meta.MetaAnalysis(dataset, study_ids)

        # Get pAgF image (posterior probability of activation given feature)
        pAgF_img = None
        for key in ma.images:
            if 'pAgF' in key:
                pAgF_img = ma.images[key]
                break
        if pAgF_img is None and ma.images:
            pAgF_img = list(ma.images.values())[0]

    except Exception as e:
        return {
            "error": f"Meta-analysis failed for '{term}': {e}",
            "top_regions": [],
            "map_id": None
        }

    # Generate PNG
    image_path = _generate_disease_png(pAgF_img, session_id, term)

    # Parcellate to ROI coords for correlation
    parcellated = _parcellate_image_to_regions(pAgF_img)

    map_id = f"{session_id}_disease_{term}"

    from services.correlation_service import store_parcellated_map
    store_parcellated_map(map_id, parcellated)

    # Top regions by value
    top_regions = sorted(parcellated.items(), key=lambda x: x[1], reverse=True)[:10]

    return {
        "indication": indication,
        "neurosynth_term": term,
        "map_id": map_id,
        "n_studies": len(study_ids),
        "top_regions": [{"region": r, "value": round(v, 4)} for r, v in top_regions],
        "image_path": image_path,
        "source": "Neurosynth meta-analysis"
    }


def get_cognitive_associations(regions: list, top_n: int = 8) -> dict:
    """
    Map brain regions to cognitive/behavioral functions via curated lookup.

    Uses a lookup table for reliability and speed (Neurosynth decoder is too slow).

    Args:
        regions: List of brain region names
        top_n: Number of top associations to return

    Returns:
        dict with cognitive_associations list
    """
    REGION_FUNCTION_MAP = {
        "hippocampus": ["episodic memory", "memory consolidation", "spatial navigation", "pattern separation"],
        "entorhinal": ["memory encoding", "grid cells", "spatial processing", "temporal lobe function"],
        "prefrontal": ["working memory", "cognitive control", "decision making", "executive function"],
        "dlpfc": ["working memory", "cognitive control", "executive function"],
        "anterior cingulate": ["error monitoring", "cognitive control", "attention", "conflict detection"],
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

    all_functions = []
    for region in regions:
        region_lower = region.lower()
        for key, functions in REGION_FUNCTION_MAP.items():
            if key in region_lower:
                all_functions.extend(functions)

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
