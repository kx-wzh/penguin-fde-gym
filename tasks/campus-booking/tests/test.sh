#!/bin/bash
set -euo pipefail

exec python3 -E /opt/fde-gym-private/harness/verify.py --require-simulator
