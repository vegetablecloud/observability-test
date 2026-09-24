# Copilot-kit: bygg om Grafana-dashboards som kod

Allt du behöver för att få Copilot-agenten att bygga dashboards med samma angreppssätt som
`telemetry-demo`. Det innebär en generator istället för handskriven JSON, och dashboards som
berättar något istället för att bara visa data.

## Så här använder du det (i jobbrepot)

1. **Regler.** Kopiera `grafana-dashboards.instructions.md` till
   `.github/instructions/grafana-dashboards.instructions.md`.
   Copilot läser den automatiskt för filer som matchar `applyTo`. Justera globben
   efter var era dashboards ligger.
2. **Referensexempel.** Kopiera
   `telemetry-demo/observability/grafana/build_dashboards.py` till
   `docs/reference/build_dashboards.example.py`.
   Det är mönstret agenten ska lära sig av, inte något den ska kopiera.
3. **Prompt.** Öppna Copilot Chat i *Agent mode*, fyll i `<...>` i `PROMPT.md` och klistra in.
   Börja med **en** dashboard, godkänn förslaget, och ta sedan resten.

## Vad agenten ska ta med sig från exemplet

| Mönster | Var i `build_dashboards.py` |
|---|---|
| Byggstenar överst, en `build_*()` per dashboard | `panel`, `stat`, `timeseries`, `table`, `logs`, `text`, `row`, `dashboard` |
| Gemensamma queries som konstanter | `P95`, `UP_MAP` |
| En accentfärg och fast färg per tjänst | `Y`, `SERVICE_COLORS`, `service_overrides()`, `color_override(dash=, width=)` |
| Trösklar som färgar först när det spelar roll | `thresholds((None, WH), (2, Y))` + `th_style="dashed"` |
| KPI-rad → trender → orsak bredvid verkan → drill-down → loggar | `build_overview()` (p95 bredvid GPU) |
| Kapitel i flödets ordning | `build_flow()`: `row("① Källor …")`, `row("② OTel Collector …")` |
| Flödesdiagram som SVG i en text-panel | `FLOW_SVG` |
| Mixed-datakälla, tabell hopslagen på `service_name` | första tabellen i `build_flow()` |
| Klick från metric till trace till loggar | `exemplar=True` + `provisioning/datasources/datasources.yaml` |
| Beskrivning på varje panel ("ska vara 0, blir den gul: …") | överallt |

## Tips

- Om agenten börjar hitta på metric-namn: påminn om regeln och be den lista alla metrics
  den använder, med källa (vilken befintlig panel de kom ifrån).
- Be den köra generatorn och visa `git diff --stat` innan du granskar.
- Datakälle-länkarna (exemplars, trace → logs) ligger i Grafanas datasource-provisionering,
  inte i dashboarden. Visa agenten `datasources.yaml` om ni provisionerar datakällor själva.
