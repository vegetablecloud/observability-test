#!/usr/bin/env bash
# Testflöde A→Ö: kör en uppsättning scenarier med ett eget test-run-id och skriv ut
# en länk per fråga (trace) och en länk till hela testkörningen i Grafana.
#
#   ./scripts/e2e-test.sh            kör alla scenarier i normalläge
#   ./scripts/e2e-test.sh loop       kör dem med ett chaos-läge aktivt (återställs efteråt)
#
# Varje anrop skickar headern x-test-run-id. Frontend sätter den som attributet
# test.run.id på root-spanen, och dashboarden "05 · Testflöde A→Ö" filtrerar på den.
set -euo pipefail
URL="${FRONTEND_URL:-http://localhost:8080}"
GRAFANA="${GRAFANA_URL:-http://localhost:3000}"
RUN="e2e-$(date +%H%M%S)"
MODE="${1:-normal}"

SCENARIOS=(
  "Hur kopplar jag loggar i Loki till en trace_id?"
  "Hur ser prognosen ut för projekt P-101?"
  "Vilka risker finns i projekt P-102 och håller budgeten?"
  "Vad är status för projekt P-999?"
  "Hur ser jag vilken LangGraph-nod som felar?"
)

[[ "$MODE" != "normal" ]] && curl -fsS -X POST "$URL/demo/chaos/$MODE" >/dev/null && echo "chaos: $MODE"
printf "\n%-8s %-6s %-7s %-60s %s\n" "status" "ms" "steg" "fråga" "trace"
for q in "${SCENARIOS[@]}"; do
  start=$(date +%s%3N)
  out=$(curl -sS -o /tmp/e2e.json -w "%{http_code} %header{x-trace-id}" -X POST "$URL/ask" \
        -H 'content-type: application/json' -H "x-test-run-id: $RUN" \
        -d "{\"question\":\"$q\",\"userId\":\"tester\",\"userEmail\":\"tester@kund.se\"}")
  ms=$(( $(date +%s%3N) - start ))
  code=${out%% *}; tid=${out#* }
  steps=$(python3 -c "import json;d=json.load(open('/tmp/e2e.json'));print(len(d.get('steps',[])))" 2>/dev/null || echo "-")
  printf "%-8s %-6s %-7s %-60s %s\n" "$code" "$ms" "$steps" "${q:0:58}" "$GRAFANA/d/test-flow?var-test_run=$RUN&var-trace_id=$tid"
done
[[ "$MODE" != "normal" ]] && curl -fsS -X POST "$URL/demo/chaos/normal" >/dev/null && echo "chaos: normal"

echo
echo "Hela testkörningen:  $GRAFANA/d/test-flow?var-test_run=$RUN"
echo "(traces syns efter ~10 s: tail sampling väntar in hela tracen innan den skickas)"
