#!/usr/bin/env bash
set -euo pipefail

session="laya-e2-submission"
if tmux has-session -t "$session" 2>/dev/null; then
  tmux kill-session -t "$session"
  echo "stopped $session"
else
  echo "$session is not running"
fi
