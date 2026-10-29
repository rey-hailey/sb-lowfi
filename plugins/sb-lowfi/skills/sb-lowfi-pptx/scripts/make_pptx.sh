#!/bin/bash
# low-fi HTML -> 화면설계서 PPTX 한 번에
# 사용: make_pptx.sh <lowfi.html> <out.pptx> [--md 화면설계서.md] [--project 이름] [--date YYYY-MM-DD] [--version v1.0] [--note "..."]
set -e
SK="$(cd "$(dirname "$0")/.." && pwd)"
PY="$SK/.venv/bin/python"
if [ ! -x "$PY" ]; then python3 -m venv "$SK/.venv" && "$SK/.venv/bin/pip" install -q python-pptx lxml; fi
HTML="$1"; OUT="$2"; shift 2
GEO="$(mktemp -t geo).json"
"$PY" "$SK/scripts/extract_geo.py" "$HTML" "$GEO"
"$PY" "$SK/scripts/build_pptx.py" --geo "$GEO" --out "$OUT" "$@"
