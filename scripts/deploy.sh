#!/bin/sh
set -eu

PROJECT_ROOT="${PROJECT_ROOT:-$(pwd)}"
VENV_PATH="${VENV_PATH:-$PROJECT_ROOT/.venv}"
SKIP_TESTS="${SKIP_TESTS:-0}"
SYSTEMD_SERVICE="${SYSTEMD_SERVICE:-ops-core}"

cd "$PROJECT_ROOT"

mkdir -p data logs

if [ ! -d "$VENV_PATH" ]; then
  python3.11 -m venv "$VENV_PATH"
fi

"$VENV_PATH/bin/python" -m pip install --upgrade pip
"$VENV_PATH/bin/pip" install -e ".[dev]"

"$VENV_PATH/bin/python" -m compileall .

if [ "$SKIP_TESTS" != "1" ]; then
  "$VENV_PATH/bin/pytest" -q
fi

install -m 0644 deploy/systemd/ops-core.service "/etc/systemd/system/${SYSTEMD_SERVICE}.service"
systemctl daemon-reload
systemctl enable "$SYSTEMD_SERVICE"
systemctl restart "$SYSTEMD_SERVICE"

scripts/smoke_test.sh
systemctl status --no-pager "$SYSTEMD_SERVICE"

echo "Deploy complete: ops-core installed, restarted, and smoke test passed."
