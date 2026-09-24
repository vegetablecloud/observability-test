"""Kunskapsbasen som RAG-steget söker i (lagras som vektorer i Qdrant vid start)."""

DOCS = [
    ("metrics", "Metrics svarar på frågan: är något fel? En p95-graf som går från 200 ms till 4 s visar direkt att något hänt."),
    ("traces", "Traces svarar på frågan: var händer det? En trace-waterfall visar vilken tjänst och vilket anrop som tog tiden."),
    ("logs", "Logs svarar på frågan: vad exakt hände? Filtrera loggar på trace_id för att se just den requestens händelser."),
    ("traces", "Trace context propageras mellan tjänster med W3C traceparent-headern så att alla spans får samma trace_id."),
    ("logs", "Lägg trace_id och span_id i varje loggrad. Då kan Grafana hoppa från en span direkt till dess loggar i Loki."),
    ("metrics", "Undvik höga cardinality-labels som user_id eller request_id i metrics. Varje unikt värde blir en ny tidsserie."),
    ("metrics", "Counter växer bara (requests_total), Gauge går upp och ner (queue_length) och Histogram ger fördelningar (p95)."),
    ("collector", "OpenTelemetry Collector tar emot OTLP, batchar, filtrerar, redigerar känslig data och samplar innan export."),
    ("collector", "Tail sampling behåller alla traces med fel och alla långsamma traces, och bara en andel av resten."),
    ("traces", "Tempo metrics-generator räknar fram RED-metrics (rate, errors, duration) och en service graph ur traces."),
    ("infra", "Infrastrukturmetrics som CPU, minne och GPU hämtas med pull från exporters som node-exporter, cAdvisor och dcgm-exporter."),
    ("infra", "På en DGX Spark delar CPU och GPU på 128 GB unified memory. Full GPU ger längre LLM-latens och timeouts."),
    ("metrics", "Exemplars kopplar en punkt i en histogram-graf till den trace som gav värdet. Klicka på punkten för att öppna tracen."),
    ("collector", "Push betyder att tjänsten själv skickar OTLP till Collectorn. Pull betyder att Prometheus eller Collectorn hämtar /metrics."),
    ("logs", "Loki indexerar bara ett fåtal labels som service_name. Resten, som trace_id, lagras som structured metadata."),
]
