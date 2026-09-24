#!/usr/bin/env bash
# Simulera en incident i stacken (mock-läget). Ett läge i taget, sätts i alla tjänster via frontend.
#   ./scripts/incident.sh slow       GPU mättas, gemma svarar på 1-4 s -> timeouts + retry
#   ./scripts/incident.sh error      30 % av gemmas svar ger 500
#   ./scripts/incident.sh loop       agenten slutar aldrig anropa verktyg -> recursion_limit
#   ./scripts/incident.sh bad_args   trasiga tool-argument -> ToolArgumentError
#   ./scripts/incident.sh rag_error  sökindexet ger 503 i 40 % av sökningarna
#   ./scripts/incident.sh db_slow    ParadeDB-frågorna tar ~1 s
#   ./scripts/incident.sh stale      förberäkningen stannar -> långsamma verktygsanrop
#   ./scripts/incident.sh normal     tillbaka till normalläge
#   ./scripts/incident.sh story      normal 3 min -> slow 3 min -> normal (som i filmen)
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
