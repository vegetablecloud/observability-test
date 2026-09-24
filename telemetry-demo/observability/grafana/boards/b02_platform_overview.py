"""
02 · Plattform · Översikt – dashboarden från filmen.
Svarar på: "Är något fel, var, och vad exakt?" – metrics → traces → logs på samma tidsaxel.

  ① RED per tjänst     requests/s, fel och p95 för varje tjänst (med exemplars: klick -> trace)
  ② Orsak bredvid verkan   p95 per tjänst bredvid GPU och modellernas köer
  ③ Var                service graph + långsamma requests (TraceQL)
  ④ Vad                WARN/ERROR från alla tjänster
"""

from dashlib import (ACCENT, G300, G500, WHITE, Board, bargauge, color_override, logs, prom, service_map, service_overrides, stat,
                     node_graph, table, tempo_columns, thresholds, timeseries, traceql)
from dashlib import queries as Q


def build():
    b = Board("platform-overview", "02 · Plattform · Översikt", "Är något fel, var, och vad exakt? Metrics → traces → logs på samma tidsaxel",
              tags=["plattform"])
    b.add(stat("Frågor / s", [prom(Q.ASK_RATE)], decimals=1, desc="Användarnas frågor till frontend /ask."), w=4, h=4)
    b.add(stat("Felkvot", [prom(Q.ASK_ERR_RATIO)], unit="percentunit", decimals=1, th=thresholds((None, WHITE), (0.02, ACCENT)),
               desc="Andel frågor som gav 5xx, senaste 5 min. Gul över 2 %."), w=4, h=4)
    b.add(stat("p95 · användarens väntetid", [prom(Q.ASK_P95)], unit="s", th=thresholds((None, WHITE), (3, ACCENT)),
               desc="Tiden användaren väntar på svar (frontend /ask). Gul över 3 s."), w=4, h=4)
    b.add(stat("LLM-omförsök / min", [prom('sum(rate(gen_ai_client_operation_duration_seconds_count{service_name="ai-chat", error_type!=""}[1m])) * 60 or vector(0)')],
               decimals=0, th=thresholds((None, WHITE), (1, ACCENT)),
               desc="LLM-anrop från agenten som slutade i fel (timeout, 500). Över 0: titta på 04 · LLM & RAG."), w=4, h=4)
    b.add(stat("GPU", [prom("avg(DCGM_FI_DEV_GPU_UTIL)")], unit="percent", decimals=0, th=thresholds((None, WHITE), (90, ACCENT)),
               desc="GPU-utnyttjande på DGX Spark."), w=4, h=4)
    b.add(stat("Unified memory", [prom("sum(DCGM_FI_DEV_FB_USED) * 1024 * 1024")], unit="bytes", decimals=0,
               th=thresholds((None, WHITE), (120 * 1024 ** 3, ACCENT)),
               desc="Använt av 128 GB (DGX Spark delar minne mellan CPU och GPU)."), w=4, h=4)

    b.row("① RED per tjänst · rate, errors, duration")
    b.add(timeseries("Requests / s per tjänst", [prom(Q.rate_by_service(), "{{service}}")], overrides=service_overrides(),
                     desc="Server-spans per tjänst (Tempo span-metrics). Alla tjänster bör följa samma kurva som frontend."), w=8, h=8)
    b.add(bargauge("Felkvot per tjänst · 2 min", [prom(Q.error_ratio_by_service(), "{{service}}", instant=True)], unit="percentunit",
                   decimals=1, max_=0.2, th=thresholds((None, G500), (0.02, ACCENT)), mode="basic",
                   desc="Andel server-spans med status ERROR. Gul över 2 %. Tjänsten längst upp med gult är oftast där felet börjar."),
          w=4, h=8)
    b.add(timeseries("Request p95 · per tjänst", [prom(Q.P95_BY_SERVICE, "{{service_name}}", exemplar=True)], unit="s",
                     overrides=service_overrides(), th=thresholds((None, "transparent"), (3, ACCENT)), th_style="dashed",
                     desc="METRICS svarar på: är något fel? ◆ = exemplar – klicka för att öppna exakt den trace som gav värdet."),
          w=12, h=8)

    b.row("② Orsak bredvid verkan · samma tidsaxel")
    b.add(timeseries("DGX Spark · GPU, minne och KV-cache", [
        prom("avg(DCGM_FI_DEV_GPU_UTIL)", "GPU"),
        prom("100 * sum(DCGM_FI_DEV_FB_USED) / (sum(DCGM_FI_DEV_FB_USED) + sum(DCGM_FI_DEV_FB_FREE))", "unified mem"),
        prom('100 * avg({"vllm:kv_cache_usage_perc", model_name="gemma"})', "gemma KV-cache")],
        unit="percent", max_=100,
        overrides=[color_override("GPU", ACCENT, width=3), color_override("unified mem", G300, dash=True), color_override("gemma KV-cache", G500)],
        desc="Slår GPU:n i taket minuten innan latensen i ① stiger? Då är det modellen, inte koden."), w=12, h=8)
    b.add(timeseries("Modellernas köer", [
        prom('sum by (model_name) (avg_over_time({"vllm:num_requests_waiting"}[1m]))', "väntar · {{model_name}}"),
        prom('sum by (model_name) (avg_over_time({"vllm:num_requests_running"}[1m]))', "körs · {{model_name}}")],
        overrides=[color_override("väntar · gemma", ACCENT, width=3), color_override("körs · gemma", WHITE),
                   color_override("väntar · harrier", ACCENT, dash=True), color_override("körs · harrier", G500, dash=True)],
        desc="Requests som köar i vLLM. Växande kö = modellen hinner inte med, oavsett hur snabb resten av stacken är."), w=12, h=8)

    b.row("③ Var händer det? · traces")
    b.add(node_graph("Service graph · ur traces", [service_map()],
                     desc="Byggs automatiskt av Tempos metrics-generator ur spans. vLLM och databaserna är 'virtuella noder': "
                     "de skickar inga egna traces, men syns ändå via anroparnas client-spans."), w=12, h=12)
    b.add(table("Långsamma frågor (> 2 s) · klicka för trace", [traceql(
        '{ resource.service.name = "frontend" && kind = server && duration > 2s } | select(span.http.response.status_code)', limit=20, table="spans")],
        transformations=[tempo_columns({"http.response.status_code": "Status"}, hide=["Name", "traceIdHidden"])],
        desc="TRACES svarar på: var händer det? Öppna en trace och se vilken span som tar tiden."), w=12, h=12)

    b.row("④ Vad exakt hände? · logs")
    b.add(logs("WARN & ERROR · alla tjänster", '{deployment_environment_name="demo"} | detected_level=~"warn|warning|error"',
               desc="LOGS svarar på: vad exakt hände? Expandera en rad → 'Öppna trace' via trace_id."), w=24, h=10)
    return b
