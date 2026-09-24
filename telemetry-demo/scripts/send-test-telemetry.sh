#!/usr/bin/env bash
# Visar "kontraktet" för ett externt team: allt de behöver är Collectorns endpoint.
# Skickar en span + en loggrad + en metric med ren OTLP/HTTP-JSON (ingen SDK)
# från värdmaskinen, som om det vore en tjänst ni inte äger.
set -euo pipefail
EP="${OTLP_HTTP:-http://localhost:4318}"
now=$(date +%s%N); end=$((now + 250000000))
tid=$(openssl rand -hex 16); sid=$(openssl rand -hex 8)
res='{"attributes":[{"key":"service.name","value":{"stringValue":"partner-service"}},{"key":"service.version","value":{"stringValue":"0.1.0"}},{"key":"deployment.environment.name","value":{"stringValue":"demo"}}]}'

curl -fsS -o /dev/null -H 'content-type: application/json' "$EP/v1/traces" -d "{\"resourceSpans\":[{\"resource\":$res,\"scopeSpans\":[{\"scope\":{\"name\":\"curl\"},\"spans\":[{\"traceId\":\"$tid\",\"spanId\":\"$sid\",\"name\":\"GET /partner/orders\",\"kind\":2,\"startTimeUnixNano\":\"$now\",\"endTimeUnixNano\":\"$end\",\"attributes\":[{\"key\":\"http.route\",\"value\":{\"stringValue\":\"/partner/orders\"}}]}]}]}]}"
curl -fsS -o /dev/null -H 'content-type: application/json' "$EP/v1/logs" -d "{\"resourceLogs\":[{\"resource\":$res,\"scopeLogs\":[{\"logRecords\":[{\"timeUnixNano\":\"$now\",\"severityNumber\":9,\"severityText\":\"INFO\",\"body\":{\"stringValue\":\"order_synced count=12\"},\"traceId\":\"$tid\",\"spanId\":\"$sid\"}]}]}]}"
curl -fsS -o /dev/null -H 'content-type: application/json' "$EP/v1/metrics" -d "{\"resourceMetrics\":[{\"resource\":$res,\"scopeMetrics\":[{\"metrics\":[{\"name\":\"partner.orders.synced\",\"unit\":\"{order}\",\"sum\":{\"aggregationTemporality\":2,\"isMonotonic\":true,\"dataPoints\":[{\"asInt\":\"12\",\"startTimeUnixNano\":\"$now\",\"timeUnixNano\":\"$end\"}]}}]}]}]}"
echo "Skickat till $EP  trace_id=$tid"
echo "Grafana: Explore -> Tempo -> $tid   |  Loki: {service_name=\"partner-service\"}  |  Prometheus: partner_orders_synced_total"
