#!/bin/bash
set -euo pipefail

# Harbor starts the main service with /app as its working directory.
# Keep the run metadata private and expose the generated workspace at /app.
cd /
runner=/opt/fde-gym-private/harness/run.py
python3 "$runner" new --engagement campus_booking --level L3 --name "$FDE_TASK_RUN"

workspace="$FDEGYM_RUNS/$FDE_TASK_RUN/workspace"
rmdir /app
mv "$workspace" /app
ln -s /app "$workspace"
chown -R fde-agent:fde-agent /app

exec python3 "$runner" serve --name "$FDE_TASK_RUN"
