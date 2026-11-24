import json
import os
from pathlib import Path
import socket


run_dir = Path(os.environ["FDEGYM_RUNS"]) / os.environ["FDE_TASK_RUN"]
meta = json.loads((run_dir / "meta.json").read_text())
ports = [meta["port"], *meta.get("service_ports", {}).values()]
if "llm_port" in meta:
    ports.append(meta["llm_port"])

for port in ports:
    with socket.create_connection(("127.0.0.1", port), timeout=0.5):
        pass
