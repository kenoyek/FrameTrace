#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."
export UV_CACHE_DIR="${UV_CACHE_DIR:-/workspace/.cache/uv}"
export npm_config_cache="${npm_config_cache:-/workspace/.cache/npm}"
command -v ffmpeg >/dev/null
command -v ffprobe >/dev/null
uv venv --allow-existing .venv
uv pip sync --python .venv/bin/python services/api/requirements-dev.lock
uv pip install --python .venv/bin/python --no-deps -e services/api
cd apps/mobile
npm ci --no-audit --no-fund
