#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."
# Set GHDL, IVERILOG, IVL_ROOT, VVP when these tools are not on PATH.
python3 tools/verify_r1.py
python3 tools/verify_memory_r1.py
