"""
03 · AI-agent · LangGraph – för AI-utvecklarna.
Svarar på: "Vad gör agenten, steg för steg, och exakt var går det fel?"

  ① Hur mår agenten?          körningar, lyckade, p95, steg, verktygsfel, tokens
  ② Grafen                     som den är RITAD i koden  |  som den KÖRS just nu (node graph, felring per nod)
  ③ Noderna                    var går tiden, och vilken nod felar?
  ④ Verktygen                  anrop, latens och fel per verktyg
  ⑤ LLM:en i agenten           anrop per körning, tokens, latens, omförsök
  ⑥ Körningarna                senaste körningar och exakt var de som felade kraschade (klicka -> trace)
  ⑦ En körning i detalj        hela waterfallen + loggarna för ett trace_id

Allt kommer från agent_otel.py i ai-chat: en span per nod/verktyg/LLM-anrop och metrics med
labels som langgraph.node och gen_ai.tool.name (få, stabila värden).
"""

from dashlib import (ACCENT, cell, sort_by, tempo_columns, G300, G500, G700, NODE_COLORS, TOOL_COLORS, WHITE, Board, bargauge, color_override,
                     field_override, heatmap, logs, loki, node_graph, organize, prom, regex_override, stat, table,
                     text, thresholds, timeseries, traceql, traces)
from dashlib.diagram import Box, Edge, svg_map

R = "[5m]"
NODE = "langgraph_node_duration_seconds"
RUNS = "agent_runs_total"
TOOL = "agent_tool_calls_total"

# Grafen som den är ritad i graph.py
GRAPH_BOXES = [
    Box("start", 20, 150, "START", "", w=90, h=44),
    Box("guard", 150, 150, "guard_input", "PII · validering", w=170),
    Box("agent", 380, 150, "agent", "gemma väljer verktyg", w=190, accent=True),
    Box("tools", 380, 30, "tools", "parallella tool calls", w=190),
    Box("sd", 640, 0, "search_documents", "→ rag-api", w=200, h=50, dashed=True),
    Box("gpi", 640, 60, "get_project_insight", "→ algorithm", w=200, h=50, dashed=True),
    Box("respond", 380, 280, "respond", "svar + källor", w=190),
    Box("end", 640, 286, "END", "", w=90, h=44),
]
GRAPH_EDGES = [
    Edge("start", "guard"), Edge("guard", "agent", label="ok"), Edge("guard", "respond", kind="pull", label="blockerad"),
    Edge("agent", "tools", label="tool_calls"), Edge("tools", "agent", kind="pull"),
    Edge("agent", "respond", label="svar klart"), Edge("respond", "end"),
    Edge("tools", "sd", kind="telemetry"), Edge("tools", "gpi", kind="telemetry"),
]


def live_graph():
    """
    Node graph ur metrics. Kanterna = använda övergångar i grafen (langgraph.transitions), noderna härleds
    ur kanterna och visar anrop/min. Fältnamnen (id, source, target, mainstat) måste vara riktiga fältnamn,
    därför labelsToFields med valueLabel: en label i queryn blir namnet på värdefältet.
    """
    edges = ('sum by (langgraph_from, langgraph_to) (rate(langgraph_transitions_total[5m])) * 60')
    for lbl, src in (("source", "langgraph_from"), ("target", "langgraph_to")):
        edges = f'label_replace({edges}, "{lbl}", "$1", "{src}", "(.*)")'
        edges = f'label_replace(label_replace({edges}, "{lbl}", "START", "{lbl}", "__start__"), "{lbl}", "END", "{lbl}", "__end__")'
    edges = f'label_replace(label_join({edges}, "id", "→", "source", "target"), "field", "mainstat", "", "")'
    return node_graph("Grafen som den körs just nu", [prom(edges, ref="edges", instant=True)],
                      transformations=[{"id": "labelsToFields", "options": {"mode": "columns", "valueLabel": "field",
                                                                              "keepLabels": ["id", "source", "target", "field"]}},
                                       {"id": "merge", "options": {}}],
                      desc="Ur metrics, senaste 5 min. Varje pil = en kant i grafen som faktiskt används, siffran i noden = anrop/min. "
                           "Blir pilen tools ⇄ agent tjockare än START → guard_input loopar agenten (fler varv per fråga).")


OUTCOME_CELLS = [field_override("Utfall", display=cell("color-text"), mappings=[
    {"type": "value", "options": {"ok": {"color": WHITE, "index": 0}}},
    {"type": "regex", "options": {"pattern": ".+", "result": {"color": ACCENT, "index": 1}}}])]


def node_colors():
    return [color_override(n, c, width=3 if n == "agent" else None) for n, c in NODE_COLORS.items()]


def build():
    b = Board("ai-agent", "03 · AI-agent · LangGraph", "Vad gör agenten, steg för steg, och exakt var går det fel?", tags=["ai"])
    b.textbox("trace_id", "trace_id (välj en körning i tabellen)")

    # ① Hur mår agenten?
    b.add(stat("Körningar / min", [prom(f"sum(rate({RUNS}{R})) * 60")], decimals=1,
               desc="Hur många gånger grafen körs från START till END per minut."), w=4, h=4)
    b.add(stat("Lyckade körningar", [prom(f'sum(rate({RUNS}{{outcome="ok"}}{R})) / sum(rate({RUNS}{R}))')], unit="percentunit",
               decimals=1, th=thresholds((None, ACCENT), (0.97, WHITE)),
               desc="Körningar som nådde respond. Resten: recursion_limit (loop), llm_unavailable, guard_blocked. Se ⑤ Utfall."), w=4, h=4)
    b.add(stat("p95 · hela körningen", [prom(f"histogram_quantile(0.95, sum by (le) (rate(agent_run_duration_seconds_bucket{R})))")],
               unit="s", th=thresholds((None, WHITE), (3, ACCENT)),
               desc="Från START till END. Vilken nod som äter tiden syns i ③."), w=4, h=4)
    b.add(stat("Steg per körning", [prom("sum(rate(agent_run_steps_sum[5m])) / sum(rate(agent_run_steps_count[5m]))")],
               unit="short", decimals=1, th=thresholds((None, WHITE), (6, ACCENT)),
               desc="Antal noder som körs per fråga. Normalt 5 (guard → agent → tools → agent → respond). Stiger den: agenten loopar."),
          w=4, h=4)
    b.add(stat("Verktygsfel", [prom(f'(sum(rate({TOOL}{{outcome="error"}}{R})) or vector(0)) / sum(rate({TOOL}{R}))')],
               unit="percentunit", decimals=1, th=thresholds((None, WHITE), (0.05, ACCENT)),
               desc="Tool calls som kastade fel. Felet skickas tillbaka till modellen (som LangGraphs ToolNode), så körningen kan ändå lyckas."),
          w=4, h=4)
    b.add(stat("Tokens / min", [prom('sum(rate(gen_ai_client_token_usage_sum{service_name="ai-chat"}[5m])) * 60')], decimals=0,
               desc="In + ut, alla LLM-anrop agenten gör. Kostnaden (eller GPU-tiden) för agenten."), w=4, h=4)

    # ② Grafen
    b.row("① Grafen · ritad i koden  |  körd just nu")
    b.add(text(svg_map(GRAPH_BOXES, GRAPH_EDGES, width=860, height=360, legend=False), mode="html", title="Så är grafen ritad (graph.py)",
               transparent=False), w=10, h=11)
    b.add(live_graph(), w=14, h=11)

    # ③ Noderna
    b.row("② Noderna · var går tiden, och vilken nod felar?")
    b.add(timeseries("p95 per nod", [prom(f"histogram_quantile(0.95, sum by (le, langgraph_node) (rate({NODE}_bucket[1m])))", "{{langgraph_node}}")],
                     unit="s", overrides=node_colors(),
                     desc="agent (gul) är LLM-anropet och brukar dominera. Går tools upp: ett verktyg eller dess backend är långsamt."),
          w=12, h=8)
    b.add(bargauge("Andel av körningens tid",
                   [prom(f"sum by (langgraph_node) (rate({NODE}_sum{R})) / scalar(sum(rate(agent_run_duration_seconds_sum{R})))", "{{langgraph_node}}",
                         instant=True)], unit="percentunit", max_=1, decimals=0, color=G300, mode="basic",
                   desc="Hur stor del av den totala körtiden varje nod står för (summa över alla körningar, 5 min).",
                   overrides=[color_override("agent", ACCENT)]), w=6, h=8)
    b.add(bargauge("Fel per nod · senaste 5 min",
                   [prom(f'sum by (langgraph_node) (increase({NODE}_count{{outcome="error"}}{R})) or sum by (langgraph_node) (increase({NODE}_count{R})) * 0',
                         "{{langgraph_node}}", instant=True)],
                   unit="short", decimals=0, th=thresholds((None, G700), (1, ACCENT)), mode="basic",
                   desc="Antal gånger en nod kastade fel. Noden som felar är den som stoppar grafen (tools fångar verktygsfel själv)."),
          w=6, h=8)

    # ④ Verktygen
    b.row("③ Verktygen · vad anropar agenten, och vad går sönder?")
    b.add(timeseries("Anrop / min per verktyg", [
        prom(f'sum by (gen_ai_tool_name) (rate({TOOL}{{outcome="ok"}}[1m])) * 60', "{{gen_ai_tool_name}}"),
        prom(f'sum by (gen_ai_tool_name) (rate({TOOL}{{outcome="error"}}[1m])) * 60', "FEL · {{gen_ai_tool_name}}")],
        unit="short", stack=True, fill=30, desc="Staplat: lyckade (grå/vit) och fel (gul) per verktyg.",
        overrides=[color_override(n, c) for n, c in TOOL_COLORS.items()] + [regex_override("FEL.*", ACCENT)]), w=8, h=8)
    b.add(timeseries("p95 per verktyg", [
        prom("histogram_quantile(0.95, sum by (le, gen_ai_tool_name) (rate(agent_tool_duration_seconds_bucket[1m])))", "{{gen_ai_tool_name}}")],
        unit="s", overrides=[color_override(n, c) for n, c in TOOL_COLORS.items()],
        desc="get_project_insight ska ligga på några ms (förberäknat). Hoppar den till ~1 s: förberäkningen har stannat (cache miss)."),
          w=8, h=8)
    b.add(table("Verktygsfel · typ", [
        prom(f'sum by (gen_ai_tool_name, error_type) (increase({TOOL}{{outcome="error"}}[15m]))', instant=True, fmt="table")],
        transformations=[organize(rename={"gen_ai_tool_name": "Verktyg", "error_type": "Feltyp", "Value": "Antal (15 min)"}, exclude=["Time"])],
        sort="Antal (15 min)", overrides=[field_override("Antal (15 min)", decimals=0)],
        desc="HTTPStatusError = verktygets backend svarade med fel (t.ex. 404 för okänt projekt). ToolArgumentError = modellen skickade "
             "trasiga argument."), w=8, h=8)

    # ⑤ LLM:en
    b.row("④ LLM:en i agenten")
    b.add(timeseries("LLM-anrop per körning", [
        prom('sum(rate(gen_ai_client_operation_duration_seconds_count{service_name="ai-chat", gen_ai_operation_name="chat"}[1m])) '
             '/ sum(rate(agent_runs_total[1m]))', "LLM-anrop / körning")], unit="short", color=ACCENT, decimals=1,
        desc="Normalt 2: ett för att välja verktyg, ett för att svara. Fler = fler varv i loopen agent ⇄ tools."), w=6, h=8)
    b.add(timeseries("Tokens / min", [
        prom('sum by (gen_ai_token_type) (rate(gen_ai_client_token_usage_sum{service_name="ai-chat"}[1m])) * 60', "{{gen_ai_token_type}}")],
        unit="short", stack=True, fill=40, overrides=[color_override("input", G500), color_override("output", ACCENT)],
        desc="Input = prompt + verktygsresultat (växer med varje varv). Output = det modellen genererar."), w=6, h=8)
    b.add(timeseries("LLM p95 (agentens vy) vs vLLM", [
        prom('histogram_quantile(0.95, sum by (le) (rate(gen_ai_client_operation_duration_seconds_bucket{service_name="ai-chat", gen_ai_operation_name="chat"}[1m])))',
             "agenten ser (inkl. omförsök)"),
        prom('histogram_quantile(0.95, sum by (le) (rate({"vllm:e2e_request_latency_seconds_bucket", model_name="gemma"}[1m])))', "vLLM e2e")],
        unit="s", overrides=[color_override("agenten ser (inkl. omförsök)", ACCENT, width=3), color_override("vLLM e2e", WHITE, dash=True)],
        desc="Skillnaden mellan linjerna = nätverk, kö och omförsök. Ligger de ihop: modellen själv är långsam."), w=6, h=8)
    b.add(timeseries("Omförsök & misslyckade LLM-anrop", [
        loki('sum(count_over_time({service_name="ai-chat"} |= "llm_request_retry" [1m])) or vector(0)', "omförsök / min"),
        loki('sum(count_over_time({service_name="ai-chat"} |= "LLMUnavailable" [1m])) or vector(0)', "gav upp / min")],
        unit="short", overrides=[color_override("omförsök / min", G300), color_override("gav upp / min", ACCENT, width=3)],
        desc="Räknat ur loggarna (Loki). Omförsök är ok, 'gav upp' betyder att användaren fick ett fel."), w=6, h=8)

    # ⑥ Utfall
    b.row("⑤ Utfall")
    b.add(timeseries("Körningar per utfall", [prom(f"sum by (outcome) (rate({RUNS}[1m])) * 60", "{{outcome}}")], unit="short",
                     bars=True, stack=True,
                     overrides=[color_override("ok", G700), color_override("recursion_limit", ACCENT), color_override("llm_unavailable", ACCENT),
                                color_override("guard_blocked", G300)],
                     desc="ok = grått. Allt gult är körningar som inte nådde fram: recursion_limit (agenten loopade), llm_unavailable (gemma svarade inte)."),
          w=12, h=8)
    b.add(heatmap("Körningens längd · fördelning", [prom("sum by (le) (increase(agent_run_duration_seconds_bucket[1m]))", "{{le}}", fmt="heatmap")],
                  desc="Varje kolumn = en minut, varje ruta = hur många körningar som tog så lång tid. Ljusare = fler. Ett nytt band högt upp = en ny sorts långsamhet."),
          w=12, h=8)

    # ⑦ Körningarna
    b.row("⑥ Körningarna · klicka på en rad för hela tracen")
    b.add(table("Senaste körningarna", [traceql(
        '{ name = "invoke_agent chat-agent" } | select(span.agent.outcome, span.agent.trail, span.agent.steps)', limit=30, table="spans")],
        transformations=[tempo_columns({"agent.outcome": "Utfall", "agent.trail": "Väg genom grafen", "agent.steps": "Antal steg"},
                                       order=["Start time", "agent.outcome", "agent.steps", "Duration", "agent.trail", "Span ID"],
                                       hide=["Name", "traceIdHidden"]), sort_by("Start")],
        overrides=OUTCOME_CELLS + [field_override("Tid", unit="ns", decimals=0, width=90), field_override("Antal steg", width=90),
                                   field_override("Utfall", width=130), field_override("Start", width=170),
                                   field_override("Span", width=150)], time_from="10m",
        desc="En rad per agentkörning senaste 10 min: utfall, vägen genom grafen (trail) och antal steg. Klicka på Span för hela waterfallen."),
        w=12, h=10)
    b.add(table("Här kraschade det · nod och verktyg", [traceql(
        '{ resource.service.name = "ai-chat" && status = error && (name =~ "node .*" || name =~ "execute_tool .*") }'
        ' | select(span.langgraph.node, span.gen_ai.tool.name, span.error.type, span.langgraph.step)', limit=30, table="spans")],
        transformations=[tempo_columns({"langgraph.node": "Nod", "gen_ai.tool.name": "Verktyg", "error.type": "Feltyp",
                                        "langgraph.step": "LangGraph-steg"},
                                       order=["Start time", "Name", "error.type", "langgraph.node", "gen_ai.tool.name", "langgraph.step",
                                              "Duration", "Span ID"], hide=["traceIdHidden"]), sort_by("Start")],
        overrides=[field_override("Tid", unit="ns", decimals=0), field_override("Feltyp", display=cell("color-text"),
                                                                                  color={"mode": "fixed", "fixedColor": ACCENT})],
        desc="Varje span i agenten som fick status ERROR: vilken nod, vilket verktyg, vilket steg och vilken feltyp. "
             "Det är svaret på 'var i programmet kraschar det?'. Senaste 15 min.", time_from="15m"), w=12, h=10)
    b.add(logs("Agentens loggar · node_failed · tool_failed · recursion_limit",
               '{service_name="ai-chat"} |~ "node_failed|tool_failed|agent_recursion_limit|llm_request_failed|LLMUnavailable"',
               desc="Samma fel som tabellen ovan, med detaljer. Varje rad har trace_id: expandera och klicka 'Öppna trace'."), w=24, h=8)

    # ⑧ En körning i detalj
    b.row("⑦ En körning i detalj · klistra in ett trace_id högst upp och fäll ut", collapsed=True)
    b.add(traces("Waterfall för $trace_id",
                 desc="Hela körningen: invoke_agent → varje nod → chat gemma / execute_tool. Klicka på en span för attribut: "
                      "langgraph.step, gen_ai.tool.call.arguments, gen_ai.output.messages, error.type."), w=24, h=16)
    b.add(logs("Loggar för $trace_id · i tidsordning", '{deployment_environment_name="demo"} | trace_id="$trace_id"', ascending=True,
               desc="Agentens berättelse i text: node_done node=agent step=2 ... tool_done tool=search_documents ..."), w=24, h=10)
    return b
