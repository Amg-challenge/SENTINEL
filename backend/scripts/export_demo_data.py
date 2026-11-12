"""Pre-compute the demo data: the API serves it fast, the front-end keeps it as fallback.

Run from the backend/ folder after any change to the engine or the scenarios:
    python scripts/export_demo_data.py

Writes:
    backend/data/demo.json                      read by the API at start-up (no 10 s calibration)
    frontend/public/demo-fallback.json          used by the front-end if the API is unreachable
"""
import json
import os
import sys
from pathlib import Path

BACKEND = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BACKEND))

from api import service  # noqa: E402

service.DATA_FILE = BACKEND / "data" / "__none__.json"   # force a fresh calibration
service.stats.cache_clear()
bundle = service.demo_bundle()

targets = [BACKEND / "data" / "demo.json", BACKEND.parent / "frontend" / "public" / "demo-fallback.json"]
for path in targets:
    os.makedirs(path.parent, exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(bundle, f, ensure_ascii=False, indent=2)
    print("wrote", path.relative_to(BACKEND.parent))
print("threshold", bundle["stats"]["threshold"], "· scenarios", len(bundle["scenarios"]))
