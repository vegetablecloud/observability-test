"""Kunskapsbasen som rag-api söker i. Laddas in i ParadeDB (BM25 + pgvector) vid start."""

DOCS = [
    # --- observability (frågor om hur man felsöker) ----------------------------------------------
    ("metrics", "Metrics", "Metrics svarar på frågan: är något fel? En p95-graf som går från 200 ms till 4 s visar direkt att något hänt."),
    ("traces", "Traces", "Traces svarar på frågan: var händer det? En trace-waterfall visar vilken tjänst och vilket anrop som tog tiden."),
    ("logs", "Logs", "Logs svarar på frågan: vad exakt hände? Filtrera loggar på trace_id för att se just den requestens händelser."),
    ("traces", "Propagation", "Trace context propageras mellan tjänster med W3C traceparent-headern så att alla spans får samma trace_id."),
    ("logs", "Loggkorrelation", "Lägg trace_id och span_id i varje loggrad. Då kan Grafana hoppa från en span direkt till dess loggar i Loki."),
    ("metrics", "Cardinality", "Undvik höga cardinality-labels som user_id eller request_id i metrics. Varje unikt värde blir en ny tidsserie."),
    ("metrics", "Metrictyper", "Counter växer bara (requests_total), Gauge går upp och ner (queue_length) och Histogram ger fördelningar (p95)."),
    ("collector", "Collector", "OpenTelemetry Collector tar emot OTLP, batchar, filtrerar, redigerar känslig data och samplar innan export."),
    ("collector", "Tail sampling", "Tail sampling behåller alla traces med fel och alla långsamma traces, och bara en andel av resten."),
    ("traces", "Span metrics", "Tempo metrics-generator räknar fram RED-metrics (rate, errors, duration) och en service graph ur traces."),
    ("infra", "Infrastruktur", "Infrastrukturmetrics som CPU, minne och GPU hämtas med pull från exporters som node-exporter, cAdvisor och dcgm-exporter."),
    ("infra", "DGX Spark", "På en DGX Spark delar CPU och GPU på 128 GB unified memory. Full GPU ger längre LLM-latens och timeouts."),
    ("metrics", "Exemplars", "Exemplars kopplar en punkt i en histogram-graf till den trace som gav värdet. Klicka på punkten för att öppna tracen."),
    ("collector", "Push och pull", "Push betyder att tjänsten själv skickar OTLP till Collectorn. Pull betyder att Prometheus eller Collectorn hämtar /metrics."),
    ("logs", "Loki", "Loki indexerar bara ett fåtal labels som service_name. Resten, som trace_id, lagras som structured metadata."),
    ("agent", "LangGraph-noder", "I en LangGraph-agent blir varje nod en span. Då syns i vilken nod, i vilket steg och i vilket verktyg ett fel uppstod."),
    ("agent", "Tool calls", "När modellen anropar ett verktyg loggas verktygets namn, argument och resultat på spanen execute_tool."),
    ("agent", "Recursion limit", "LangGraph stoppar en agent som loopar med GraphRecursionError när antalet steg passerar recursion_limit."),
    # --- projektdata (frågor som kräver förberäknade insikter) -----------------------------------
    ("projekt", "Leveransrisk", "Ett projekt med försenade leveranser av material har högre risk. Följ upp leveransplanen varje vecka."),
    ("projekt", "Budgetprognos", "Budgetprognosen jämför upparbetad kostnad med plan. Avvikelse över 10 procent ska rapporteras till styrgruppen."),
    ("projekt", "Projektstatus", "Projektstatus sammanfattar tidplan, kostnad och kvalitet. Grön betyder enligt plan, gul betyder avvikelse."),
    ("projekt", "Riskregister", "Riskregistret listar sannolikhet och konsekvens per risk. De tre största riskerna tas upp på varje projektmöte."),
    ("projekt", "Förberäkning", "Tunga beräkningar som prognoser görs i förväg av algoritmtjänsten så att agenten får svar på under en sekund."),
]
