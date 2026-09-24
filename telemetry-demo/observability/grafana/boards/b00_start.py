"""
00 · Start – plattformens framsida. Svarar på: "Mår allt bra just nu, och vart går jag härnäst?"

Uppifrån och ned:
  1. Status för VARJE komponent (OK / STÖRD / NERE) – tre rutnät: app, AI & data, plattform
  2. De fem siffror alla bryr sig om (lyckade frågor, väntetid, agenten, verktygen, GPU)
  3. Klickbar arkitekturkarta – varje ruta leder till sin dashboard
  4. Vem är du? Genvägar per roll
  5. Senaste felen, från alla tjänster, med länk till trace
"""

from dashlib import (ACCENT, STATUS_MAP, TILE, WHITE, Board, logs, prom, stat, text, thresholds)
from dashlib import queries as Q
from dashlib.diagram import Box, Edge, svg_map

BOXES = [
    Box("user", 20, 150, "användare", "UI · loadgen · e2e", w=150),
    Box("frontend", 200, 150, "frontend", "C# · UI / BFF", link="/d/platform-overview"),
    Box("backend", 410, 150, "backend", "C# · affärslogik", link="/d/platform-overview"),
    Box("postgres", 410, 40, "postgres", "app-databas", link="/d/databases", dashed=True),
    Box("ai-chat", 620, 150, "ai-chat", "LangGraph-agent", link="/d/ai-agent", accent=True),
    Box("algorithm", 620, 40, "algorithm", "förberäknade svar", link="/d/ai-agent"),
    Box("rag-api", 620, 270, "rag-api", "hybrid-sökning", link="/d/llm-rag"),
    Box("vllm-gemma", 850, 150, "vllm · gemma", "chat + tool calling", link="/d/llm-rag", dashed=True),
    Box("vllm-embed", 850, 270, "vllm · harrier", "embeddings", link="/d/llm-rag", dashed=True),
    Box("paradedb", 850, 370, "paradedb", "BM25 + pgvector", link="/d/databases", dashed=True),
    Box("collector", 1100, 90, "OTel Collector", "receive·process·export", link="/d/telemetry-flow", h=200, w=190),
    Box("loki", 1330, 60, "loki", "logs", link="/d/telemetry-flow", w=110, h=50),
    Box("tempo", 1330, 165, "tempo", "traces", link="/d/telemetry-flow", w=110, h=50),
    Box("prometheus", 1330, 270, "prometheus", "metrics", link="/d/telemetry-flow", w=110, h=50),
    Box("grafana", 1470, 150, "grafana", "du är här", w=110, h=80, accent=True),
    Box("dgx", 1100, 330, "DGX Spark", "CPU · GPU · minne · containrar", link="/d/infra-dgx", w=340, h=56, dashed=True),
]
EDGES = [
    Edge("user", "frontend"), Edge("frontend", "backend"), Edge("backend", "ai-chat"),
    Edge("backend", "postgres", kind="request"), Edge("ai-chat", "vllm-gemma", label="LLM"),
    Edge("ai-chat", "rag-api", label="verktyg"), Edge("ai-chat", "algorithm", label="verktyg"),
    Edge("rag-api", "vllm-embed"), Edge("rag-api", "paradedb"), Edge("algorithm", "postgres"),
    Edge("vllm-gemma", "collector", kind="pull", label="/metrics"), Edge("paradedb", "collector", kind="pull"),
    Edge("collector", "loki", kind="telemetry"), Edge("collector", "tempo", kind="telemetry"),
    Edge("collector", "prometheus", kind="telemetry"), Edge("dgx", "prometheus", kind="pull"),
    Edge("loki", "grafana", kind="telemetry"), Edge("tempo", "grafana", kind="telemetry"),
    Edge("prometheus", "grafana", kind="telemetry"),
]
COLUMNS = [(20, "① ANVÄNDARE"), (200, "② APPLIKATION · pushar OTLP"), (850, "③ MODELLER & DATA · pull"),
           (1100, "④ TELEMETRI"), (1470, "⑤ SE")]

HERO = """
<div style="font-family:Inter,system-ui,sans-serif;padding:6px 4px 0">
  <div style="font-family:'Roboto Mono',monospace;font-size:12px;letter-spacing:.12em;color:#FFB400">AI-PLATTFORMEN · LIVE</div>
  <div style="font-size:30px;font-weight:600;letter-spacing:-.02em;color:#fff;margin-top:4px">Mår allt bra just nu?</div>
  <div style="font-size:15px;color:#D6D6D6;margin-top:4px">Status för varje komponent nedan. Gult betyder alltid <i>titta här</i>.
  Klicka på en ruta eller välj din roll för att gå vidare.</div>
</div>"""


def persona(title, who, links):
    items = "".join(f'<a href="{u}" style="display:block;color:#fff;text-decoration:none;padding:7px 0;border-top:1px solid #262626;'
                     f'font-family:\'Roboto Mono\',monospace;font-size:13px">{t} <span style="color:#FFB400">→</span></a>'
                     for t, u in links)
    return (f'<div style="border:1px solid #262626;background:#0D0D0D;padding:14px 16px;height:100%;box-sizing:border-box">'
            f'<div style="font-family:\'Roboto Mono\',monospace;font-size:12px;letter-spacing:.1em;color:#707070">{who}</div>'
            f'<div style="font-size:17px;font-weight:600;color:#fff;margin:4px 0 10px">{title}</div>{items}</div>')


PERSONAS = [
    ("Följ ett anrop från A till Ö", "TESTARE", [("05 · Testflöde A→Ö", "/d/test-flow"), ("02 · Plattform · Översikt", "/d/platform-overview")]),
    ("Se agenten tänka, steg för steg", "AI-UTVECKLARE", [("03 · AI-agent · LangGraph", "/d/ai-agent"), ("04 · LLM & RAG", "/d/llm-rag")]),
    ("Håll maskinen frisk", "DRIFT", [("06 · Containrar", "/d/containers"), ("07 · DGX Spark", "/d/infra-dgx"), ("08 · Databaser", "/d/databases")]),
    ("Förstå telemetrin", "PLATTFORM", [("01 · Telemetriflödet", "/d/telemetry-flow"), ("09 · Cardinality & kostnad", "/d/cardinality-cost")]),
]


def status_tiles(title, expr, desc):
    return stat(title, [prom(expr, "{{komponent}}", instant=True)], unit="none", desc=desc, mappings=STATUS_MAP,
                spark=False, text_mode="value_and_name", color_mode="background_solid", orientation="vertical",
                th=thresholds((None, TILE), (1, "#7A5600"), (2, ACCENT)), no_value="ingen data", text_size=(13, 18))


def build():
    b = Board("start", "00 · Start", "Plattformens framsida: status för varje komponent, nyckeltal och vägen vidare",
              time="now-1h", tags=["start"])
    b.add(text(HERO, mode="html"), w=24, h=4)

    b.add(status_tiles("Applikationen · pushar telemetri", Q.status_app(),
                       "Felkvot per tjänst ur traces: > 2 % = STÖRD, > 50 % = NERE. En tjänst som varit aktiv "
                       "senaste timmen men tystnat i 2 minuter visas som NERE."), w=7, h=5)
    b.add(status_tiles("AI-modeller & databaser · hämtas (pull)", f"{Q.status_vllm()} or {Q.status_db()}",
                       "vLLM: NERE om /metrics inte svarar, STÖRD om time-to-first-token p95 > 1 s eller kön > 4. "
                       "Databaser: NERE om Collectorn slutat få statistik."), w=7, h=5)
    b.add(status_tiles("Plattform & infrastruktur", Q.status_up("otel-collector|prometheus|loki|tempo|grafana|node-exporter|cadvisor|dcgm-exporter"),
                       "Allt Prometheus skrapar själv. NERE = scrape misslyckas (up = 0)."), w=10, h=5)

    b.add(stat("Lyckade frågor", [prom(f"1 - ({Q.ASK_ERR_RATIO})")], unit="percentunit", decimals=1,
               desc="Andel av användarnas frågor (frontend /ask) utan 5xx, senaste 5 min. Under 98 % blir den gul.",
               th=thresholds((None, ACCENT), (0.98, WHITE))), w=4, h=4)
    b.add(stat("Väntetid p95", [prom(Q.ASK_P95)], unit="s",
               desc="95 % av användarna får svar snabbare än så här (frontend /ask). Gul över 3 s.",
               th=thresholds((None, WHITE), (3, ACCENT))), w=4, h=4)
    b.add(stat("Frågor / min", [prom(f"{Q.ASK_RATE} * 60")], unit="short", decimals=0,
               desc="Hur många frågor användarna ställer just nu."), w=4, h=4)
    b.add(stat("Agentkörningar OK", [prom('sum(rate(agent_runs_total{outcome="ok"}[5m])) / sum(rate(agent_runs_total[5m]))')],
               unit="percentunit", decimals=1, th=thresholds((None, ACCENT), (0.97, WHITE)),
               desc="Andel LangGraph-körningar som nådde respond utan fel (recursion limit, LLM nere, …). Detaljer: 03 · AI-agent.",
               links=[{"title": "03 · AI-agent", "url": "/d/ai-agent"}]), w=4, h=4)
    b.add(stat("Verktygsfel", [prom('(sum(rate(agent_tool_calls_total{outcome="error"}[5m])) or vector(0)) / sum(rate(agent_tool_calls_total[5m]))')],
               unit="percentunit", decimals=1, th=thresholds((None, WHITE), (0.05, ACCENT)),
               desc="Andel tool calls som misslyckades. Agenten får felet tillbaka och kan ofta svara ändå, men över 5 % är något trasigt.",
               links=[{"title": "03 · AI-agent", "url": "/d/ai-agent"}]), w=4, h=4)
    b.add(stat("GPU", [prom("avg(DCGM_FI_DEV_GPU_UTIL)")], unit="percent", decimals=0, th=thresholds((None, WHITE), (90, ACCENT)),
               desc="GPU-utnyttjande på DGX Spark. Över 90 %: förvänta längre svarstider från modellerna.",
               links=[{"title": "07 · DGX Spark", "url": "/d/infra-dgx"}]), w=4, h=4)

    b.row("Arkitekturen · klicka på en ruta")
    b.add(text(svg_map(BOXES, EDGES, COLUMNS), mode="html"), w=24, h=14)

    b.row("Vem är du?")
    for title, who, links in PERSONAS:
        b.add(text(persona(title, who, links), mode="html"), w=6, h=6)

    b.row("Senaste felen · alla tjänster")
    b.add(logs("ERROR · senaste först", '{deployment_environment_name="demo"} | detected_level="error"',
               desc="Varje felrad från alla tjänster. Expandera en rad och klicka 'Öppna trace' för att se hela anropet."), w=24, h=9)
    return b
