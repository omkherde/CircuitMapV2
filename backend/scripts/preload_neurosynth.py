"""
scripts/preload_neurosynth.py — Download Neurosynth 0.3.x database.

neurosynth.utils.download() does not exist in v0.3.7. This script
downloads database.txt.gz and features.txt.gz directly from the
neurosynth-data GitHub repository and builds the Dataset pickle.

Run from backend/:
    python scripts/preload_neurosynth.py
"""
import os
import sys
import gzip
import shutil
import urllib.request

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from dotenv import load_dotenv
load_dotenv()

DATA_DIR = os.getenv("NEUROSYNTH_DATA_DIR", "./cache/neurosynth_data")
os.makedirs(DATA_DIR, exist_ok=True)

print(f"Neurosynth data directory: {os.path.abspath(DATA_DIR)}")

# neurosynth-data GitHub repository — these files are compatible with 0.3.x
BASE_URL = "https://github.com/neurosynth/neurosynth-data/raw/master/current_data.tar.gz"
FALLBACK_FILES = {
    "database.txt.gz": [
        "https://github.com/neurosynth/neurosynth-data/raw/master/data/database.txt.gz",
        "https://raw.githubusercontent.com/neurosynth/neurosynth-data/master/data/database.txt.gz",
    ],
    "features.txt.gz": [
        "https://github.com/neurosynth/neurosynth-data/raw/master/data/features.txt.gz",
        "https://raw.githubusercontent.com/neurosynth/neurosynth-data/master/data/features.txt.gz",
    ],
}

db_path = os.path.join(DATA_DIR, "database.txt")
feat_path = os.path.join(DATA_DIR, "features.txt")


def download_file(url: str, dest: str) -> bool:
    """Download url to dest. Returns True on success."""
    print(f"  Downloading from: {url}")
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
        with urllib.request.urlopen(req, timeout=120) as resp, open(dest, 'wb') as f:
            total = int(resp.headers.get('Content-Length', 0))
            downloaded = 0
            chunk = 65536
            while True:
                data = resp.read(chunk)
                if not data:
                    break
                f.write(data)
                downloaded += len(data)
                if total:
                    pct = downloaded / total * 100
                    print(f"  {downloaded:,} / {total:,} bytes ({pct:.0f}%)", end='\r')
        print()
        return True
    except Exception as e:
        print(f"  Failed: {e}")
        return False


def try_download_via_tarball() -> bool:
    """Try downloading the combined tarball."""
    dest_tar = os.path.join(DATA_DIR, "current_data.tar.gz")
    print("Trying combined tarball download...")
    if not download_file(BASE_URL, dest_tar):
        return False
    try:
        import tarfile
        print("Extracting tarball...")
        with tarfile.open(dest_tar) as tf:
            tf.extractall(DATA_DIR)
        # Locate extracted files
        for root, _, files in os.walk(DATA_DIR):
            for fname in files:
                fpath = os.path.join(root, fname)
                if fname == "database.txt" and not os.path.exists(db_path):
                    shutil.copy(fpath, db_path)
                elif fname == "features.txt" and not os.path.exists(feat_path):
                    shutil.copy(fpath, feat_path)
        return os.path.exists(db_path) and os.path.exists(feat_path)
    except Exception as e:
        print(f"Tarball extraction failed: {e}")
        return False


def download_individual_files() -> bool:
    """Download and unpack database.txt.gz and features.txt.gz individually."""
    for gz_name, urls in FALLBACK_FILES.items():
        target_txt = os.path.join(DATA_DIR, gz_name.replace(".gz", ""))
        if os.path.exists(target_txt) and os.path.getsize(target_txt) > 10_000:
            print(f"  {gz_name}: already present, skipping")
            continue

        gz_path = os.path.join(DATA_DIR, gz_name)
        success = False
        for url in urls:
            if download_file(url, gz_path):
                success = True
                break

        if not success:
            print(f"  ERROR: Could not download {gz_name}")
            return False

        # Decompress
        print(f"  Decompressing {gz_name}...")
        try:
            with gzip.open(gz_path, 'rb') as f_in, open(target_txt, 'wb') as f_out:
                shutil.copyfileobj(f_in, f_out)
            os.remove(gz_path)
            print(f"  {target_txt}: {os.path.getsize(target_txt):,} bytes")
        except Exception as e:
            print(f"  Decompression failed: {e}")
            return False

    return os.path.exists(db_path) and os.path.exists(feat_path)


# Step 1: Download data files
print("\nStep 1: Downloading Neurosynth database files...")

if os.path.exists(db_path) and os.path.getsize(db_path) > 10_000 \
        and os.path.exists(feat_path) and os.path.getsize(feat_path) > 10_000:
    print("  Data files already present.")
else:
    ok = download_individual_files()
    if not ok:
        ok = try_download_via_tarball()
    if not ok:
        print("\nERROR: Could not download Neurosynth data.")
        print("Manual fallback: download database.txt and features.txt from")
        print("  https://github.com/neurosynth/neurosynth-data/tree/master/data")
        print(f"and place them in: {os.path.abspath(DATA_DIR)}")
        sys.exit(1)

print(f"  database.txt: {os.path.getsize(db_path):,} bytes")
print(f"  features.txt: {os.path.getsize(feat_path):,} bytes")

# Step 2: Build and save Dataset
print("\nStep 2: Building Neurosynth Dataset (this takes a few minutes)...")
try:
    from neurosynth.base.dataset import Dataset
    dataset = Dataset(db_path, feat_path)

    pkl_path = os.path.join(DATA_DIR, "dataset.pkl")
    dataset.save(pkl_path)
    print(f"  Dataset saved to: {pkl_path}")

    # Verify key terms
    print("\nStep 3: Verifying key terms:")
    for term in ['alzheimer', 'schizophrenia', 'depression', 'parkinson']:
        try:
            studies = dataset.get_studies(features=term, frequency_threshold=0.001)
            print(f"  '{term}': {len(studies)} studies")
        except Exception as e:
            print(f"  '{term}': ERROR - {e}")

    print("\nNeurosynth preload COMPLETE")
except Exception as e:
    print(f"Dataset build failed: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)
