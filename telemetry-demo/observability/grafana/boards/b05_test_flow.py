"""
05 · Testflöde A→Ö – för testarna.
Svarar på: "Vad hände med MINA anrop, steg för steg, genom hela stacken?"

  ① Så testar du              kör ./scripts/e2e-test.sh, välj testkörning, klicka på ett anrop
  ② Testkörningen             alla anrop med status och tid · alla fel och exakt var de uppstod
  ③ Ett anrop A→Ö             varje steg i tidsordning (tabell) · waterfall · loggarna i tidsordning

Allt bygger på två saker i telemetrin:
  * frontend sätter test.run.id (från headern x-test-run-id) på root-spanen
  * trace_id följer med genom alla tjänster (W3C traceparent) och finns i varje loggrad
"""

from dashlib import (ACCENT, WHITE, Board, cell, field_override, logs, sort_by, table, tempo_columns, text, traceql, traces)

HOWTO = """
<div style="font-family:Inter,system-ui,sans-serif;display:grid;grid-template-columns:1.2fr 1fr 1fr 1fr;gap:14px;padding:4px">
  <div>
    <div style="font-family:'Roboto Mono',monospace;font-size:12px;letter-spacing:.12em;color:#FFB400">TESTFLÖDE A → Ö</div>
    <div style="font-size:26px;font-weight:600;color:#fff;margin-top:4px;letter-spacing:-.02em">Vad hände med mina anrop?</div>
    <div style="font-size:14px;color:#D6D6D6;margin-top:6px">Varje anrop är en trace genom hela stacken. Här ser du alla steg, i ordning, och exakt var något gick fel.</div>
  </div>
  <div style="border:1px solid #262626;background:#0D0D0D;padding:12px 14px">
    <div style="font-family:'Roboto Mono',monospace;font-size:12px;color:#707070">1 · KÖR</div>
    <div style="color:#fff;margin-top:6px;font-size:14px">Märk dina anrop med headern <code>x-test-run-id</code>, eller kör</div>
    <div style="font-family:'Roboto Mono',monospace;color:#FFB400;margin-top:6px;font-size:13px">./scripts/e2e-test.sh</div>
  </div>
  <div style="border:1px solid #262626;background:#0D0D0D;padding:12px 14px">
    <div style="font-family:'Roboto Mono',monospace;font-size:12px;color:#707070">2 · VÄLJ</div>
    <div style="color:#fff;margin-top:6px;font-size:14px">Skriv test-run-id högst upp (skriptet skriver ut länken). <code>loadgen</code> = den simulerade trafiken.</div>
  </div>
  <div style="border:1px solid #262626;background:#0D0D0D;padding:12px 14px">
    <div style="font-family:'Roboto Mono',monospace;font-size:12px;color:#707070">3 · FÖLJ</div>
    <div style="color:#fff;margin-top:6px;font-size:14px">Kopiera ett trace-id till <code>trace_id</code> och fäll ut ③ – eller klicka på trace-id:t för Explore.</div>
  </div>
</div>"""

STATUS_CELLS = field_override("Status", display=cell("color-text"), mappings=[
    {"type": "range", "options": {"from": 200, "to": 399, "result": {"color": WHITE, "index": 0}}},
    {"type": "range", "options": {"from": 400, "to": 599, "result": {"color": ACCENT, "index": 1}}}])


def build():
    b = Board("test-flow", "05 · Testflöde A→Ö", "Vad hände med mina anrop, steg för steg, genom hela stacken?",
              time="now-1h", refresh="30s", tags=["test"])
    b.textbox("test_run", "test-run-id", "loadgen")
    b.textbox("trace_id", "trace_id")
    b.add(text(HOWTO, mode="html"), w=24, h=5)

    b.row("② Testkörningen · $test_run")
    b.add(table("Alla anrop i testkörningen", [traceql(
        '{ resource.service.name = "frontend" && kind = server && span.test.run.id = "$test_run" }'
        ' | select(span.http.response.status_code, span.http.route)', limit=100, table="spans")],
        transformations=[tempo_columns({"http.response.status_code": "Status", "http.route": "Route"},
                                       order=["Start time", "http.response.status_code", "Duration", "http.route", "traceIdHidden", "Span ID"],
                                       hide=["Name"]),
                         sort_by("Start")],
        overrides=[STATUS_CELLS, field_override("Tid", unit="ns", decimals=0, display=cell("color-text"),
                                                thresholds={"mode": "absolute", "steps": [{"value": None, "color": WHITE},
                                                                                          {"value": 3e9, "color": ACCENT}]},
                                                color={"mode": "thresholds"})],
        desc="Ett anrop per rad, senaste först. Status ≥ 400 och tid över 3 s är gula. Kopiera trace_id till variabeln högst upp "
             "för att följa anropet A→Ö i ③, eller klicka på Span för att öppna det i Explore."), w=13, h=12)
    b.add(table("Fel i testkörningen · exakt var", [traceql(
        '{ span.test.run.id = "$test_run" } >> { status = error }'
        ' | select(resource.service.name, span.error.type, span.langgraph.node, span.gen_ai.tool.name, span.http.response.status_code)',
        limit=100, table="spans", spss=10)],
        transformations=[tempo_columns({"service.name": "Tjänst", "error.type": "Feltyp", "langgraph.node": "Nod",
                                        "gen_ai.tool.name": "Verktyg", "http.response.status_code": "HTTP"},
                                       order=["Start time", "service.name", "Name", "error.type", "langgraph.node", "gen_ai.tool.name",
                                              "http.response.status_code", "Duration", "traceIdHidden", "Span ID"])],
        overrides=[field_override("Tid", unit="ns", decimals=0),
                   field_override("Feltyp", display=cell("color-text"), color={"mode": "fixed", "fixedColor": ACCENT})],
        desc="Varje span med status ERROR under en rot-span i testkörningen: vilken tjänst, vilket steg, vilken feltyp, "
             "och för agenten vilken nod och vilket verktyg. Tomt = inga fel."), w=11, h=12)

    b.row("③ Ett anrop A→Ö · $trace_id")
    b.add(table("Stegen i tidsordning", [traceql(
        '{ trace:id = "$trace_id" && name != "" } | select(resource.service.name, span.langgraph.node, span.gen_ai.tool.name, status, span.error.type)',
        limit=1, table="spans", spss=100)],
        transformations=[tempo_columns({"service.name": "Tjänst", "langgraph.node": "Nod", "gen_ai.tool.name": "Verktyg",
                                        "status": "Status", "error.type": "Feltyp"},
                                       order=["Start time", "service.name", "Name", "Duration", "status", "error.type", "langgraph.node",
                                              "gen_ai.tool.name", "Span ID"], hide=["traceIdHidden"]),
                         sort_by("Start", desc=False)],
        overrides=[field_override("Tid", unit="ns", decimals=1, display=cell("gauge", "basic"),
                                  color={"mode": "fixed", "fixedColor": "#4D4D4D"}),
                   field_override("Status", display=cell("color-text"), mappings=[
                       {"type": "value", "options": {"error": {"color": ACCENT, "index": 0}}}]),
                   field_override("Feltyp", display=cell("color-text"), color={"mode": "fixed", "fixedColor": ACCENT})],
        desc="Varje span i anropet, i den ordning de startade: frontend → backend → ai-chat (noderna, LLM, verktygen) → rag-api → "
             "databaser. Stapeln visar hur lång tid steget tog. Gult = steget felade."), w=24, h=14)
    b.add(traces("Waterfall · $trace_id",
                 desc="Samma steg som tabellen, som waterfall. Klicka på en span för alla attribut och 'Logs for this span'."), w=24, h=16)
    b.add(logs("Loggarna för anropet · i tidsordning, alla tjänster", '{deployment_environment_name="demo"} | trace_id="$trace_id"',
               ascending=True,
               desc="Berättelsen i text: request_started (frontend) → node_done … tool_done … (ai-chat) → search_done (rag-api) → "
                    "ask_completed (backend) → response_sent."), w=24, h=12)
    return b
