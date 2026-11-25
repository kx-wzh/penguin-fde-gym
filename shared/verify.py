"""Run the pinned FDE-Gym grader and publish its Harbor reward on success."""

import json
import math
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile

from harbor_security import (
    VERIFIER_LOGS,
    WORKSPACE,
    protect_verifier_logs,
    stop_agent_processes,
    verify_workspace_tree,
)


def reward_from_report(report, require_simulator):
    if require_simulator and report.get("simulator_errors", 0):
        raise RuntimeError("FDE-Gym could not complete all simulated campus conversations")
    score = report["uplift_net"]
    if isinstance(score, bool) or not isinstance(score, (int, float)) or not math.isfinite(score):
        raise ValueError("FDE-Gym returned an invalid uplift_net")
    return max(0.0, min(1.0, score))


def main():
    protect_verifier_logs()
    (VERIFIER_LOGS / "fde-result.json").unlink(missing_ok=True)
    stop_agent_processes()
    verify_workspace_tree(WORKSPACE)

    require_simulator = sys.argv[1:] == ["--require-simulator"]
    if require_simulator and not os.environ.get("FDEGYM_LLM_URL"):
        key_file = Path(os.environ["FDEGYM_OPENROUTER_KEY_FILE"])
        if key_file.stat().st_size == 0:
            raise RuntimeError("Campus scoring needs FDEGYM_MODEL_KEY_FILE or a FDEGYM_LLM_URL endpoint")

    run = os.environ["FDE_TASK_RUN"]
    with (VERIFIER_LOGS / "fde-grade-stdout.json").open("w") as stdout:
        subprocess.run(
            [sys.executable, str(Path(__file__).with_name("run.py")), "grade", "--name", run],
            stdout=stdout,
            check=True,
        )

    report = Path(os.environ["FDEGYM_RUNS"]) / run / "result.json"
    shutil.copyfile(report, VERIFIER_LOGS / "fde-result.json")
    reward = reward_from_report(json.loads(report.read_text()), require_simulator)
    with tempfile.NamedTemporaryFile(mode="w", dir=VERIFIER_LOGS, delete=False) as pending:
        try:
            json.dump({"reward": reward}, pending)
            pending.write("\n")
            pending.close()
            os.chmod(pending.name, 0o644)
            os.replace(pending.name, VERIFIER_LOGS / "reward.json")
        finally:
            Path(pending.name).unlink(missing_ok=True)


if __name__ == "__main__":
    main()
