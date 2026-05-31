#!/bin/sh
set -eu

LOG_FILE="${OPS_CORE_LOG_FILE:-logs/ops-core.log}"

if [ -f "$LOG_FILE" ]; then
  tail -f "$LOG_FILE"
else
  journalctl -u ops-core -f
fi
