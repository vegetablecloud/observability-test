# Copilot-kit: bygg om Grafana-dashboards som kod

Allt du behöver för att få Copilot-agenten att bygga dashboards med samma angreppssätt som
`telemetry-demo`. Det innebär en generator istället för handskriven JSON, och dashboards som
berättar något istället för att bara visa data.

## Så här använder du det (i jobbrepot)

0. **Grafana MCP (rekommenderas).** Då kan agenten fråga er riktiga Grafana vilka metrics,
   labels och datakällor som finns, och köra queries innan den använder dem. Det tar bort
   gissandet.
   - Skapa ett *service account* i Grafana med rollen **Viewer** och skapa en token.
   - Kopiera `mcp.json` till `.vscode/mcp.json` och byt `GRAFANA_URL`. VS Code frågar efter
     token vid start. Kräver Docker Desktop (imagen `grafana/mcp-grafana`).
   - `--disable-write` gör servern läsbar men inte skrivbar. Det är avsiktligt:
     dashboards ska ändras via generatorn och en PR, inte direkt i Grafana.
   - Starta servern i VS Code (*MCP: List Servers → grafana → Start*) och slå på
     verktygen i Agent mode (verktygsikonen i chatten).
   - I Copilot Enterprise måste policyn **"MCP servers in Copilot"** vara påslagen för
     organisationen, och en eventuell allowlist måste tillåta servern. Fråga er
     GitHub-admin om servern inte syns.
1. **Regler.** Kopiera `grafana-dashboards.instructions.md` till
   `.github/instructions/grafana-dashboards.instructions.md`.
   Copilot läser den automatiskt för filer som matchar `applyTo`. Justera globben
   efter var era dashboards ligger.
2. **Referensen.** Kopiera till jobbrepot:
   | Från det här repot | Till jobbrepot |
   |---|---|
   | `copilot-kit/HANDOFF.md` | `docs/reference/HANDOFF.md` |
   | `telemetry-demo/observability/grafana/` (dashlib/, boards/, build_dashboards.py, check_queries.py, provisioning/) | `docs/reference/grafana/` |
   | `telemetry-demo/services/ai-chat/agent_otel.py` | `docs/reference/agent_otel.py` |
   | `telemetry-demo/docs/kontrakt-for-team.md` | `docs/reference/kontrakt-for-team.md` |

   Det är mönstret agenten ska lära sig av, inte något den ska kopiera. Det räcker **inte** med en
   py-fil: dashboards blir bara bra om telemetrin under dem har rätt namn, och det visar
   `agent_otel.py`, datakällorna och kontraktet.
3. **Prompt.** Öppna Copilot Chat i *Agent mode*, fyll i `<...>` i `PROMPT.md` och klistra in.
   Börja med **en** dashboard, godkänn förslaget, och ta sedan resten.

## Vad agenten ska ta med sig från exemplet

| Mönster | Var i referensen |
|---|---|
| Byggstenar i ett bibliotek, en fil per dashboard | `dashlib/panels.py`, `boards/bNN_*.py` |
| Automatisk layout, ingen x/y för hand | `dashlib/board.py` (`Board.add`, `Board.row(collapsed=)`) |
| Bygget stoppar på regelbrott | `dashlib/validate.py`, `build_dashboards.py --check` |
| Varje query verifieras mot Grafana | `check_queries.py` |
| En accentfärg, fast färg per tjänst, status OK/STÖRD/NERE | `dashlib/theme.py`, `dashlib/queries.py` |
| Startsida med status per komponent och genvägar per roll | `boards/b00_start.py` |
| Klickbar, animerad arkitekturkarta | `dashlib/diagram.py` |
| LangGraph: grafen ritad bredvid grafen körd (node graph ur metrics) | `boards/b03_ai_agent.py` → `live_graph()` |
| Var kraschade det: TraceQL med `status = error` per nod och verktyg | `boards/b03_ai_agent.py`, `b05_test_flow.py` |
| Testflöde A→Ö: `test.run.id`, strukturell TraceQL, steg i tidsordning | `boards/b05_test_flow.py` |
| Orsak bredvid verkan (p95 bredvid GPU och köer) | `boards/b02_platform_overview.py` |
| Topp 5-containrar, upp/nere över tid | `boards/b06_containers.py` |
| Klick från metric till trace till loggar | `exemplar=True` + `provisioning/datasources/datasources.yaml` |
| Chaos-/deploy-markörer på alla grafer | `CHAOS_ANNOTATION` i `dashlib/board.py` |

## Tips

- Om agenten börjar hitta på metric-namn: påminn om regeln och be den lista alla metrics
  den använder, med källa (vilken befintlig panel de kom ifrån).
- Be den köra generatorn och visa `git diff --stat` innan du granskar.
- Datakälle-länkarna (exemplars, trace → logs) ligger i Grafanas datasource-provisionering,
  inte i dashboarden. Visa agenten `datasources.yaml` om ni provisionerar datakällor själva.
