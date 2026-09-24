#!/usr/bin/env bash
# Simulera en incident i LLM-servern (mock-läget).
#   ./scripts/incident.sh slow    GPU mättas, LLM-anrop tar 1-4 s -> timeouts + retry
#   ./scripts/incident.sh error   30 % av LLM-anropen ger 500
#   ./scripts/incident.sh normal  tillbaka till normalläge
#   ./scripts/incident.sh story   normal 3 min -> slow 3 min -> normal (som i filmen)
set -euo pipefail
URL="${FRONTEND_URL:-http://localhost:8080}"
mode="${1:-slow}"

set_mode() { curl -fsS -X POST "$URL/demo/chaos/$1"; echo; }

if [[ "$mode" == "story" ]]; then
  set_mode normal; echo "normal i 3 min..."; sleep 180
  set_mode slow;   echo "INCIDENT i 3 min – öppna Grafana 02 · Plattform · Översikt"; sleep 180
  set_mode normal; echo "klart. Följ nu metrics -> exemplar -> trace -> logs."
else
  set_mode "$mode"
fi
