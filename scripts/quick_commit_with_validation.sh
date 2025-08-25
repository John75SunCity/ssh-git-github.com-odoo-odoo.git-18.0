#!/usr/bin/env bash
set -euo pipefail

# Wrapper to run validation with python3 (not python), then commit staged changes

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT_DIR"

if ! command -v python3 >/dev/null 2>&1; then
  echo "python3 not found; please install Python 3." >&2
  exit 127
fi

python3 development-tools/syntax-tools/find_syntax_errors.py

git add .
msg=${1:-"fix: Automated syntax and translation fixes (python3 wrapper)"}
git commit -m "$msg" || {
  echo "No changes to commit."; exit 0; }
