"""
scripts/preload_neurosynth.py — Download Neurosynth v7 dataset.

Neurosynth restructured to a new format in 2019; the old database.txt /
features.txt files no longer exist. This script downloads the v7 files:

  coordinates.tsv     — MNI activation coordinates per study
  metadata.tsv        — study metadata (PMID, year, journal, ...)
  features.npz        — sparse TF-IDF term-weight matrix (studies × vocab)
  vocabulary.txt      — term at each column index of features.npz

Run from backend/:
    python scripts/preload_neurosynth.py
"""
import gzip
import os
import pickle
import shutil
import sys
import urllib.request

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from dotenv import load_dotenv
load_dotenv()

DATA_DIR = os.getenv("NEUROSYNTH_DATA_DIR", "./cache/neurosynth_data")
os.makedirs(DATA_DIR, exist_ok=True)
print(f"Neurosynth data directory: {os.path.abspath(DATA_DIR)}")

BASE = "https://raw.githubusercontent.com/neurosynth/neurosynth-data/master"
FILES = {
    "coordinates.tsv.gz": f"{BASE}/data-neurosynth_version-7_coordinates.tsv.gz",
    "metadata.tsv.gz":    f"{BASE}/data-neurosynth_version-7_metadata.tsv.gz",
    "features.npz":       f"{BASE}/data-neurosynth_version-7_vocab-terms_source-abstract_type-tfidf_features.npz",
    "vocabulary.txt":     f"{BASE}/data-neurosynth_version-7_vocab-terms_vocabulary.txt",
}


def download(url: str, dest: str) -> bool:
    print(f"  GET {url}")
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
        with urllib.request.urlopen(req, timeout=180) as resp, open(dest, "wb") as fh:
            total = int(resp.headers.get("Content-Length", 0))
            downloaded = 0
            while chunk := resp.read(65536):
                fh.write(chunk)
                downloaded += len(chunk)
                if total:
                    print(f"  {downloaded:,}/{total:,} ({100*downloaded//total}%)", end="\r")
        print()
        return True
    except Exception as exc:
        print(f"  FAILED: {exc}")
        return False


# ── Download files ──────────────────────────────────────────────────────────

print("\nStep 1: Downloading Neurosynth v7 data files...")
for filename, url in FILES.items():
    dest_gz  = os.path.join(DATA_DIR, filename)
    dest_txt = dest_gz.replace(".gz", "") if filename.endswith(".gz") else dest_gz

    if os.path.exists(dest_txt) and os.path.getsize(dest_txt) > 1000:
        print(f"  {filename}: already present, skipping")
        continue

    if not download(url, dest_gz):
        print(f"\nERROR: could not download {filename}. Check internet connection.")
        sys.exit(1)

    if filename.endswith(".gz"):
        print(f"  Decompressing {filename}...")
        with gzip.open(dest_gz, "rb") as fin, open(dest_txt, "wb") as fout:
            shutil.copyfileobj(fin, fout)
        os.remove(dest_gz)
        print(f"  → {dest_txt} ({os.path.getsize(dest_txt):,} bytes)")

# ── Build and pickle the dataset ────────────────────────────────────────────

print("\nStep 2: Building dataset index...")

import numpy as np
import pandas as pd
import scipy.sparse

coords_path   = os.path.join(DATA_DIR, "coordinates.tsv")
metadata_path = os.path.join(DATA_DIR, "metadata.tsv")
features_path = os.path.join(DATA_DIR, "features.npz")
vocab_path    = os.path.join(DATA_DIR, "vocabulary.txt")

print("  Loading coordinates...")
coords_df = pd.read_csv(coords_path, sep="\t")
# Normalise column names — v7 uses 'id', 'x', 'y', 'z'
coords_df.columns = [c.lower() for c in coords_df.columns]
if "space" in coords_df.columns:
    # Keep only MNI-space coordinates
    coords_df = coords_df[coords_df["space"].str.upper() == "MNI"].copy()
print(f"  Coordinates: {len(coords_df):,} activations")

print("  Loading metadata...")
meta_df = pd.read_csv(metadata_path, sep="\t")
meta_df.columns = [c.lower() for c in meta_df.columns]
# Canonical study-id column name across Neurosynth v7 variants
id_col = next((c for c in meta_df.columns if c in ("id", "pmid", "study_id")), meta_df.columns[0])
study_ids = meta_df[id_col].astype(str).tolist()
study_id_to_idx = {sid: i for i, sid in enumerate(study_ids)}
print(f"  Studies: {len(study_ids):,}")

print("  Loading features matrix...")
features = scipy.sparse.load_npz(features_path)
print(f"  Features matrix: {features.shape} (studies × terms)")

print("  Loading vocabulary...")
with open(vocab_path) as fh:
    vocabulary = [line.strip() for line in fh if line.strip()]
print(f"  Vocabulary: {len(vocabulary):,} terms")

# Ensure shapes align
assert features.shape[0] == len(study_ids), (
    f"Feature rows ({features.shape[0]}) != study count ({len(study_ids)})"
)
assert features.shape[1] == len(vocabulary), (
    f"Feature cols ({features.shape[1]}) != vocab size ({len(vocabulary)})"
)

dataset = {
    "coords":          coords_df,
    "features":        features,
    "vocabulary":      vocabulary,
    "study_ids":       study_ids,
    "study_id_to_idx": study_id_to_idx,
}

pkl_path = os.path.join(DATA_DIR, "dataset.pkl")
print(f"\n  Saving to {pkl_path} ...")
with open(pkl_path, "wb") as fh:
    pickle.dump(dataset, fh, protocol=4)
print(f"  Saved ({os.path.getsize(pkl_path):,} bytes)")

# ── Quick verification ───────────────────────────────────────────────────────

print("\nStep 3: Verification — activations near hippocampus (-24, -20, -18):")
rx, ry, rz = -24.0, -20.0, -18.0
coord_arr = coords_df[["x", "y", "z"]].values.astype(float)
dists = np.sqrt(np.sum((coord_arr - [rx, ry, rz]) ** 2, axis=1))
nearby = coords_df.iloc[dists <= 10]
print(f"  {len(nearby):,} activations within 10 mm of hippocampus_L")

print("\nNeurosynth v7 preload COMPLETE")
