#!/bin/sh
set -eu

PROJECT_NAME="${PROJECT_NAME:-personal-infra-tools}"
PROJECT_ROOT="${PROJECT_ROOT:-$(pwd)}"
VENV_PATH="${VENV_PATH:-$PROJECT_ROOT/.venv}"
SKIP_TESTS="${SKIP_TESTS:-0}"
RECREATE_VENV="${RECREATE_VENV:-0}"
SERVICE_REGISTRY_PATH="${SERVICE_REGISTRY_PATH:-}"

cd "$PROJECT_ROOT"

if [ "$RECREATE_VENV" = "1" ] && [ -d "$VENV_PATH" ]; then
  rm -rf "$VENV_PATH"
fi

mkdir -p data logs

if [ ! -d "$VENV_PATH" ]; then
  python3.11 -m venv "$VENV_PATH"
fi

"$VENV_PATH/bin/python" -m pip install --upgrade pip
"$VENV_PATH/bin/pip" install -e ".[dev]"

if [ "$SKIP_TESTS" != "1" ]; then
  "$VENV_PATH/bin/pytest"
fi

if [ -n "$SERVICE_REGISTRY_PATH" ]; then
  export SERVICE_REGISTRY_PATH
  "$VENV_PATH/bin/fastapi-message" validate-registry
else
  echo "SERVICE_REGISTRY_PATH is not set; skipping real registry validation."
fi

PYTHON="$VENV_PATH/bin/python" scripts/smoke_test.sh

echo "Deploy complete: $PROJECT_NAME package installed and smoke test passed."
