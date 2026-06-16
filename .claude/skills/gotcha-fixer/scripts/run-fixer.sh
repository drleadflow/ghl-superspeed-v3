#!/usr/bin/env bash
# Print agent-ready briefs for every OPEN gotcha, one block per gotcha.
# The gotcha-fixer skill dispatches one background agent per block.
#   ./run-fixer.sh            # all open gotchas
#   ./run-fixer.sh <id>       # a single gotcha
set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../../../.." && pwd)"
exec python3 "$ROOT/scripts/gotcha.py" brief "${1:-}"
