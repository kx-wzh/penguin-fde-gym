#!/bin/bash
set -euo pipefail

mkdir -p /logs/verifier
python3 /opt/fde-gym-private/harness/run.py grade --name "$FDE_TASK_RUN" \
    > /logs/verifier/fde-grade-stdout.json

python3 - <<'PY'
import json
import math
import os
from pathlib import Path
import shutil

report = Path(os.environ["FDEGYM_RUNS"]) / os.environ["FDE_TASK_RUN"] / "result.json"
logs = Path("/logs/verifier")
shutil.copyfile(report, logs / "fde-result.json")

score = json.loads(report.read_text())["uplift_net"]
if isinstance(score, bool) or not isinstance(score, (int, float)) or not math.isfinite(score):
    raise ValueError("FDE-Gym returned an invalid uplift_net")
(logs / "reward.json").write_text(json.dumps({"reward": max(0.0, min(1.0, score))}) + "\n")
PY
