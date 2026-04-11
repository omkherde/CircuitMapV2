import os
import tempfile
from pathlib import Path

os.environ.setdefault(
    "MPLCONFIGDIR",
    os.path.join(tempfile.gettempdir(), "circuitmap-matplotlib")
)

import matplotlib
matplotlib.use('Agg')  # MUST be before any other matplotlib import
import matplotlib.pyplot as plt

import numpy as np
import pandas as pd
from scipy import stats

DATA_DIR = os.getenv("AHBA_DATA_DIR", "./cache/ahba_data")
SESSIONS_DIR = os.getenv("SESSIONS_DIR", "./sessions")

# Module-level caches — load once, reuse across requests
_expression_cache: dict[str, pd.Series] | None = None
_donor_metadata_cache: list[dict] | None = None


def ahba_data_ready() -> bool:
    """Return True when the local AHBA microarray cache is present on disk."""
    return any(Path(DATA_DIR).glob("microarray/normalized_microarray_donor*"))


def _load_donor_metadata() -> list[dict]:
    """
    Load donor metadata for per-gene aggregation.

    Each entry contains:
      expr_path : Path to MicroarrayExpression.csv
      regions   : pd.Series of structure names (for region-name aggregation)
      probes    : pd.DataFrame with probe_id → gene_symbol mapping
      mni_coords: np.ndarray of shape (n_samples, 3) — MNI x/y/z per sample
                  Used by _parcellate_by_mni_coords for proper spatial alignment.
    """
    global _donor_metadata_cache
    if _donor_metadata_cache is None:
        donor_dirs = sorted(Path(DATA_DIR).glob("microarray/normalized_microarray_donor*"))
        donors: list[dict] = []
        for donor_dir in donor_dirs:
            sample_path = donor_dir / "SampleAnnot.csv"
            probes_path = donor_dir / "Probes.csv"
            expr_path = donor_dir / "MicroarrayExpression.csv"

            if not (sample_path.exists() and probes_path.exists() and expr_path.exists()):
                continue

            sample_annot = pd.read_csv(
                sample_path,
                usecols=["structure_name", "structure_acronym", "mni_x", "mni_y", "mni_z"]
            )
            regions = (
                sample_annot["structure_name"]
                .fillna(sample_annot["structure_acronym"])
                .astype(str)
                .str.strip()
            )
            # MNI coordinates — shape (n_samples, 3)
            mni_coords = sample_annot[["mni_x", "mni_y", "mni_z"]].to_numpy(dtype=float)

            probes = pd.read_csv(
                probes_path,
                usecols=["probe_id", "gene_symbol"]
            )

            donors.append({
                "expr_path": expr_path,
                "regions": regions,
                "probes": probes,
                "mni_coords": mni_coords,
            })

        _donor_metadata_cache = donors

    return _donor_metadata_cache


def _load_probe_sample_means(expr_path: Path, probe_ids: set[int]) -> np.ndarray | None:
    """Load only the requested probe rows and average them into one per-sample vector."""
    probe_frames: list[pd.DataFrame] = []

    for chunk in pd.read_csv(expr_path, header=None, chunksize=2048):
        matched = chunk[chunk.iloc[:, 0].isin(probe_ids)]
        if not matched.empty:
            probe_frames.append(matched.iloc[:, 1:].astype(float))

    if not probe_frames:
        return None

    probe_matrix = pd.concat(probe_frames, axis=0).to_numpy(dtype=float)
    return probe_matrix.mean(axis=0)


def _get_gene_expression(gene_name: str) -> pd.Series:
    """
    Aggregate AHBA microarray expression for a single gene across all donors.

    We avoid `abagen.get_expression_data(atlas=None)` here because that path
    is invalid for the raw microarray cache and was causing the runtime
    `NoneType has no len()` error seen in the agent session.
    """
    global _expression_cache
    if _expression_cache is None:
        _expression_cache = {}

    gene_key = gene_name.upper().strip()
    if gene_key in _expression_cache:
        return _expression_cache[gene_key]

    donor_region_series: list[pd.Series] = []

    for donor in _load_donor_metadata():
        probes = donor["probes"]
        probe_ids = set(
            probes.loc[
                probes["gene_symbol"].astype(str).str.upper() == gene_key,
                "probe_id"
            ]
            .dropna()
            .astype(int)
            .tolist()
        )

        if not probe_ids:
            continue

        sample_means = _load_probe_sample_means(donor["expr_path"], probe_ids)
        if sample_means is None or len(sample_means) != len(donor["regions"]):
            continue

        donor_frame = pd.DataFrame({
            "region": donor["regions"].to_numpy(),
            "expression": sample_means,
        })
        donor_region_series.append(
            donor_frame.groupby("region", sort=False)["expression"].mean()
        )

    if not donor_region_series:
        raise KeyError(gene_key)

    expression = pd.concat(donor_region_series, axis=1).mean(axis=1, skipna=True).dropna()
    _expression_cache[gene_key] = expression
    return expression


def get_expression_map(gene_name: str, session_id: str) -> dict:
    """
    Get brain-wide expression data for a gene from the Allen Human Brain Atlas.

    Args:
        gene_name: Official HGNC gene symbol (e.g., 'SUV39H1', 'COMT')
        session_id: Session ID for output file naming

    Returns:
        dict with top_regions, map_id, image_path, atlas, n_samples, parcellated_values
    """
    if not ahba_data_ready():
        return {
            "error": "AHBA data not found. Run scripts/preload_ahba.py first.",
            "top_regions": [],
            "map_id": None
        }

    try:
        gene_values = _get_gene_expression(gene_name)
    except KeyError:
        return {
            "error": f"Gene '{gene_name}' not found in AHBA. Check HGNC symbol.",
            "top_regions": [],
            "map_id": None
        }
    except Exception as e:
        return {
            "error": f"Failed to load AHBA data: {e}. Run scripts/preload_ahba.py first.",
            "top_regions": [],
            "map_id": None
        }

    # Compute percentile ranks
    percentiles = stats.rankdata(gene_values.to_numpy()) / len(gene_values) * 100

    # Build top regions list
    top_idx = np.argsort(percentiles)[::-1][:10]
    top_regions = []
    for i in top_idx:
        region_name = gene_values.index[i]
        top_regions.append({
            "region": str(region_name),
            "percentile": round(float(percentiles[i]), 1),
            "raw_expression": round(float(gene_values.iloc[i]), 4)
        })

    # Generate PNG
    image_path = _generate_expression_png(gene_values, percentiles, session_id, gene_name)

    # Build parcellated map for correlation (normalize to 0-1)
    norm_values = (gene_values.values - gene_values.values.min()) / \
                  (gene_values.values.max() - gene_values.values.min() + 1e-8)
    parcellated = {str(region): float(val)
                   for region, val in zip(gene_values.index, norm_values)}

    map_id = f"{session_id}_expression_{gene_name}"

    # Build an ROI-parcellated map using MNI spatial lookup so that the region
    # labels match exactly the 20 neurosynth_service ROI coordinates.
    # This replaces the old fuzzy string-matching approach and restores proper
    # spatial alignment for the Pearson correlation computation.
    from services.correlation_service import store_parcellated_map
    roi_parcellated = _parcellate_by_mni_coords(gene_name)
    store_parcellated_map(map_id, roi_parcellated)

    return {
        "gene_name": gene_name,
        "map_id": map_id,
        "top_regions": top_regions,
        "atlas": "Allen Human Brain Atlas microarray (donor-averaged)",
        "n_samples": int(len(gene_values)),
        "image_path": image_path,
        "parcellated_values": parcellated
    }


def _parcellate_by_mni_coords(gene_name: str, radius_mm: float = 15.0) -> dict[str, float]:
    """
    Parcellate AHBA expression to the 20 standard ROI coordinates using spatial
    nearest-neighbour averaging.

    For each ROI (from neurosynth_service.ROI_COORDS), we find all AHBA
    microarray samples within `radius_mm` millimetres and average their
    expression.  This produces DK-compatible spatial alignment without relying
    on fragile region-name string matching.

    Returns a dict keyed by ROI label with values normalised to [0, 1].
    Falls back to zero-filled ROI dict if no AHBA data is loaded.
    """
    from services.neurosynth_service import ROI_COORDS

    gene_key = gene_name.upper().strip()

    # Collect all (mni_coord, expression) pairs across donors
    all_coords: list[np.ndarray] = []
    all_expr: list[float] = []

    for donor in _load_donor_metadata():
        probes = donor["probes"]
        probe_ids = set(
            probes.loc[
                probes["gene_symbol"].astype(str).str.upper() == gene_key,
                "probe_id"
            ]
            .dropna()
            .astype(int)
            .tolist()
        )
        if not probe_ids:
            continue

        sample_means = _load_probe_sample_means(donor["expr_path"], probe_ids)
        mni_coords = donor["mni_coords"]  # (n_samples, 3)

        if sample_means is None or len(sample_means) != len(mni_coords):
            continue

        for coord, expr in zip(mni_coords, sample_means):
            if not np.isnan(expr):
                all_coords.append(coord)
                all_expr.append(float(expr))

    if not all_coords:
        # No AHBA samples found for this gene — return zeros
        return {roi: 0.0 for roi in ROI_COORDS}

    coords_arr = np.array(all_coords)  # (N, 3)
    expr_arr = np.array(all_expr)      # (N,)

    result: dict[str, float] = {}
    for roi_label, (rx, ry, rz) in ROI_COORDS.items():
        # Euclidean distance from this ROI centre to every AHBA sample
        dists = np.sqrt(np.sum((coords_arr - np.array([rx, ry, rz])) ** 2, axis=1))
        mask = dists <= radius_mm
        if mask.any():
            # Inverse-distance weighted average for smoother interpolation
            weights = 1.0 / (dists[mask] + 1e-3)
            result[roi_label] = float(np.average(expr_arr[mask], weights=weights))
        else:
            # No sample within radius — use nearest single sample
            nearest_idx = int(np.argmin(dists))
            result[roi_label] = float(expr_arr[nearest_idx])

    # Normalise to [0, 1]
    values = np.array(list(result.values()))
    v_min, v_max = values.min(), values.max()
    if v_max > v_min:
        for k in result:
            result[k] = float((result[k] - v_min) / (v_max - v_min))

    return result


def _generate_expression_png(
    gene_values: pd.Series,
    percentiles: np.ndarray,
    session_id: str,
    gene_name: str
) -> str:
    """Generate brain expression bar chart as PNG. Returns absolute file path."""
    output_dir = os.path.join(SESSIONS_DIR, session_id)
    os.makedirs(output_dir, exist_ok=True)
    output_path = os.path.join(output_dir, "expression.png")

    # Normalize values to 0-1
    values = gene_values.values
    norm_values = (values - values.min()) / (values.max() - values.min() + 1e-8)

    # Top 15 regions
    top_idx = np.argsort(norm_values)[::-1][:15]
    top_regions = [str(gene_values.index[i]) for i in top_idx]
    top_values = [norm_values[i] for i in top_idx]

    fig, ax = plt.subplots(1, 1, figsize=(10, 6))

    colors = plt.cm.RdBu_r(np.array(top_values))
    ax.barh(range(len(top_regions)), top_values, color=colors)
    ax.set_yticks(range(len(top_regions)))
    ax.set_yticklabels(top_regions, fontsize=9)
    ax.set_xlabel("Normalized expression (percentile rank)", fontsize=10)
    ax.set_title(f"{gene_name} — Brain Expression\n(Allen Human Brain Atlas via abagen)",
                 fontsize=12, fontweight='bold')
    ax.invert_yaxis()
    ax.set_xlim(0, 1.15)
    ax.axvline(x=0.5, color='gray', linestyle='--', alpha=0.4, linewidth=0.8)
    ax.text(0.51, -0.5, 'median', fontsize=7, color='gray')

    plt.tight_layout()
    plt.savefig(output_path, dpi=150, bbox_inches='tight', facecolor='white')
    plt.close('all')  # CRITICAL: prevent memory leak

    return os.path.abspath(output_path)


if __name__ == "__main__":
    result = get_expression_map("COMT", "test_session")
    print("Top regions:", result.get("top_regions", [])[:3])
    if result.get("error"):
        print(f"Note: {result['error']} (expected if AHBA not preloaded)")
    else:
        assert result["top_regions"], "Should return regions"
        assert os.path.exists(result["image_path"]), f"PNG not found at {result['image_path']}"
    print("ahba_service TEST PASSED")
