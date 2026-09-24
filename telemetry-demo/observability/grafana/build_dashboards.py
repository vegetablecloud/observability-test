#!/usr/bin/env python3
"""
Genererar Grafana-dashboards (JSON) för telemetry-demot.

    python3 observability/grafana/build_dashboards.py

Varför en generator i stället för handskriven JSON? Dashboard-JSON är mångordig
och svår att granska. Här syns frågorna (PromQL/LogQL/TraceQL) tydligt, och
alla paneler delar samma färger och stil. Grafana läser in resultatet från
observability/grafana/dashboards/ (provisioning), ändringar syns inom 30 s.

Färgspråk (Conpanion): svart/vitt/grått – GULT (#FFB400) bara för det som är
viktigt just nu: huvudserien, eller när ett tröskelvärde passeras.
"""

import json
from pathlib import Path

OUT = Path(__file__).parent / "dashboards"

Y, WH, G200, G300, G500, G700 = "#FFB400", "#FFFFFF", "#EDEDED", "#D6D6D6", "#707070", "#4D4D4D"
PROM = {"type": "prometheus", "uid": "prometheus"}
LOKI = {"type": "loki", "uid": "loki"}
TEMPO = {"type": "tempo", "uid": "tempo"}
MIXED = {"type": "datasource", "uid": "-- Mixed --"}

SERVICE_COLORS = {
    "frontend": WH, "backend": Y, "ai-chat": G300, "algorithm": G500,
    "llm-server": G200, "llm": G200, "qdrant": G700, "postgres": G700, "user": G500, "partner-service": G700,
}

# ---------------------------------------------------------------------------
# Byggstenar
# ---------------------------------------------------------------------------
_id = 0


def _next_id():
    global _id
    _id += 1
    return _id


def prom(expr, legend="", ref="A", instant=False, exemplar=False, fmt=None):
    t = {"datasource": PROM, "refId": ref, "expr": expr, "legendFormat": legend or "__auto",
         "range": not instant, "instant": instant, "exemplar": exemplar}
    if fmt:
        t["format"] = fmt
    return t


def loki(expr, legend="", ref="A", instant=False, qtype="range"):
    return {"datasource": LOKI, "refId": ref, "expr": expr, "legendFormat": legend,
            "queryType": "instant" if instant else qtype}


def color_override(name, color, dash=False, width=None):
    props = [{"id": "color", "value": {"mode": "fixed", "fixedColor": color}}]
    if dash:
        props.append({"id": "custom.lineStyle", "value": {"fill": "dash", "dash": [6, 4]}})
    if width:
        props.append({"id": "custom.lineWidth", "value": width})
    return {"matcher": {"id": "byName", "options": name}, "properties": props}


def service_overrides(names=None):
    names = names or SERVICE_COLORS.keys()
    return [color_override(n, SERVICE_COLORS[n], dash=(n == "algorithm"), width=3 if n == "backend" else None)
            for n in names if n in SERVICE_COLORS]


def thresholds(*steps):
    """steps: (value, color) – första värdet ska vara None (bas)."""
    return {"mode": "absolute", "steps": [{"value": v, "color": c} for v, c in steps]}


def panel(kind, title, grid, targets=None, desc="", ds=PROM, **kw):
    x, y, w, h = grid
    p = {"id": _next_id(), "type": kind, "title": title, "description": desc,
         "gridPos": {"x": x, "y": y, "w": w, "h": h}, "datasource": ds, "targets": targets or []}
    p.update(kw)
    return p


def timeseries(title, grid, targets, unit="short", desc="", overrides=None, fill=0, stack=False, th=None,
               th_style="off", color=None, legend="list", ds=PROM, decimals=None, max_=None, min_=None):
    defaults = {
        "unit": unit,
        "color": {"mode": "fixed", "fixedColor": color} if color else {"mode": "palette-classic"},
        "custom": {"drawStyle": "line", "lineWidth": 2, "fillOpacity": fill, "gradientMode": "opacity" if fill else "none",
                   "showPoints": "never", "spanNulls": True, "axisBorderShow": False, "axisSoftMin": 0,
                   "stacking": {"mode": "normal" if stack else "none", "group": "A"},
                   "thresholdsStyle": {"mode": th_style}},
    }
    if th:
        defaults["thresholds"] = th
    if decimals is not None:
        defaults["decimals"] = decimals
    if max_ is not None:
        defaults["max"] = max_
    if min_ is not None:
        defaults["min"] = min_
    return panel("timeseries", title, grid, targets, desc, ds=ds,
                 fieldConfig={"defaults": defaults, "overrides": overrides or []},
                 options={"legend": {"displayMode": legend, "placement": "bottom", "showLegend": legend != "hidden"},
                          "tooltip": {"mode": "multi", "sort": "desc"}})


def stat(title, grid, targets, unit="short", th=None, desc="", decimals=None, spark=True, text_mode="value",
         mappings=None, color_mode="value", ds=PROM, orientation="auto", reduce="lastNotNull"):
    d = {"unit": unit, "color": {"mode": "thresholds"},
         "thresholds": th or thresholds((None, WH))}
    if decimals is not None:
        d["decimals"] = decimals
    if mappings:
        d["mappings"] = mappings
    return panel("stat", title, grid, targets, desc, ds=ds,
                 fieldConfig={"defaults": d, "overrides": []},
                 options={"reduceOptions": {"calcs": [reduce], "fields": "", "values": False},
                          "colorMode": color_mode, "graphMode": "area" if spark else "none", "textMode": text_mode,
                          "justifyMode": "auto", "orientation": orientation, "wideLayout": True, "showPercentChange": False})


def text(title, grid, content, mode="markdown", transparent=False):
    return panel("text", title, grid, [], ds=None, options={"mode": mode, "content": content}, transparent=transparent)


def row(title, y, collapsed=False):
    return {"id": _next_id(), "type": "row", "title": title, "collapsed": collapsed,
            "gridPos": {"x": 0, "y": y, "w": 24, "h": 1}, "panels": []}


def logs(title, grid, expr, desc=""):
    return panel("logs", title, grid, [loki(expr)], desc, ds=LOKI,
                 options={"showTime": True, "showLabels": False, "showCommonLabels": False, "wrapLogMessage": True,
                          "prettifyLogMessage": False, "enableLogDetails": True, "sortOrder": "Descending",
                          "dedupStrategy": "none", "enableInfiniteScrolling": True})


def table(title, grid, targets, desc="", transformations=None, overrides=None, ds=PROM, unit="short", sort=None):
    opts = {"showHeader": True, "cellHeight": "sm", "footer": {"show": False}}
    if sort:
        opts["sortBy"] = [{"displayName": sort, "desc": True}]
    return panel("table", title, grid, targets, desc, ds=ds,
                 fieldConfig={"defaults": {"unit": unit, "custom": {"align": "auto", "cellOptions": {"type": "auto"}}},
                              "overrides": overrides or []},
                 options=opts, transformations=transformations or [])


def dashboard(uid, title, panels, desc="", variables=None, time="now-30m"):
    return {
        "uid": uid, "title": title, "description": desc, "tags": ["telemetry-demo"],
        "editable": True, "graphTooltip": 1,  # delad crosshair: samma tidpunkt i alla paneler
        "time": {"from": time, "to": "now"}, "refresh": "10s", "schemaVersion": 41, "version": 1,
        "timepicker": {}, "timezone": "browser", "fiscalYearStartMonth": 0, "liveNow": False,
        "templating": {"list": variables or []}, "annotations": {"list": []},
        "links": [{"title": "Telemetry-demo", "type": "dashboards", "tags": ["telemetry-demo"], "asDropdown": False,
                   "includeVars": False, "keepTime": True, "targetBlank": False, "icon": "external link"}],
        "panels": panels,
    }


def write(name, dash):
    OUT.mkdir(exist_ok=True)
    (OUT / name).write_text(json.dumps(dash, indent=2, ensure_ascii=False) + "\n")
    print("wrote", OUT / name)


P95 = 'histogram_quantile(0.95, sum by (le, service_name) (rate(http_server_request_duration_seconds_bucket{http_route!="/health"}[1m])))'
UP_MAP = [{"type": "value", "options": {"1": {"text": "UP", "color": "#161616"}, "0": {"text": "DOWN", "color": Y}}}]


# ---------------------------------------------------------------------------
# 01 · Telemetriflödet – hur datan rör sig, push vs pull, steg för steg
# ---------------------------------------------------------------------------
FLOW_SVG = """
<div style="font-family:Inter,system-ui,sans-serif;color:#fff;padding:4px 8px">
<svg viewBox="0 0 1600 330" width="100%" style="max-height:330px" xmlns="http://www.w3.org/2000/svg" font-family="Roboto Mono, monospace">
  <defs>
    <marker id="a" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="7" markerHeight="7" orient="auto"><path d="M0 0L10 5L0 10z" fill="#D6D6D6"/></marker>
    <marker id="ay" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="7" markerHeight="7" orient="auto"><path d="M0 0L10 5L0 10z" fill="#FFB400"/></marker>
  </defs>
  <g font-size="13" fill="#707070" letter-spacing="1">
    <text x="20" y="20">① KÄLLOR</text><text x="560" y="20">② OTEL COLLECTOR</text><text x="1060" y="20">③ LAGRING</text><text x="1400" y="20">④ GRAFANA</text>
  </g>
  <!-- push -->
  <g font-size="14">
    <text x="20" y="52" fill="#FFB400">PUSH · OTLP · tjänsten äger sin SDK</text>
    <rect x="20" y="62" width="190" height="34" fill="#0D0D0D" stroke="#FFB400"/><text x="32" y="84" fill="#fff">frontend · c#</text>
    <rect x="220" y="62" width="190" height="34" fill="#0D0D0D" stroke="#FFB400"/><text x="232" y="84" fill="#fff">backend · c#</text>
    <rect x="20" y="104" width="190" height="34" fill="#0D0D0D" stroke="#FFB400"/><text x="32" y="126" fill="#fff">algorithm · py</text>
    <rect x="220" y="104" width="190" height="34" fill="#0D0D0D" stroke="#FFB400"/><text x="232" y="126" fill="#fff">ai-chat · py</text>
    <text x="20" y="160" fill="#707070">+ andra team → :4317 / :4318</text>
  </g>
  <!-- pull by collector -->
  <g font-size="14">
    <text x="20" y="196" fill="#D6D6D6">PULL · Collectorn hämtar · du äger inte koden</text>
    <rect x="20" y="206" width="126" height="34" fill="#0D0D0D" stroke="#707070" stroke-dasharray="5 4"/><text x="30" y="228" fill="#fff">vLLM</text>
    <rect x="152" y="206" width="126" height="34" fill="#0D0D0D" stroke="#707070" stroke-dasharray="5 4"/><text x="162" y="228" fill="#fff">qdrant</text>
    <rect x="284" y="206" width="126" height="34" fill="#0D0D0D" stroke="#707070" stroke-dasharray="5 4"/><text x="294" y="228" fill="#fff">postgres</text>
  </g>
  <!-- pull by prometheus -->
  <g font-size="14">
    <text x="20" y="272" fill="#D6D6D6">PULL · Prometheus skrapar infra</text>
    <rect x="20" y="282" width="126" height="34" fill="#0D0D0D" stroke="#707070" stroke-dasharray="5 4"/><text x="30" y="304" fill="#fff">node-exp</text>
    <rect x="152" y="282" width="126" height="34" fill="#0D0D0D" stroke="#707070" stroke-dasharray="5 4"/><text x="162" y="304" fill="#fff">cAdvisor</text>
    <rect x="284" y="282" width="126" height="34" fill="#0D0D0D" stroke="#707070" stroke-dasharray="5 4"/><text x="294" y="304" fill="#fff">dcgm (GPU)</text>
  </g>
  <!-- collector -->
  <rect x="560" y="40" width="420" height="220" fill="#0D0D0D" stroke="#D6D6D6" stroke-width="2"/>
  <g font-size="13" fill="#fff">
    <rect x="580" y="60" width="110" height="180" fill="none" stroke="#4D4D4D"/><text x="592" y="82" fill="#707070">RECEIVE</text>
    <text x="592" y="110">otlp</text><text x="592" y="134">prometheus</text><text x="592" y="158">postgresql</text>
    <rect x="705" y="60" width="140" height="180" fill="none" stroke="#4D4D4D"/><text x="717" y="82" fill="#707070">PROCESS</text>
    <text x="717" y="106">memory_limiter</text><text x="717" y="128">filter (brus)</text><text x="717" y="150">redact (PII)</text><text x="717" y="172">tail_sampling</text><text x="717" y="194">batch</text>
    <rect x="860" y="60" width="104" height="180" fill="none" stroke="#4D4D4D"/><text x="872" y="82" fill="#707070">EXPORT</text>
    <text x="872" y="110">loki</text><text x="872" y="134">tempo</text><text x="872" y="158">prometheus</text>
  </g>
  <!-- arrows sources -> collector -->
  <path fill="none" d="M410 100 L560 100" stroke="#FFB400" stroke-width="3" marker-end="url(#ay)"/>
  <text x="440" y="92" font-size="12" fill="#FFB400">logs·traces·metrics</text>
  <path fill="none" d="M560 222 L410 222" stroke="#D6D6D6" stroke-width="2" stroke-dasharray="6 5" marker-end="url(#a)"/>
  <text x="440" y="214" font-size="12" fill="#D6D6D6">GET /metrics</text>
  <!-- stores -->
  <g font-size="16" fill="#fff">
    <rect x="1060" y="44" width="250" height="56" fill="#0D0D0D" stroke="#D6D6D6"/><text x="1076" y="78">Loki</text><text x="1160" y="78" font-size="12" fill="#707070">LOGS</text>
    <rect x="1060" y="122" width="250" height="56" fill="#0D0D0D" stroke="#D6D6D6"/><text x="1076" y="156">Tempo</text><text x="1160" y="156" font-size="12" fill="#707070">TRACES</text>
    <rect x="1060" y="200" width="250" height="56" fill="#0D0D0D" stroke="#D6D6D6"/><text x="1076" y="234">Prometheus</text><text x="1200" y="234" font-size="12" fill="#707070">METRICS</text>
  </g>
  <path fill="none" d="M980 72 L1060 72" stroke="#D6D6D6" stroke-width="2" marker-end="url(#a)"/>
  <path fill="none" d="M980 150 L1060 150" stroke="#D6D6D6" stroke-width="2" marker-end="url(#a)"/>
  <path fill="none" d="M980 228 L1060 228" stroke="#D6D6D6" stroke-width="2" marker-end="url(#a)"/>
  <!-- tempo -> prometheus metrics generator -->
  <path fill="none" d="M1300 178 Q1340 190 1300 200" stroke="#707070" stroke-width="2" fill="none" stroke-dasharray="4 4" marker-end="url(#a)"/>
  <text x="1318" y="194" font-size="11" fill="#707070">RED</text>
  <!-- prometheus scrape infra -->
  <path fill="none" d="M1185 256 L1185 299 L410 299" stroke="#D6D6D6" stroke-width="2" stroke-dasharray="6 5" marker-end="url(#a)"/>
  <text x="700" y="292" font-size="12" fill="#D6D6D6">scrape (pull)</text>
  <!-- grafana -->
  <rect x="1400" y="44" width="180" height="212" fill="#FFB400"/>
  <text x="1418" y="80" font-size="20" font-weight="600" font-family="Inter" fill="#000">Grafana</text>
  <g font-size="12" fill="#000"><text x="1418" y="110">metric → exemplar</text><text x="1418" y="132">→ trace</text><text x="1418" y="154">→ logs (trace_id)</text><text x="1418" y="190">samma tidsaxel</text><text x="1418" y="210">samma service.name</text></g>
  <path fill="none" d="M1310 72 L1400 72" stroke="#D6D6D6" stroke-width="2" marker-end="url(#a)"/>
  <path fill="none" d="M1310 150 L1400 150" stroke="#D6D6D6" stroke-width="2" marker-end="url(#a)"/>
  <path fill="none" d="M1310 228 L1400 228" stroke="#D6D6D6" stroke-width="2" marker-end="url(#a)"/>
</svg>
</div>
"""


def build_flow():
    p = []
    p.append(text("", (0, 0, 24, 10), FLOW_SVG, mode="html", transparent=True))

    y = 10
    p.append(row("① Källor – vem skickar vad? (push)", y)); y += 1
    p.append(table(
        "Push-tjänster: telemetri per service.name", (0, y, 14, 8),
        [
            {**prom('sum by (service) (rate(traces_spanmetrics_calls_total[2m]))', ref="A", instant=True, fmt="table")},
            {**prom('count by (service_name) ({service_name=~".+", job!~"llm-server|qdrant|postgresql"})', ref="B", instant=True, fmt="table")},
            {**loki('sum by (service_name) (rate({service_name=~".+"}[2m]))', ref="C", instant=True)},
        ],
        desc="Spans/s (Tempo span-metrics), aktiva metric-serier (Prometheus) och loggrader/s (Loki) per tjänst. "
             "Alla tre går att ställa mot varandra tack vare samma service.name.",
        ds=MIXED,
        transformations=[
            {"id": "organize", "options": {"renameByName": {"service": "service_name"}}},
            {"id": "joinByField", "options": {"byField": "service_name", "mode": "outer"}},
            {"id": "organize", "options": {"excludeByName": {"Time": True, "Time 1": True, "Time 2": True, "Time 3": True},
                                           "renameByName": {"service_name": "Tjänst", "Value #A": "Spans/s",
                                                            "Value #B": "Metric-serier", "Value #C": "Loggrader/s"}}},
        ],
        overrides=[{"matcher": {"id": "byName", "options": "Spans/s"}, "properties": [{"id": "decimals", "value": 1}]},
                   {"matcher": {"id": "byName", "options": "Loggrader/s"}, "properties": [{"id": "decimals", "value": 1}]}],
        sort="Spans/s"))
    p.append(stat("Prometheus hämtar själv (pull)", (14, y, 5, 8),
                  [prom('max by (job) (up{service_name=""})', "{{job}}", instant=True)],
                  desc="Scrape-mål i prometheus.yml: infrastruktur-exporters och observability-stacken själv.",
                  mappings=UP_MAP, spark=False, text_mode="value_and_name", color_mode="background_solid",
                  th=thresholds((None, "#161616")), orientation="horizontal"))
    p.append(stat("Collectorn hämtar (pull)", (19, y, 5, 8),
                  [prom('max by (job) (up{service_name!=""})', "{{job}}", instant=True, ref="A"),
                   prom('clamp_max(sum(rate(otelcol_scraper_scraped_metric_points{receiver="postgresql"}[2m])) > bool 0, 1)', "postgres", instant=True, ref="B")],
                  desc="Tredjepart du inte äger: Collectorns prometheus- och postgresql-receivers hämtar och skickar sedan vidare som OTLP.",
                  mappings=UP_MAP, spark=False, text_mode="value_and_name", color_mode="background_solid",
                  th=thresholds((None, "#161616")), orientation="horizontal"))
    y += 8

    p.append(row("② OTel Collector – receive · process · export", y)); y += 1
    p.append(stat("In: spans/s", (0, y, 4, 4), [prom('sum(rate(otelcol_receiver_accepted_spans[1m]))')], unit="short", decimals=0))
    p.append(stat("In: metric points/s", (4, y, 4, 4), [prom('sum(rate(otelcol_receiver_accepted_metric_points[1m]))')], decimals=0))
    p.append(stat("In: loggrader/s", (8, y, 4, 4), [prom('sum(rate(otelcol_receiver_accepted_log_records[1m]))')], decimals=0))
    p.append(stat("Refused / failed", (12, y, 4, 4),
                  [prom('sum(rate(otelcol_receiver_refused_spans[1m])) + sum(rate(otelcol_receiver_refused_log_records[1m])) + sum(rate(otelcol_receiver_refused_metric_points[1m])) + sum(rate(otelcol_exporter_send_failed_spans[1m]) or vector(0))')],
                  desc="Ska vara 0. Blir den gul: Collectorn eller en backend orkar inte (memory_limiter backar av eller exporten misslyckas).",
                  th=thresholds((None, WH), (0.01, Y)), decimals=1))
    p.append(stat("Exporter-kö", (16, y, 4, 4), [prom('sum(otelcol_exporter_queue_size)')],
                  desc="Data som väntar på att skickas till Loki/Tempo/Prometheus. Växer den är en backend långsam.",
                  th=thresholds((None, WH), (100, Y))))
    p.append(stat("Collector-minne", (20, y, 4, 4), [prom('max(otelcol_process_memory_rss)')], unit="bytes"))
    y += 4
    p.append(timeseries("In per receiver", (0, y, 8, 8), [
        prom('sum by (receiver) (rate(otelcol_receiver_accepted_spans[1m]))', "spans · {{receiver}}", "A"),
        prom('sum by (receiver) (rate(otelcol_receiver_accepted_log_records[1m]))', "logs · {{receiver}}", "B"),
        prom('sum by (receiver) (rate(otelcol_receiver_accepted_metric_points[1m]))', "metrics · {{receiver}}", "C"),
    ], unit="short", desc="otlp = push från tjänsterna. prometheus/postgresql = pull som Collectorn gör själv.",
        overrides=[color_override("spans · otlp", Y, width=3), color_override("logs · otlp", WH),
                   color_override("metrics · otlp", G300), color_override("metrics · prometheus", G500, dash=True),
                   color_override("metrics · postgresql", G700, dash=True)]))
    p.append(timeseries("Processors: in → ut (det som försvinner är filtrerat/samplat)", (8, y, 8, 8), [
        prom('sum by (processor) (rate(otelcol_processor_incoming_items{processor=~"filter.*"}[1m]))', "in · {{processor}}", "A"),
        prom('sum by (processor) (rate(otelcol_processor_outgoing_items{processor=~"filter.*"}[1m]))', "ut · {{processor}}", "B"),
        prom('sum(rate({"otelcol_processor_filter_spans.filtered"}[1m]))', "bortfiltrerade spans (/health)", "C"),
        prom('sum(rate({"otelcol_processor_filter_logs.filtered"}[1m]))', "bortfiltrerade loggar (DEBUG)", "D"),
    ], desc="filter/noise tar bort health checks och DEBUG innan något lagras.",
        overrides=[color_override("bortfiltrerade spans (/health)", Y), color_override("bortfiltrerade loggar (DEBUG)", Y, dash=True),
                   color_override("in · filter/noise", G300), color_override("ut · filter/noise", WH, dash=True)]))
    p.append(timeseries("Tail sampling: beslut per policy", (16, y, 8, 8), [
        prom('sum by (policy) (rate(otelcol_processor_tail_sampling_count_traces_sampled{sampled="true"}[1m]))', "behåll · {{policy}}", "A"),
        prom('sum(rate(otelcol_processor_tail_sampling_global_count_traces_sampled{sampled="false"}[1m]))', "släng", "B"),
    ], desc="errors och slow behålls alltid. 'rest' styrs av TRACE_SAMPLING_PERCENT i .env (100 = allt). Prova 10.",
        overrides=[color_override("behåll · errors", Y, width=3), color_override("behåll · slow", Y, dash=True),
                   color_override("behåll · rest", G300), color_override("släng", G700)]))
    y += 8
    p.append(timeseries("Ut per exporter", (0, y, 12, 7), [
        prom('sum by (exporter) (rate(otelcol_exporter_sent_spans[1m]))', "spans → {{exporter}}", "A"),
        prom('sum by (exporter) (rate(otelcol_exporter_sent_log_records[1m]))', "logs → {{exporter}}", "B"),
        prom('sum by (exporter) (rate(otelcol_exporter_sent_metric_points[1m]))', "metrics → {{exporter}}", "C"),
    ], overrides=[color_override("spans → otlp_grpc/tempo", Y, width=3), color_override("logs → otlp_http/loki", WH),
                  color_override("metrics → otlp_http/prometheus", G300)]))
    p.append(timeseries("Batch-storlek (färre, större skrivningar)", (12, y, 12, 7), [
        prom('histogram_quantile(0.5, sum by (le) (rate(otelcol_processor_batch_batch_send_size_bucket[2m])))', "p50 items per batch", "A"),
        prom('sum(rate(otelcol_processor_batch_timeout_trigger_send[1m]))', "batchar skickade p.g.a. timeout /s", "B"),
    ], overrides=[color_override("p50 items per batch", WH), color_override("batchar skickade p.g.a. timeout /s", G500, dash=True)]))
    y += 7

    p.append(row("③ Lagring – Loki · Tempo · Prometheus tar emot", y)); y += 1
    p.append(stat("Loki: loggrader/s", (0, y, 4, 5), [prom('sum(rate(loki_distributor_lines_received_total[1m]))')], decimals=0))
    p.append(stat("Loki: bytes/s", (4, y, 4, 5), [prom('sum(rate(loki_distributor_bytes_received_total[1m]))')], unit="Bps"))
    p.append(stat("Tempo: spans/s", (8, y, 4, 5), [prom('sum(rate(tempo_distributor_spans_received_total[1m]))')], decimals=0))
    p.append(stat("Tempo: aktiva traces", (12, y, 4, 5), [prom('sum(tempo_ingester_live_traces)')]))
    p.append(stat("Prometheus: aktiva serier", (16, y, 4, 5), [prom('max(prometheus_tsdb_head_series)')],
                  desc="Antal tidsserier i minnet. Växer den okontrollerat: cardinality-problem (se dashboard 05).",
                  th=thresholds((None, WH), (50000, Y))))
    p.append(stat("Prometheus: samples/s", (20, y, 4, 5), [prom('sum(rate(prometheus_tsdb_head_samples_appended_total[1m]))')], decimals=0))
    y += 5
    p.append(timeseries("Mottaget per backend (samma tidsaxel)", (0, y, 24, 7), [
        prom('sum(rate(loki_distributor_lines_received_total[1m]))', "Loki · loggrader/s", "A"),
        prom('sum(rate(tempo_distributor_spans_received_total[1m]))', "Tempo · spans/s", "B"),
        prom('sum(rate(prometheus_tsdb_head_samples_appended_total[1m]))', "Prometheus · samples/s", "C"),
    ], overrides=[color_override("Tempo · spans/s", Y, width=3), color_override("Loki · loggrader/s", WH),
                  {**color_override("Prometheus · samples/s", G500, dash=True),
                   "properties": color_override("Prometheus · samples/s", G500, dash=True)["properties"] + [{"id": "custom.axisPlacement", "value": "right"}]}]))
    y += 7
    p.append(row("④ Grafana – nästa steg", y)); y += 1
    p.append(text("", (0, y, 24, 4), """
**Följ en request genom allt:** öppna **02 · Plattform · Översikt** → klicka på en **exemplar-punkt** (◆) i p95-grafen → tracen öppnas i Tempo → klicka **Logs for this span** → Loki visar loggarna för just det `trace_id`.

**Simulera incident:** knappen *slow* i chatt-UI:t (http://localhost:8080) eller `./scripts/incident.sh slow`. Se p95 och GPU gå upp, följ kedjan metrics → traces → logs.
""", transparent=True))
    return dashboard("telemetry-flow", "01 · Telemetriflödet", p,
                     desc="Hur telemetri flyttar sig: källor (push/pull) → OTel Collector → Loki/Tempo/Prometheus → Grafana")


# ---------------------------------------------------------------------------
# 02 · Plattform · Översikt – dashboarden från filmen
# ---------------------------------------------------------------------------
def build_overview():
    p = []
    y = 0
    p.append(stat("Requests/s", (0, y, 4, 4),
                  [prom('sum(rate(http_server_request_duration_seconds_count{service_name="frontend", http_route="/ask"}[1m]))')], decimals=1))
    p.append(stat("Felkvot", (4, y, 4, 4),
                  [prom('sum(rate(http_server_request_duration_seconds_count{service_name="frontend", http_route="/ask", http_response_status_code=~"5.."}[1m])) / sum(rate(http_server_request_duration_seconds_count{service_name="frontend", http_route="/ask"}[1m]))')],
                  unit="percentunit", decimals=1, th=thresholds((None, WH), (0.02, Y))))
    p.append(stat("p95 · användarens väntetid", (8, y, 4, 4),
                  [prom('histogram_quantile(0.95, sum by (le) (rate(http_server_request_duration_seconds_bucket{service_name="frontend", http_route="/ask"}[1m])))')],
                  unit="s", decimals=2, th=thresholds((None, WH), (2, Y))))
    p.append(stat("LLM-omförsök/min", (12, y, 4, 4), [prom('sum(rate(gen_ai_client_retries_total[1m])) * 60 or vector(0)')],
                  decimals=0, th=thresholds((None, WH), (1, Y))))
    p.append(stat("GPU", (16, y, 4, 4), [prom('avg(DCGM_FI_DEV_GPU_UTIL)')], unit="percent", decimals=0,
                  th=thresholds((None, WH), (90, Y))))
    p.append(stat("Unified memory", (20, y, 4, 4), [prom('sum(DCGM_FI_DEV_FB_USED) * 1024 * 1024')], unit="bytes", decimals=0,
                  desc="av 128 GB (DGX Spark delar minne mellan CPU och GPU)",
                  th=thresholds((None, WH), (120 * 1024 ** 3, Y))))
    y += 4
    p.append(timeseries("Request p95 · per tjänst", (0, y, 12, 9), [prom(P95, "{{service_name}}", exemplar=True)], unit="s",
                        desc="METRICS svarar på: är något fel? ◆ = exemplar – klicka för att öppna exakt den trace som gav värdet.",
                        overrides=service_overrides(), th=thresholds((None, "transparent"), (2, Y)), th_style="dashed"))
    p.append(timeseries("DGX Spark · GPU & minne", (12, y, 12, 9), [
        prom('avg(DCGM_FI_DEV_GPU_UTIL)', "GPU", "A"),
        prom('100 * sum(DCGM_FI_DEV_FB_USED) / (sum(DCGM_FI_DEV_FB_USED) + sum(DCGM_FI_DEV_FB_FREE))', "unified mem", "B"),
        prom('100 * avg(vllm:kv_cache_usage_perc)', "vLLM KV-cache", "C"),
    ], unit="percent", max_=100, desc="Samma tidsaxel som p95: slår GPU:n i taket minuten innan latensen stiger?",
        overrides=[color_override("GPU", Y, width=3), color_override("unified mem", G300, dash=True), color_override("vLLM KV-cache", G500)]))
    y += 9
    p.append(panel("nodeGraph", "Service graph · Tempo (från traces)", (0, y, 12, 11),
                   [{"datasource": TEMPO, "refId": "A", "queryType": "serviceMap", "serviceMapIncludeNamespace": False}],
                   desc="Byggs automatiskt av Tempos metrics-generator ur spans. llm, qdrant och postgres är 'virtuella noder' – de skickar inga egna traces.",
                   ds=TEMPO, options={}))
    p.append(panel("table", "Långsamma requests (> 1 s) · klicka för trace", (12, y, 12, 11),
                   [{"datasource": TEMPO, "refId": "A", "queryType": "traceql", "limit": 20, "tableType": "traces",
                     "query": '{ resource.service.name = "frontend" && kind = server && duration > 1s }'}],
                   desc="TRACES svarar på: var händer det? Öppna en trace och se vilken span som tar tiden.",
                   ds=TEMPO, options={"showHeader": True, "cellHeight": "sm"},
                   fieldConfig={"defaults": {"custom": {"align": "auto"}}, "overrides": []}))
    y += 11
    p.append(logs("WARN & ERROR · alla tjänster", (0, y, 12, 10),
                  '{deployment_environment_name="demo"} | detected_level=~"warn|warning|error"',
                  desc="LOGS svarar på: vad exakt hände? Expandera en rad → 'Öppna trace' via trace_id."))
    p.append(logs("Loggar för trace_id = $trace_id", (12, y, 12, 10),
                  '{deployment_environment_name="demo"} | trace_id!="" | trace_id="$trace_id"',
                  desc="Klistra in ett trace_id i variabeln högst upp (eller klicka 'Logs for this span' i en trace)."))
    variables = [{"type": "textbox", "name": "trace_id", "label": "trace_id", "query": "", "current": {"value": ""},
                  "hide": 0, "options": []}]
    return dashboard("platform-overview", "02 · Plattform · Översikt", p, variables=variables,
                     desc="Metrics → traces → logs på samma tidsaxel, ner till GPU:n")


# ---------------------------------------------------------------------------
# 03 · AI · RAG & LLM
# ---------------------------------------------------------------------------
def build_ai():
    p = []
    y = 0
    p.append(stat("RAG-förfrågningar/s", (0, y, 4, 4), [prom('sum(rate(rag_requests_total[1m]))')], decimals=1))
    p.append(stat("LLM p95 (klientens vy)", (4, y, 4, 4),
                  [prom('histogram_quantile(0.95, sum by (le) (rate(gen_ai_client_operation_duration_seconds_bucket[1m])))')],
                  unit="s", decimals=2, th=thresholds((None, WH), (2, Y))))
    p.append(stat("Time to first token p95", (8, y, 4, 4),
                  [prom('histogram_quantile(0.95, sum by (le) (rate({"vllm:time_to_first_token_seconds_bucket"}[1m])))')],
                  unit="s", decimals=2, th=thresholds((None, WH), (1, Y))))
    p.append(stat("Genererade tokens/s", (12, y, 4, 4), [prom('sum(rate({"vllm:generation_tokens_total"}[1m]))')], decimals=0))
    p.append(stat("LLM-fel", (16, y, 4, 4), [prom('sum(rate(rag_requests_total{outcome!="ok"}[1m])) / sum(rate(rag_requests_total[1m]))')],
                  unit="percentunit", decimals=1, th=thresholds((None, WH), (0.02, Y))))
    p.append(stat("KV-cache", (20, y, 4, 4), [prom('100 * avg({"vllm:kv_cache_usage_perc"})')], unit="percent", decimals=0,
                  th=thresholds((None, WH), (85, Y))))
    y += 4
    p.append(timeseries("Var i AI-flödet går tiden? p95 per steg (från spans)", (0, y, 12, 9), [
        prom('histogram_quantile(0.95, sum by (le, span_name) (rate(traces_spanmetrics_latency_bucket{service="ai-chat", span_name=~"rag.*|chat .*"}[1m])))', "{{span_name}}"),
    ], unit="s", desc="Tempo span-metrics ur de MANUELLA spans i ai-chat. Här syns varför egna spans runt varje AI-steg lönar sig.",
        overrides=[color_override("chat local-model", Y, width=3), color_override("rag.pipeline", WH),
                   color_override("rag.retrieve", G300), color_override("rag.rerank", G500, dash=True), color_override("rag.embed", G700)]))
    p.append(timeseries("LLM-latens: klient vs server", (12, y, 12, 9), [
        prom('histogram_quantile(0.95, sum by (le) (rate(gen_ai_client_operation_duration_seconds_bucket[1m])))', "ai-chat ser (inkl. omförsök) p95", "A"),
        prom('histogram_quantile(0.95, sum by (le) (rate({"vllm:e2e_request_latency_seconds_bucket"}[1m])))', "vLLM e2e p95", "B"),
        prom('histogram_quantile(0.95, sum by (le) (rate({"vllm:time_to_first_token_seconds_bucket"}[1m])))', "vLLM time to first token p95", "C"),
    ], unit="s", desc="Push (ai-chat, OTel SDK) mot pull (vLLM:s egna /metrics). Skillnaden = nätverk + kö + omförsök.",
        overrides=[color_override("ai-chat ser (inkl. omförsök) p95", Y, width=3), color_override("vLLM e2e p95", WH),
                   color_override("vLLM time to first token p95", G500, dash=True)]))
    y += 9
    p.append(timeseries("Omförsök & fel mot LLM", (0, y, 8, 8), [
        prom('sum by (error_type) (rate(gen_ai_client_retries_total[1m])) * 60', "omförsök/min · {{error_type}}", "A"),
        prom('sum by (outcome) (rate(rag_requests_total{outcome!="ok"}[1m])) * 60', "misslyckade/min · {{outcome}}", "B"),
    ], overrides=[color_override("omförsök/min · timeout", Y, width=3)]))
    p.append(timeseries("vLLM: kö och körning", (8, y, 8, 8), [
        prom('sum({"vllm:num_requests_running"})', "running", "A"),
        prom('sum({"vllm:num_requests_waiting"})', "waiting", "B"),
    ], overrides=[color_override("running", WH), color_override("waiting", Y)]))
    p.append(timeseries("Tokens/s", (16, y, 8, 8), [
        prom('sum(rate({"vllm:prompt_tokens_total"}[1m]))', "prompt (in)", "A"),
        prom('sum(rate({"vllm:generation_tokens_total"}[1m]))', "generation (ut)", "B"),
    ], overrides=[color_override("prompt (in)", G300, dash=True), color_override("generation (ut)", Y)]))
    y += 8
    p.append(timeseries("Retrieval (Qdrant) p95", (0, y, 8, 8), [
        prom('histogram_quantile(0.95, sum by (le) (rate(rag_retrieval_duration_seconds_bucket[1m])))', "ai-chat: rag.retrieval.duration", "A"),
    ], unit="s", color=WH))
    p.append(timeseries("Dokument efter rerank (medel)", (8, y, 8, 8), [
        prom('sum(rate(rag_documents_retrieved_sum[1m])) / sum(rate(rag_documents_retrieved_count[1m]))', "dokument", "A"),
    ], color=G300, decimals=1))
    p.append(timeseries("GPU (samma tidsaxel)", (16, y, 8, 8), [prom('avg(DCGM_FI_DEV_GPU_UTIL)', "GPU %")], unit="percent", max_=100,
                        color=Y, th=thresholds((None, "transparent"), (90, Y)), th_style="dashed"))
    y += 8
    p.append(logs("ai-chat · loggar (retrieval, retry, fel)", (0, y, 24, 9), '{service_name="ai-chat"} |~ "retry|failed|retrieval_done"'))
    return dashboard("ai-rag-llm", "03 · AI · RAG & LLM", p, desc="RAG-pipelinen steg för steg och LLM-servern (vLLM) under den")


# ---------------------------------------------------------------------------
# 04 · Infrastruktur · DGX Spark & containers
# ---------------------------------------------------------------------------
def build_infra():
    p = []
    y = 0
    cpu = '100 * (1 - avg(rate(node_cpu_seconds_total{mode="idle"}[1m])))'
    mem = '100 * (1 - sum(node_memory_MemAvailable_bytes) / sum(node_memory_MemTotal_bytes))'
    disk = '100 * (1 - max(node_filesystem_avail_bytes{mountpoint="/"}) / max(node_filesystem_size_bytes{mountpoint="/"}))'
    p.append(stat("CPU", (0, y, 4, 4), [prom(cpu)], unit="percent", decimals=0, th=thresholds((None, WH), (85, Y))))
    p.append(stat("Minne (värd)", (4, y, 4, 4), [prom(mem)], unit="percent", decimals=0, th=thresholds((None, WH), (90, Y))))
    p.append(stat("Disk /", (8, y, 4, 4), [prom(disk)], unit="percent", decimals=0, th=thresholds((None, WH), (85, Y))))
    p.append(stat("GPU", (12, y, 4, 4), [prom('avg(DCGM_FI_DEV_GPU_UTIL)')], unit="percent", decimals=0, th=thresholds((None, WH), (90, Y))))
    p.append(stat("GPU-temp", (16, y, 4, 4), [prom('max(DCGM_FI_DEV_GPU_TEMP)')], unit="celsius", decimals=0, th=thresholds((None, WH), (80, Y))))
    p.append(stat("GPU-effekt", (20, y, 4, 4), [prom('sum(DCGM_FI_DEV_POWER_USAGE)')], unit="watt", decimals=0))
    y += 4
    p.append(row("Värdmaskinen · node-exporter (pull)", y)); y += 1
    p.append(timeseries("CPU per läge", (0, y, 8, 8), [
        prom('100 * sum by (mode) (rate(node_cpu_seconds_total{mode=~"user|system|iowait"}[1m])) / scalar(count(count by (cpu) (node_cpu_seconds_total)))', "{{mode}}")],
        unit="percent", stack=True, fill=40, overrides=[color_override("user", WH), color_override("system", G500), color_override("iowait", Y)]))
    p.append(timeseries("Minne", (8, y, 8, 8), [
        prom('sum(node_memory_MemTotal_bytes) - sum(node_memory_MemAvailable_bytes)', "använt", "A"),
        prom('sum(node_memory_MemTotal_bytes)', "totalt", "B")],
        unit="bytes", overrides=[color_override("använt", WH), color_override("totalt", G700, dash=True)]))
    p.append(timeseries("Nätverk", (16, y, 8, 8), [
        prom('sum(rate(node_network_receive_bytes_total{device!~"lo|veth.*|docker.*|br-.*"}[1m]))', "rx", "A"),
        prom('-sum(rate(node_network_transmit_bytes_total{device!~"lo|veth.*|docker.*|br-.*"}[1m]))', "tx", "B")],
        unit="Bps", overrides=[color_override("rx", WH), color_override("tx", G500)]))
    y += 8
    p.append(row("GPU · dcgm-exporter (pull)", y)); y += 1
    p.append(timeseries("GPU-utnyttjande", (0, y, 8, 8), [prom('avg by (gpu) (DCGM_FI_DEV_GPU_UTIL)', "gpu {{gpu}}")], unit="percent", max_=100,
                        color=Y, fill=15, th=thresholds((None, "transparent"), (90, Y)), th_style="dashed"))
    p.append(timeseries("GPU-minne", (8, y, 8, 8), [
        prom('sum(DCGM_FI_DEV_FB_USED) * 1024 * 1024', "använt", "A"),
        prom('(sum(DCGM_FI_DEV_FB_USED) + sum(DCGM_FI_DEV_FB_FREE)) * 1024 * 1024', "totalt", "B")],
        unit="bytes", overrides=[color_override("använt", WH), color_override("totalt", G700, dash=True)]))
    p.append(timeseries("Temperatur & effekt", (16, y, 8, 8), [
        prom('max(DCGM_FI_DEV_GPU_TEMP)', "°C", "A"), prom('sum(DCGM_FI_DEV_POWER_USAGE)', "W", "B")],
        overrides=[color_override("°C", WH), color_override("W", G500, dash=True)]))
    y += 8
    p.append(row("Containers · cAdvisor (pull)", y)); y += 1
    svc = 'container_label_com_docker_compose_service'
    p.append(timeseries("CPU per container", (0, y, 12, 9), [
        prom(f'sum by ({svc}) (rate(container_cpu_usage_seconds_total{{{svc}!=""}}[1m]))', f"{{{{{svc}}}}}")],
        unit="percentunit", desc="1.0 = en hel CPU-kärna. Ingen data? cAdvisor behöver cgroup v2 och Docker-socket (se docs/).",
        overrides=[color_override(n, c) for n, c in SERVICE_COLORS.items()]))
    p.append(timeseries("Minne per container", (12, y, 12, 9), [
        prom(f'sum by ({svc}) (container_memory_working_set_bytes{{{svc}!=""}})', f"{{{{{svc}}}}}")],
        unit="bytes", overrides=[color_override(n, c) for n, c in SERVICE_COLORS.items()]))
    y += 9
    p.append(row("Runtime per tjänst · OTel SDK (push)", y)); y += 1
    p.append(timeseries(".NET: working set", (0, y, 8, 8), [prom('sum by (service_name) (dotnet_process_memory_working_set_bytes)', "{{service_name}}")],
                        unit="bytes", overrides=service_overrides()))
    p.append(timeseries(".NET: GC-paus", (8, y, 8, 8), [prom('sum by (service_name) (rate(dotnet_gc_pause_time_seconds_total[1m]))', "{{service_name}}")],
                        unit="percentunit", overrides=service_overrides()))
    p.append(timeseries("Postgres (Collectorn hämtar)", (16, y, 8, 8), [
        prom('sum(rate(postgresql_commits_total[1m]))', "commits/s", "A"),
        prom('sum(postgresql_backends)', "anslutningar", "B")],
        overrides=[color_override("commits/s", WH), color_override("anslutningar", G500, dash=True)]))
    return dashboard("infra-dgx", "04 · Infrastruktur · DGX Spark & containers", p,
                     desc="Hårdvara, GPU och containers – samma tidsaxel som applikationen")


# ---------------------------------------------------------------------------
# 05 · Cardinality & telemetrikostnad
# ---------------------------------------------------------------------------
def build_cardinality():
    p = []
    y = 0
    p.append(stat("Aktiva serier", (0, y, 6, 4), [prom('max(prometheus_tsdb_head_series)')], th=thresholds((None, WH), (50000, Y))))
    p.append(stat("app_ask_requests_total · serier", (6, y, 6, 4), [prom('count(app_ask_requests_total)')],
                  desc="Sätt BAD_CARDINALITY=true i .env och starta om backend. Varje user_id × request_id blir en ny serie.",
                  th=thresholds((None, WH), (100, Y))))
    p.append(stat("Loki · bytes/s", (12, y, 6, 4), [prom('sum(rate(loki_distributor_bytes_received_total[1m]))')], unit="Bps"))
    p.append(stat("Tempo · bytes/s", (18, y, 6, 4), [prom('sum(rate(tempo_distributor_bytes_received_total[1m]))')], unit="Bps"))
    y += 4
    p.append(timeseries("app_ask_requests_total · antal serier över tid", (0, y, 12, 8), [prom('count(app_ask_requests_total)', "serier")],
                        color=Y, fill=15, desc="Bra labels: app_intent, outcome (få, stabila värden). Dåliga: user_id, request_id, filename."))
    p.append(text("Tumregler", (12, y, 12, 8), """
| Hör hemma i… | Exempel |
|---|---|
| **Metric-labels** (få, stabila) | `service_name`, `http_route`, `http_response_status_code`, `app_intent` |
| **Trace-attribut** (unika id:n) | `user.id`, `request.id`, `gen_ai.usage.*`, `rag.top_k` |
| **Loggar** (detaljer) | felmeddelanden, `attempt=2 reason=timeout` |

Unika värden som label ger en ny tidsserie per värde → minne, disk och långsamma frågor i Prometheus.
""", transparent=False))
    y += 8
    p.append(table("Topp 15 metrics efter antal serier", (0, y, 8, 11),
                   [prom('topk(15, count by (__name__) ({__name__=~".+"}))', instant=True, fmt="table")],
                   transformations=[{"id": "organize", "options": {"excludeByName": {"Time": True},
                                                                  "renameByName": {"__name__": "Metric", "Value": "Serier"}}}],
                   sort="Serier"))
    p.append(table("Serier per tjänst (service_name)", (8, y, 8, 11),
                   [prom('sort_desc(count by (service_name) ({service_name!=""}))', instant=True, fmt="table")],
                   transformations=[{"id": "organize", "options": {"excludeByName": {"Time": True},
                                                                  "renameByName": {"service_name": "Tjänst", "Value": "Serier"}}}],
                   sort="Serier"))
    p.append(timeseries("Loggvolym per tjänst", (16, y, 8, 11), [loki('sum by (service_name) (bytes_rate({service_name=~".+"}[1m]))', "{{service_name}}")],
                        unit="Bps", ds=LOKI, stack=True, fill=40, overrides=service_overrides()))
    y += 11
    p.append(timeseries("Spans/s per tjänst (Tempo span-metrics)", (0, y, 24, 8),
                        [prom('sum by (service) (rate(traces_spanmetrics_calls_total[1m]))', "{{service}}")],
                        stack=True, fill=40, overrides=service_overrides()))
    return dashboard("cardinality-cost", "05 · Cardinality & kostnad", p,
                     desc="Mer telemetri är inte alltid bättre: serier, bytes och spans per tjänst")


if __name__ == "__main__":
    write("01-telemetry-flow.json", build_flow())
    write("02-platform-overview.json", build_overview())
    write("03-ai-rag-llm.json", build_ai())
    write("04-infra-dgx.json", build_infra())
    write("05-cardinality-cost.json", build_cardinality())
