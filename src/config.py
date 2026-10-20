"""Central configuration: folder paths and the weights used by the Viral Coefficient."""
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
RAW = ROOT / "data" / "raw"
PROCESSED = ROOT / "data" / "processed"
REPORTS = ROOT / "reports"
MODELS = ROOT / "models"
DB_PATH = ROOT / "data" / "engagement.db"

for p in (RAW, PROCESSED, REPORTS, MODELS):
    p.mkdir(parents=True, exist_ok=True)

# ---- Viral Coefficient weights (Module 2) ----
# High-value actions (shares, saves) are weighted far above passive actions (likes).
VIRAL_WEIGHTS = {"shares": 5.0, "saves": 3.0, "comments": 1.5, "likes": 0.5}

RANDOM_SEED = 42
