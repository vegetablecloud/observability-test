"""
09 · Cardinality & kostnad – mer telemetri är inte alltid bättre.
Svarar på: "Vad kostar vår telemetri, och vem står för det?"
"""

from dashlib import (ACCENT, WHITE, Board, field_override, loki, organize, prom, service_overrides, stat, table, text, thresholds,
                     timeseries)

RULES = """
| Hör hemma i… | Exempel |
|---|---|
| **Metric-labels** (få, stabila) | `service_name`, `http_route`, `langgraph_node`, `gen_ai_tool_name`, `outcome` |
| **Trace-attribut** (unika id:n) | `user.id`, `gen_ai.conversation.id`, `test.run.id`, `gen_ai.tool.call.arguments` |
| **Loggar** (detaljer) | felmeddelanden, `attempt=2 reason=timeout`, `node_done node=agent step=2` |

Unika värden som label ger en ny tidsserie per värde → minne, disk och långsamma frågor i Prometheus.
"""


def build():
    b = Board("cardinality-cost", "09 · Cardinality & kostnad", "Vad kostar vår telemetri, och vem står för det?", tags=["plattform"])
    b.add(stat("Aktiva serier", [prom("max(prometheus_tsdb_head_series)")], th=thresholds((None, WHITE), (50000, ACCENT)),
               desc="Tidsserier i Prometheus minne. Den viktigaste kostnadssiffran för metrics."), w=6, h=4)
    b.add(stat("app_ask_requests_total · serier", [prom("count(app_ask_requests_total)")], th=thresholds((None, WHITE), (100, ACCENT)),
               desc="Sätt BAD_CARDINALITY=true i .env och starta om backend. Varje user_id × request_id blir en ny serie."), w=6, h=4)
    b.add(stat("Loki · bytes/s", [prom("sum(rate(loki_distributor_bytes_received_total[1m]))")], unit="Bps",
               desc="Loggvolym in. Loggar kostar per byte."), w=6, h=4)
    b.add(stat("Tempo · bytes/s", [prom("sum(rate(tempo_distributor_bytes_received_total[1m]))")], unit="Bps",
               desc="Trace-volym in, efter tail sampling. Innehåll på spans (prompter, svar) syns här."), w=6, h=4)
    b.add(timeseries("app_ask_requests_total · antal serier över tid", [prom("count(app_ask_requests_total)", "serier")], color=ACCENT, fill=15,
                     desc="Bra labels: app_intent, outcome (få, stabila värden). Dåliga: user_id, request_id, filename."), w=12, h=8)
    b.add(text(RULES, title="Tumregler", transparent=False), w=12, h=8)
    b.add(table("Topp 15 metrics efter antal serier", [prom('topk(15, count by (__name__) ({__name__=~".+"}))', instant=True, fmt="table")],
                transformations=[organize(exclude=["Time"], rename={"__name__": "Metric", "Value": "Serier"})], sort="Serier",
                overrides=[field_override("Serier", decimals=0)], desc="Vilka metrics står för flest serier? Börja optimera överst."),
          w=8, h=11)
    b.add(table("Serier per tjänst", [prom('sort_desc(count by (service_name) ({service_name!=""}))', instant=True, fmt="table")],
                transformations=[organize(exclude=["Time"], rename={"service_name": "Tjänst", "Value": "Serier"})], sort="Serier",
                overrides=[field_override("Serier", decimals=0)], desc="Vilken tjänst skickar flest serier?"), w=8, h=11)
    b.add(timeseries("Loggvolym per tjänst", [loki('sum by (service_name) (bytes_rate({service_name=~".+"}[1m]))', "{{service_name}}")],
                     unit="Bps", stack=True, fill=40, overrides=service_overrides(), desc="Bytes per sekund loggar per tjänst."), w=8, h=11)
    b.add(timeseries("Spans / s per tjänst · Tempo span-metrics", [prom("sum by (service) (rate(traces_spanmetrics_calls_total[1m]))", "{{service}}")],
                     stack=True, fill=40, overrides=service_overrides(),
                     desc="ai-chat skickar flest spans: en per nod, LLM-anrop och verktyg. Värt det – men sampla resten om volymen blir för stor."),
          w=24, h=8)
    return b
