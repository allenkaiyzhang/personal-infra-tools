#!/usr/bin/env bash
set -euo pipefail

APP_DIR="${APP_DIR:-/opt/personal-infra-tools}"
VENV_DIR="${VENV_DIR:-$APP_DIR/.venv}"
RUN_TESTS="${RUN_TESTS:-1}"

cd "$APP_DIR"

if [ -d .git ] && [ "${GIT_PULL:-0}" = "1" ]; then
  git pull --ff-only
fi

mkdir -p data logs

python3.11 -m venv "$VENV_DIR"
"$VENV_DIR/bin/python" -m pip install --upgrade pip
"$VENV_DIR/bin/pip" install -e ".[dev]"

if [ "$RUN_TESTS" = "1" ]; then
  "$VENV_DIR/bin/pytest"
fi

"$VENV_DIR/bin/fastapi-message" validate-registry || {
  echo "Registry validation failed. Set SERVICE_REGISTRY_PATH or install /opt/personal-infra/services.yaml." >&2
  exit 1
}

scripts/smoke_test.sh

echo "Deploy complete: personal-infra-tools package installed and smoke test passed."
