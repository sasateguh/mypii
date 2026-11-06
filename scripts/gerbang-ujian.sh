#!/bin/bash
# Gerbang mypii (hos + Depot CI): lint + ujian (termasuk kunci sha256 split ujian). Tiada rangkaian, tiada model spaCy.
set -euo pipefail
cd "$(dirname "$0")/.."
uv run --frozen ruff check mypii tests
uv run --frozen pytest -q
