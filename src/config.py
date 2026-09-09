from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / 'data'
RAW = DATA / 'raw' / 'twcs.csv'
PROCESSED = DATA / 'processed'
GOLDEN = DATA / 'golden' / 'golden_set.csv'
RESULTS = ROOT / 'results'
RESULTS.mkdir(parents=True, exist_ok=True)
PROCESSED.mkdir(parents=True, exist_ok=True)
