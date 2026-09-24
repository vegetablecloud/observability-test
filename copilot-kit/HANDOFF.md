# Överlämning: observability-plattformen som kod

Till: GitHub Copilot (agent mode) och teamet som tar över.
Från: telemetry-demo i det här repot, byggt och verifierat mot riktig Grafana 13, Prometheus 3,
Loki 3.7, Tempo 2.8 och OTel Collector 0.161 (varje query i varje panel kördes och varje
dashboard fotograferades innan överlämning).

Läs det här först. Det förklarar **vad** som byggts, **varför** det ser ut som det gör, **vilka
filer** som bär mönstret, och **fallgroparna** som kostade tid. Kopiera inte demot. Använd
mönstret på vårt riktiga projekt.

---

## 1. Målet

En plattform som alla 18 i teamet vill ha öppen, inte en samling grafer:

| Roll | Frågan de ställer | Dashboard i demot |
|---|---|---|
| alla | Mår allt bra just nu, och vart går jag? | `00 · Start` |
| testare | Vad hände med *mina* anrop, steg för steg, A→Ö? | `05 · Testflöde A→Ö` |
| AI-utvecklare | Vad gör agenten, nod för nod, och exakt var kraschar den? | `03 · AI-agent · LangGraph` |
| AI-utvecklare | Är det modellen, embeddings eller sökningen? | `04 · LLM & RAG` |
| drift | Lever containrarna, har maskinen resurser, mår databaserna? | `06`, `07`, `08` |
| plattform | Hur rör sig telemetrin, vad kostar den? | `01`, `09` |
| alla | Är något fel, var, vad exakt? | `02 · Plattform · Översikt` |

## 2. De fem besluten som gör skillnaden

1. **Dashboards är kod.** Ett Python-bibliotek (`dashlib/`) har all Grafana-JSON *en gång*.
   Varje dashboard är en fil med en `build()`-funktion som bara innehåller titel, query, enhet
   och beskrivning. JSON är en byggprodukt. Ingen skriver JSON för hand, någonsin.
2. **Generatorn granskar sig själv.** `build_dashboards.py` stoppar bygget om en panel saknar
   beskrivning eller enhet, om paneler överlappar, om en datakälla är okänd eller om en länk
   pekar på en dashboard som inte finns. `check_queries.py` kör *varje* query mot Grafana och
   listar paneler utan data. Det är så man vet att en dashboard fungerar, inte genom att titta.
3. **En dashboard = en fråga, läst uppifrån och ned.** KPI-rad → trender → orsak bredvid verkan
   → drill-down (tabeller, traces) → loggar. Titlar är frågor eller påståenden. Varje panel
   förklarar vad som är normalt och vad man gör när den avviker.
4. **Ett färgspråk.** Grått/vitt för allt normalt, **en** accentfärg för "titta här" (huvudserien,
   ett passerat tröskelvärde, något som är nere). Samma tjänst har samma färg överallt
   (`theme.py`). Inga regnbågar.
5. **Signalerna är ihopkopplade.** Delad crosshair, exemplars (klick från en punkt i en graf till
   tracen), trace → loggar, logg → trace, samma `service.name` överallt, chaos-annoteringar på
   alla grafer, och klickbara arkitekturkartor som leder vidare.

## 3. Filerna som bär mönstret (dela dessa med Copilot)

| Fil | Varför den är viktig |
|---|---|
| `telemetry-demo/observability/grafana/dashlib/panels.py` | Byggstenarna: `prom()`, `loki()`, `traceql()`, `stat()`, `timeseries()`, `bargauge()`, `table()`, `logs()`, `traces()`, `heatmap()`, `state_timeline()`, `node_graph()`, `tempo_columns()` |
| `…/dashlib/board.py` | `Board`: automatisk layout (ingen x/y för hand), hopfällda rader, variabler, länkar, chaos-annotering |
| `…/dashlib/theme.py` | Färgspråket och statusrutornas mappning (OK / STÖRD / NERE) |
| `…/dashlib/queries.py` | Queries som återkommer: RED per tjänst, status per komponent |
| `…/dashlib/validate.py` | Reglerna som bygget stoppar på |
| `…/dashlib/diagram.py` | Klickbara, animerade arkitekturkartor som SVG |
| `…/boards/b00_start.py` | Startsidan: statusrutnät, nyckeltal, karta, roller |
| `…/boards/b03_ai_agent.py` | Agent-dashboarden: grafen ritad + körd (node graph ur metrics), noder, verktyg, LLM, körningar |
| `…/boards/b05_test_flow.py` | Testflödet: TraceQL på `test.run.id`, strukturella frågor (`>>`), steg i tidsordning |
| `…/build_dashboards.py`, `…/check_queries.py` | Bygg + validera, och kör varje query mot Grafana |
| `…/provisioning/datasources/datasources.yaml` | Länkarna mellan signalerna (exemplars, trace→logs, logs→trace) |
| `telemetry-demo/services/ai-chat/agent_otel.py` | Hur en LangGraph-agent instrumenteras: nod, LLM-anrop, verktyg, körning |
| `telemetry-demo/docs/kontrakt-for-team.md` | Vad varje team måste skicka (namn, attribut, labels) |

Det räcker **inte** med en py-fil. Dashboards blir bara bra om telemetrin under dem har rätt namn
och labels. Därför hör `agent_otel.py`, datakällorna och kontraktet till.

## 4. Så gör du det på vårt projekt

1. **Kartlägg datan först** (via Grafana MCP, se `README.md` i den här mappen): vilka tjänster finns,
   vilka signaler skickar var och en, vilka metric-namn och labels finns *exakt*. Skriv en tabell
   tjänst × signal. Luckor i instrumenteringen är fynd, inte fel.
2. **Inventera befintliga dashboards**: uid, målgrupp, fråga, paneler, svagheter.
3. **Föreslå** ny struktur per dashboard (vilken roll, vilken fråga, vilka rader). Vänta på OK.
4. **Kopiera in `dashlib/`** (byt palett i `theme.py`, datakälle-uid i `panels.py`) och skriv en
   `boards/bNN_*.py` per dashboard. Behåll befintliga `uid`.
5. **Bygg och verifiera**: `build_dashboards.py` (inga regelbrott) och `check_queries.py` (inga
   FEL; varje tom panel förklarad).
6. **Instrumentering som saknas** (t.ex. LangGraph-noder): föreslå `agent_otel.py`-mönstret för
   teamet som äger koden. Dashboarden kan inte visa det som inte skickas.

Vårt projekt har LangGraph-orkestrering med många verktyg. `agent_otel.py` skalar: dekorera varje
nod med `@tel.node("namn")` och kör varje verktyg i `tel.tool_call(...)`. Verktygsnamnen blir
labels (få, stabila värden), argument och resultat blir span-attribut (unika värden).

## 5. Fallgroparna (lärt den hårda vägen, verifierat mot riktig Grafana)

**Metric-namn**
- Collectorns egna metrics har **inget `_total`-suffix** i 0.161: `otelcol_receiver_accepted_spans`,
  inte `…_total`. Minne heter `otelcol_process_memory_rss` (inget `_bytes`). Gissa aldrig: lista namnen.
- vLLM-metrics har kolon: skriv `{"vllm:num_requests_running"}` (UTF-8-namn i Prometheus 3).
- OTLP-histogram med enhet `s` får `_seconds` i Prometheus: `gen_ai.client.operation.duration` →
  `gen_ai_client_operation_duration_seconds_bucket`.

**Labels**
- postgresql-receivern lägger tabell och index som **resource-attribut**. Utan
  `promote_resource_attributes: [postgresql.table.name, postgresql.index.name]` i Prometheus
  kollapsar alla tabeller till *en* serie per databas och siffrorna blir fel utan att något syns.
- Ge varje receiver-instans sitt eget `service.name` (en pipeline per databas med en
  `resource`-processor), annars går postgres och paradedb inte att skilja åt.

**Status "nere"**
- En tjänst som dör slutar skicka metrics. Serien försvinner och panelen blir tom, inte röd.
  Lösning (i `queries.py`): `live or (2 * max_over_time(target_info[1h]))`, så att allt som
  synts senaste timmen men tystnat visas som NERE. Aggregera båda sidor `by (komponent)` innan
  `or`, annars matchar labelsen inte och du får dubbletter.

**Tempo / TraceQL-tabeller**
- `table="spans"` ger kolumner med **visningsnamn** (`Start time`, `Span ID`, `Duration`, `Name`,
  `Trace Service`). `organize` arbetar på visningsnamnen. Använd `tempo_columns()`.
- Span-namnet (`Name`) är tomt om queryn inte filtrerar på `name`: lägg till `&& name != ""`.
- `spss` (spans per span set) får vara max 100.
- `{ trace:id = "…" }` och strukturella frågor `{ a } >> { status = error }` fungerar i Tempo 2.8
  och är grunden för testflödet.

**Node graph ur Prometheus**
- Panelen hittar fält på deras **riktiga namn** (`id`, `source`, `target`, `mainstat`).
  `organize`-rename byter bara visningsnamnet, så det fungerar inte.
- `calculateField` joinar **alla** frames innan den räknar, så noder och kanter blandas ihop.
- Filtret "apply to refId" respekteras inte av `merge`.
- Det som fungerar: **en** kant-query där `label_replace` skapar labels `id`/`source`/`target`
  plus en label `field="mainstat"`, sedan `labelsToFields` med `valueLabel: "field"` och `merge`.
  Noderna härleds ur kanterna. Se `live_graph()` i `b03_ai_agent.py`.

**Loki**
- `count_over_time` ger *inget* svar när inga rader matchar: lägg till `or vector(0)` så att
  panelen visar 0 i stället för "No data".
- HTML/SVG i text-paneler kräver `GF_PANELS_DISABLE_SANITIZE_HTML=true`.

**Heatmap**
- Prometheus-histogram: `sum by (le) (increase(x_bucket[1m]))` med `format: heatmap`, och
  `calculate: false`. Grafana gör om kumulativa buckets själv.

## 6. Hur du vet att du är klar

- [ ] `python3 build_dashboards.py` går igenom utan regelbrott.
- [ ] `python3 check_queries.py` mot vår Grafana: 0 FEL, varje tom panel har en förklaring
      (den ska vara tom tills något händer, t.ex. omstarter).
- [ ] Varje dashboard har en roll och en fråga i sin beskrivning, och startsidan länkar till den.
- [ ] Varje panel har titel, beskrivning och enhet, och accentfärgen används bara för "titta här".
- [ ] Befintliga `uid` är oförändrade.
- [ ] En testare kan gå från ett trace-id till varje steg i tidsordning utan att fråga någon.
- [ ] En AI-utvecklare ser vilken nod och vilket verktyg som felade, med feltyp.
