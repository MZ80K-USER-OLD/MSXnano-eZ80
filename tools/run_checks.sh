#!/bin/sh
set -eu
cd "$(dirname "$0")/.."
python3 tools/verify_r11_9.py
