#!/usr/bin/env bash
set -euo pipefail

project_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
session="laya-e2-submission"
runtime="${LAYA_RUNTIME:-/home/maolinqi/mlq/laya/.venv/bin/python}"
source_root="${LAYA_SOURCE_ROOT:-/home/maolinqi/mlq/laya}"
export E2_MODEL_PATH="${E2_MODEL_PATH:-/home/maolinqi/mlq/laya-jevbench-baseline/multi_type/runs/native_multitype_seed20260925/export}"
export LAYA_DEVICE="${LAYA_DEVICE:-cuda}"
bind="${E2_BIND:-127.0.0.1}"
port="${E2_PORT:-8942}"

test -x "$runtime"
test -f "$source_root/laya/serve.py"
test -f "$E2_MODEL_PATH/model.safetensors"
if tmux has-session -t "$session" 2>/dev/null; then
  echo "already running: $session" >&2
  exit 1
fi
mkdir -p "$project_dir/logs"
export PYTHONPATH="$source_root${PYTHONPATH:+:$PYTHONPATH}"
export USE_TF=0
tmux new-session -d -s "$session" \
  "cd '$project_dir' && '$runtime' -m uvicorn e2_service:app --host '$bind' --port '$port' --workers 1 > '$project_dir/logs/server.log' 2>&1"
echo "started $session on $bind:$port; log: $project_dir/logs/server.log"
