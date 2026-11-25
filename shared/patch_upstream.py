"""Apply the Harbor isolation changes to the pinned harness and robot pilot at build time."""

from pathlib import Path
import sys


def replace(path, before, after):
    source = path.read_text()
    if source.count(before) != 1:
        raise RuntimeError(f"Unexpected pinned source in {path.name}: could not apply Harbor isolation")
    path.write_text(source.replace(before, after))


def main():
    private = Path(sys.argv[1])
    harness = private / "harness"
    replace(
        harness / "isolate.py",
        'return plain, "environment scrubbed; delivered code could NOT be started as user %d" % uid',
        'raise RuntimeError("FDE-Gym could not isolate delivered code as user %d" % uid)',
    )
    replace(
        harness / "llm.py",
        "raise RuntimeError(json.dumps(d)[:300])",
        'raise RuntimeError("Simulator response did not contain choices")',
    )

    replace(
        harness / "llm.py",
        'raise RuntimeError("LLM call failed: %s" % last)',
        'raise RuntimeError("Simulator model request failed") from None',
    )

    case, = (private / "cases").iterdir()
    pilot = case / "pilot.py"
    if case.name != "robot_cell_rollout":
        if pilot.exists():
            raise RuntimeError("Unexpected pilot in the pinned FDE-Gym case")
        return

    replace(pilot, "import csv\n", "import csv\nfrom harbor_security import open_pilot_csv, open_pilot_request\n")
    replace(
        pilot,
        'with open(os.path.join(ws, "system", "fleet", "trial_request.json"), "rb") as f:',
        "with open_pilot_request(ws) as f:",
    )
    replace(
        pilot,
        '    os.makedirs(os.path.join(ws, "data", "trials"), exist_ok=True)\n'
        '    path = os.path.join(ws, "data", "trials", "trial_%d.csv" % day)\n'
        '    with open(path, "w", newline="", encoding="utf-8") as fh:',
        "    with open_pilot_csv(ws, day) as fh:",
    )
    # This pinned pilot uses data files and does not spawn delivered code. Its
    # filesystem access above does not require giving it ownership of /app.
    server = harness / "npc_server.py"
    source = server.read_text()
    before = source.index("        # A trial runs the agent's code.")
    after = source.index("    ThreadingHTTPServer(", before)
    guard = '        if os.path.dirname(a.pilot) != "/opt/fde-gym-private/cases/robot_cell_rollout":\n'
    isolated_setup = source[before:after]
    guard += "".join("    " + line for line in isolated_setup.splitlines(keepends=True))
    replace(server, isolated_setup, guard)


if __name__ == "__main__":
    main()
