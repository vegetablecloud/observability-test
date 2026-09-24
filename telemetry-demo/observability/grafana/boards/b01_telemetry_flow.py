"""
01 · Telemetriflödet – för plattformsteamet.
Svarar på: "Hur rör sig telemetrin, och tappar vi något på vägen?"

  ① Källor       vem pushar vad (per tjänst: spans, serier, loggrader) · vem hämtas (pull)
  ② Collectorn   in → processorer (filter, redact, tail sampling, batch) → ut · Collectorn övervakar sig själv
  ③ Lagring      vad Loki, Tempo och Prometheus faktiskt tar emot
"""

from dashlib import (ACCENT, G300, G500, G700, UP_MAP, WHITE, Board, color_override, field_override, join, loki, organize, prom,
                     stat, table, text, thresholds, timeseries)
from dashlib.diagram import Box, Edge, svg_map

BOXES = [
    Box("fe", 20, 50, "frontend · c#", w=170, h=40), Box("be", 200, 50, "backend · c#", w=170, h=40),
    Box("ai", 20, 100, "ai-chat · py", w=170, h=40, accent=True), Box("rag", 200, 100, "rag-api · py", w=170, h=40),
    Box("alg", 20, 150, "algorithm · py", w=170, h=40), Box("ext", 200, 150, "andra team", "→ :4317/:4318", w=170, h=40, dashed=True),
    Box("vg", 20, 230, "vllm-gemma", w=110, h=40, dashed=True), Box("ve", 140, 230, "vllm-embed", w=110, h=40, dashed=True),
    Box("pg", 260, 230, "postgres", w=110, h=40, dashed=True), Box("pdb", 20, 280, "paradedb", w=110, h=40, dashed=True),
    Box("inf", 140, 280, "node · cadvisor · dcgm", w=230, h=40, dashed=True),
    Box("col", 520, 50, "OTel Collector", "memory_limiter · filter · redact · tail_sampling · batch",
        w=560, h=90, accent=True),
    Box("loki", 1180, 40, "loki", "logs", w=160, h=50), Box("tempo", 1180, 110, "tempo", "traces → span-metrics", w=160, h=50),
    Box("prom", 1180, 180, "prometheus", "metrics", w=160, h=50), Box("graf", 1420, 110, "grafana", "frågar alla tre", w=160, h=50),
]
EDGES = [
    Edge("be", "col", label="OTLP push"), Edge("pg", "col", kind="pull", label="Collectorn hämtar"),
    Edge("inf", "prom", kind="pull", label="Prometheus skrapar"), Edge("col", "loki", kind="telemetry"),
    Edge("col", "tempo", kind="telemetry"), Edge("col", "prom", kind="telemetry"), Edge("tempo", "prom", kind="telemetry"),
    Edge("loki", "graf", kind="telemetry"), Edge("tempo", "graf", kind="telemetry"), Edge("prom", "graf", kind="telemetry"),
]
COLS = [(20, "① KÄLLOR · push (överst) och pull (streckat)"), (520, "② OTEL COLLECTOR"), (1180, "③ LAGRING"), (1420, "④ GRAFANA")]


def build():
    b = Board("telemetry-flow", "01 · Telemetriflödet", "Hur rör sig telemetrin, och tappar vi något på vägen?", tags=["plattform"])
    b.add(text(svg_map(BOXES, EDGES, COLS, height=360), mode="html"), w=24, h=11)

    b.row("① Källor · vem skickar vad?")
    b.add(table("Push-tjänster · telemetri per service.name", [
        prom('sum by (service) (rate(traces_spanmetrics_calls_total[2m]))', ref="A", instant=True, fmt="table"),
        prom('count by (service_name) ({service_name=~".+", job!~"vllm-.*|postgres|paradedb"})', ref="B", instant=True, fmt="table"),
        loki('sum by (service_name) (rate({service_name=~".+"}[2m]))', ref="C", instant=True)],
        transformations=[organize(rename={"service": "service_name"}), join("service_name"),
                         organize(exclude=["Time", "Time 1", "Time 2", "Time 3"],
                                  rename={"service_name": "Tjänst", "Value #A": "Spans/s", "Value #B": "Metric-serier", "Value #C": "Loggrader/s"})],
        overrides=[field_override("Spans/s", decimals=1), field_override("Loggrader/s", decimals=1)], sort="Spans/s",
        desc="Spans/s (Tempo span-metrics), aktiva metric-serier (Prometheus) och loggrader/s (Loki) per tjänst. "
             "Tre olika lager, samma service.name – därför går de att ställa mot varandra."), w=12, h=9)
    b.add(stat("Collectorn hämtar (pull)", [prom('max by (job) (up{job=~"vllm-.*"})', "{{job}}", instant=True, ref="A"),
                                            prom('max by (service_name) (postgresql_backends >= bool 0)', "{{service_name}}", instant=True, ref="B")],
               unit="none", mappings=UP_MAP, spark=False, text_mode="value_and_name", color_mode="background_solid",
               th=thresholds((None, "#161616")), orientation="horizontal", text_size=(13, 16),
               desc="Tredjepart du inte äger: Collectorns prometheus- och postgresql-receivers hämtar och skickar vidare som OTLP."),
          w=6, h=9)
    b.add(stat("Prometheus skrapar själv (pull)", [prom('max by (job) (up{service_name=""})', "{{job}}", instant=True)], unit="none",
               mappings=UP_MAP, spark=False, text_mode="value_and_name", color_mode="background_solid", th=thresholds((None, "#161616")),
               orientation="horizontal", text_size=(13, 16), desc="Scrape-mål i prometheus.yml: infrastruktur och observability-stacken själv."), w=6, h=9)

    b.row("② OTel Collector · receive → process → export")
    b.add(stat("In: spans/s", [prom("sum(rate(otelcol_receiver_accepted_spans[1m]))")], decimals=0,
               desc="Spans som Collectorn tagit emot (alla receivers)."), w=4, h=4)
    b.add(stat("In: metric points/s", [prom("sum(rate(otelcol_receiver_accepted_metric_points[1m]))")], decimals=0,
               desc="Metric-datapunkter in: OTLP från tjänsterna + det Collectorn hämtar själv."), w=4, h=4)
    b.add(stat("In: loggrader/s", [prom("sum(rate(otelcol_receiver_accepted_log_records[1m]))")], decimals=0,
               desc="Loggrader in, före filtrering."), w=4, h=4)
    b.add(stat("Refused / failed", [prom(
        "(sum(rate(otelcol_receiver_refused_spans[1m])) or vector(0)) + (sum(rate(otelcol_receiver_refused_log_records[1m])) or vector(0))"
        " + (sum(rate(otelcol_receiver_refused_metric_points[1m])) or vector(0)) + (sum(rate(otelcol_exporter_send_failed_spans[1m])) or vector(0))")],
        decimals=1, th=thresholds((None, WHITE), (0.01, ACCENT)),
        desc="Ska vara 0. Blir den gul: Collectorn eller en backend orkar inte (memory_limiter backar av eller exporten misslyckas)."), w=4, h=4)
    b.add(stat("Exporter-kö", [prom("sum(otelcol_exporter_queue_size)")], th=thresholds((None, WHITE), (100, ACCENT)),
               desc="Data som väntar på att skickas till Loki/Tempo/Prometheus. Växer den är en backend långsam."), w=4, h=4)
    b.add(stat("Collector-minne", [prom("max(otelcol_process_memory_rss)")], unit="bytes",
               desc="Collectorns eget minne. memory_limiter börjar backa vid 80 % av gränsen."), w=4, h=4)
    b.add(timeseries("In per receiver", [
        prom("sum by (receiver) (rate(otelcol_receiver_accepted_spans[1m]))", "spans · {{receiver}}"),
        prom("sum by (receiver) (rate(otelcol_receiver_accepted_log_records[1m]))", "logs · {{receiver}}"),
        prom("sum by (receiver) (rate(otelcol_receiver_accepted_metric_points[1m]))", "metrics · {{receiver}}")],
        overrides=[color_override("spans · otlp", ACCENT, width=3), color_override("logs · otlp", WHITE),
                   color_override("metrics · otlp", G300), color_override("metrics · prometheus", G500, dash=True),
                   color_override("metrics · postgresql/app", G700, dash=True), color_override("metrics · postgresql/rag", G700, dash=True)],
        desc="otlp = push från tjänsterna. prometheus/postgresql = pull som Collectorn gör själv."), w=8, h=8)
    b.add(timeseries("Filter: det som aldrig lagras", [
        prom('sum(rate({"otelcol_processor_filter_spans.filtered"}[1m]))', "spans (/health, ASGI-brus)"),
        prom('sum(rate({"otelcol_processor_filter_logs.filtered"}[1m]))', "loggar (DEBUG)")],
        overrides=[color_override("spans (/health, ASGI-brus)", ACCENT), color_override("loggar (DEBUG)", G300, dash=True)],
        desc="filter/noise slänger health checks, FastAPI:s interna mini-spans och DEBUG-loggar innan något lagras."), w=8, h=8)
    b.add(timeseries("Tail sampling · beslut per policy", [
        prom('sum by (policy) (rate(otelcol_processor_tail_sampling_count_traces_sampled{sampled="true"}[1m]))', "behåll · {{policy}}"),
        prom('sum(rate(otelcol_processor_tail_sampling_global_count_traces_sampled{sampled="false"}[1m]))', "släng")],
        overrides=[color_override("behåll · errors", ACCENT, width=3), color_override("behåll · slow", ACCENT, dash=True),
                   color_override("behåll · rest", G300), color_override("släng", G700)],
        desc="errors och slow behålls alltid. 'rest' styrs av TRACE_SAMPLING_PERCENT i .env (100 = allt). Prova 10."), w=8, h=8)
    b.add(timeseries("Ut per exporter", [
        prom("sum by (exporter) (rate(otelcol_exporter_sent_spans[1m]))", "spans → {{exporter}}"),
        prom("sum by (exporter) (rate(otelcol_exporter_sent_log_records[1m]))", "logs → {{exporter}}"),
        prom("sum by (exporter) (rate(otelcol_exporter_sent_metric_points[1m]))", "metrics → {{exporter}}")],
        overrides=[color_override("spans → otlp_grpc/tempo", ACCENT, width=3), color_override("logs → otlp_http/loki", WHITE),
                   color_override("metrics → otlp_http/prometheus", G300)],
        desc="Det som faktiskt lämnar Collectorn, per backend."), w=12, h=7)
    b.add(timeseries("Batch-storlek · färre, större skrivningar", [
        prom("histogram_quantile(0.5, sum by (le) (rate(otelcol_processor_batch_batch_send_size_bucket[2m])))", "p50 items per batch"),
        prom("sum(rate(otelcol_processor_batch_timeout_trigger_send[1m]))", "batchar p.g.a. timeout /s")],
        overrides=[color_override("p50 items per batch", WHITE), color_override("batchar p.g.a. timeout /s", G500, dash=True, axis_right=True)],
        desc="batch-processorn samlar data innan export. Timeout-triggade batchar = lite trafik (skickas efter 2 s)."), w=12, h=7)

    b.row("③ Lagring · vad backends tar emot")
    b.add(stat("Loki: loggrader/s", [prom("sum(rate(loki_distributor_lines_received_total[1m]))")], decimals=0,
               desc="Loggrader Loki tagit emot."), w=4, h=4)
    b.add(stat("Loki: bytes/s", [prom("sum(rate(loki_distributor_bytes_received_total[1m]))")], unit="Bps",
               desc="Loggvolym in i Loki. Kostnaden för loggar följer den här siffran."), w=4, h=4)
    b.add(stat("Tempo: spans/s", [prom("sum(rate(tempo_distributor_spans_received_total[1m]))")], decimals=0,
               desc="Spans Tempo tagit emot, efter tail sampling."), w=4, h=4)
    b.add(stat("Tempo: aktiva traces", [prom("sum(tempo_ingester_live_traces)")], desc="Traces som ingestern håller i minnet just nu."), w=4, h=4)
    b.add(stat("Prometheus: aktiva serier", [prom("max(prometheus_tsdb_head_series)")], th=thresholds((None, WHITE), (50000, ACCENT)),
               desc="Tidsserier i minnet. Växer den okontrollerat: cardinality-problem (se 09)."), w=4, h=4)
    b.add(stat("Prometheus: samples/s", [prom("sum(rate(prometheus_tsdb_head_samples_appended_total[1m]))")], decimals=0,
               desc="Datapunkter per sekund in i Prometheus."), w=4, h=4)
    return b
