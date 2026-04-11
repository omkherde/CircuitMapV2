"""
scripts/preload_ahba.py — Download Allen Human Brain Atlas microarray data.

CRITICAL: Run on home WiFi. Takes ~15 minutes, ~500MB.
Run BEFORE the hackathon:
    cd backend
    python scripts/preload_ahba.py
"""
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from dotenv import load_dotenv
load_dotenv()

import abagen

DATA_DIR = os.getenv("AHBA_DATA_DIR", "./cache/ahba_data")
os.makedirs(DATA_DIR, exist_ok=True)

print(f"AHBA data directory: {os.path.abspath(DATA_DIR)}")
print("Starting AHBA download (~500MB)...")

try:
    files = abagen.fetch_microarray(
        data_dir=DATA_DIR,
        donors='all',
        verbose=1
    )
    print(f"SUCCESS: Downloaded {len(files) if hasattr(files, '__len__') else 'all'} files")
except Exception as e:
    print(f"Full donor download failed: {e}")
    print("Trying fallback: 2 donors only (sufficient for demo)...")
    try:
        files = abagen.fetch_microarray(
            data_dir=DATA_DIR,
            donors=['9861', '10021'],
            verbose=1
        )
        print(f"Fallback SUCCESS: Downloaded 2-donor dataset")
    except Exception as e2:
        print(f"FAILED: {e2}")
        sys.exit(1)

# Verify data loads correctly
print("\nVerifying data loads...")
try:
    expression = abagen.get_expression_data(
        atlas=None,
        data_dir=DATA_DIR,
        return_donors=False,
        verbose=0
    )
    print(f"Expression matrix shape: {expression.shape}")
    demo_genes = ['SUV39H1', 'COMT', 'HDAC2']
    for gene in demo_genes:
        found = gene in expression.columns
        print(f"  {gene}: {'FOUND' if found else 'NOT FOUND'}")
    print("\nAHBA preload COMPLETE")
except Exception as e:
    print(f"Verification failed: {e}")
    print("Data downloaded but verification failed — check abagen version compatibility")
    sys.exit(1)
