"""
correlation_service.py — Spatial Pearson correlation between two parcellated brain maps.

Computes correlation + 1000-permutation null distribution (seed=42).
"""
import numpy as np
from scipy import stats
from typing import Optional

# Module-level map store — shared between ahba_service and neurosynth_service
_map_store: dict[str, dict[str, float]] = {}


def store_parcellated_map(map_id: str, values: dict[str, float]) -> None:
    """Store a parcellated brain map by ID for later correlation."""
    _map_store[map_id] = values


def get_parcellated_map(map_id: str) -> Optional[dict[str, float]]:
    """Retrieve a stored parcellated map by ID."""
    return _map_store.get(map_id)


def compute_overlap(map1_id: str, map2_id: str, label: str) -> dict:
    """
    Compute spatial Pearson correlation between two stored brain maps.

    Args:
        map1_id: ID of expression map (from get_brain_expression)
        map2_id: ID of disease map (from get_disease_map)
        label: Human-readable label for this comparison

    Returns:
        dict with r, p_value, percentile, interpretation, etc.
    """
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
            "r": 0.0,
            "percentile": 50
        }

    vec1 = np.array([map1[r] for r in common], dtype=float)
    vec2 = np.array([map2[r] for r in common], dtype=float)

    # Handle NaN
    vec1 = np.nan_to_num(vec1, nan=0.0)
    vec2 = np.nan_to_num(vec2, nan=0.0)

    # Handle zero variance
    if vec1.std() < 1e-10 or vec2.std() < 1e-10:
        return {
            "r": 0.0,
            "p_value": 1.0,
            "percentile": 50,
            "label": label,
            "interpretation": "weak",
            "null_mean": 0.0,
            "null_std": 0.0,
            "n_regions": len(common),
            "note": "Near-zero variance in one map — insufficient data"
        }

    r_obs, p_obs = stats.pearsonr(vec1, vec2)

    # Null distribution via permutation (seed=42 for reproducibility)
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


if __name__ == "__main__":
    store_parcellated_map("test_map1", {
        "hippocampus_L": 0.9, "hippocampus_R": 0.8,
        "amygdala_L": 0.3, "amygdala_R": 0.2,
        "prefrontal_dlPFC_L": 0.7, "prefrontal_dlPFC_R": 0.6,
        "striatum_L": 0.1, "striatum_R": 0.1,
        "thalamus_L": 0.4, "thalamus_R": 0.4,
        "cerebellum_L": 0.05, "cerebellum_R": 0.05,
        "entorhinal_L": 0.85, "entorhinal_R": 0.82,
        "anterior_cingulate": 0.65, "insula_L": 0.5,
        "insula_R": 0.48, "occipital_L": 0.2,
        "occipital_R": 0.22, "parietal": 0.35
    })
    store_parcellated_map("test_map2", {
        "hippocampus_L": 0.85, "hippocampus_R": 0.75,
        "amygdala_L": 0.25, "amygdala_R": 0.15,
        "prefrontal_dlPFC_L": 0.65, "prefrontal_dlPFC_R": 0.55,
        "striatum_L": 0.12, "striatum_R": 0.11,
        "thalamus_L": 0.42, "thalamus_R": 0.38,
        "cerebellum_L": 0.08, "cerebellum_R": 0.06,
        "entorhinal_L": 0.80, "entorhinal_R": 0.78,
        "anterior_cingulate": 0.60, "insula_L": 0.45,
        "insula_R": 0.43, "occipital_L": 0.18,
        "occipital_R": 0.20, "parietal": 0.30
    })
    result = compute_overlap("test_map1", "test_map2", "test overlap")
    print(f"r={result['r']}, percentile={result['percentile']}")
    assert result['r'] > 0.9, f"Correlated maps should have high r, got {result['r']}"
    print("correlation_service TEST PASSED")
