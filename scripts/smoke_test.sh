#!/bin/sh
set -eu

BASE_URL="${OPS_CORE_BASE_URL:-http://127.0.0.1:8080}"

HEALTH="$(curl -fsS "$BASE_URL/health")"
printf '%s' "$HEALTH" | grep '"status"[[:space:]]*:[[:space:]]*"ok"' >/dev/null
printf '%s' "$HEALTH" | grep '"service"[[:space:]]*:[[:space:]]*"ops-core"' >/dev/null

if [ -n "${OPS_CORE_TOKEN:-}" ]; then
  RESPONSE="$(curl -fsS -X POST "$BASE_URL/api/interactions/telegram" \
    -H "Authorization: Bearer $OPS_CORE_TOKEN" \
    -H "Content-Type: application/json" \
    -d '{"channel":"telegram","event_type":"command","user":{"id":"smoke"},"chat":{"id":"smoke","type":"private"},"message":{"id":1,"text":"/start"},"command":{"name":"start","args":[]}}')"
  printf '%s' "$RESPONSE" | grep '"ok"[[:space:]]*:[[:space:]]*true' >/dev/null
fi

echo "PASS"
