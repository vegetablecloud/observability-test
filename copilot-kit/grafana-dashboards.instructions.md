---
applyTo: "**/grafana/**,**/dashboards/**,**/*dashboard*"
---

# Grafana-dashboards: så bygger vi dem

Dessa regler gäller allt arbete med Grafana-dashboards i repot. Målet är dashboards som
**berättar något** och som går att granska i en PR, inte bara paneler med data.

## 1. Dashboards är kod, inte handskriven JSON

- Dashboards **genereras** av ett Python-script (`build_dashboards.py`, bara standardbiblioteket).
  JSON-filerna är en **byggprodukt**: de checkas in (Grafana provisionerar dem), men
  **redigeras aldrig för hand**. Ändra i scriptet och kör det igen.
- Scriptet har ett litet **bibliotek av byggstenar** överst: `panel`, `stat`, `timeseries`,
  `table`, `logs`, `text`, `row`, `dashboard`, `color_override`, `thresholds`,
  plus en funktion per datakälla som bygger en query (`prom(...)`, `loki(...)` osv.).
  All mångordig JSON (fieldConfig, options, legend, tooltip) finns **en gång** i byggstenarna.
  Varje dashboard är sedan en kort funktion `build_<namn>()` som bara innehåller
  **titel, placering, query, enhet, beskrivning**.
- Frågor som används på flera ställen (t.ex. p95-latens) ligger som **konstanter** överst.
- Stil (färger, linjebredd, tooltip, legend) sätts centralt så att alla dashboards ser likadana ut.
- `uid` är **stabil** och ändras aldrig: bokmärken, länkar och alerts pekar på den.
  Vid migrering från en befintlig dashboard: **behåll dess `uid`**.
- Panel-id:n sätts av en räknare, positionen (`gridPos`) av en `y`-markör som flyttas nedåt.

## 2. Varje dashboard svarar på en fråga

- Börja med att skriva ner **frågan** dashboarden svarar på och **vem** som läser den.
  Frågan ska stå i dashboardens `description`.
- Läs uppifrån och ned som en berättelse:
  1. **KPI-rad** överst (y=0): 4–6 `stat`-paneler, 4 kolumner breda, med tröskelvärden.
     *"Är något fel just nu?"*
  2. **Trender** (`timeseries`): *"Sedan när, och hur mycket?"*
  3. **Orsak bredvid verkan**: lägg panelen som kan förklara ett symptom **bredvid**
     symptomet, på samma tidsaxel (t.ex. resursmättnad bredvid latens).
  4. **Drill-down**: tabeller, traces, topp-listor: *"Var händer det?"*
  5. **Loggar** längst ned: *"Vad exakt hände?"*
- Använd `row`-paneler som **kapitel** när en dashboard följer ett flöde. Numrera dem i
  flödets ordning (① Källor → ② Bearbetning → ③ Lagring …).
- Hellre 5 fokuserade dashboards som länkar till varandra än en med 40 paneler.

## 3. Titlar och beskrivningar gör jobbet

- Titlar är **påståenden eller frågor**, inte metric-namn.
  Bra: `Var i flödet går tiden? p95 per steg`. Dåligt: `http_server_duration_bucket`.
- **Varje panel har `description`**: vad den visar, vad som är normalt, och vad man gör
  när den ser konstig ut ("Ska vara 0. Blir den gul: …").
- Legend-texter är mänskliga (`"p95 · {{service_name}}"`), inte rå PromQL.
- En `text`-panel får gärna förklara begrepp, ge tumregler, eller ge "nästa steg" med
  länkar till nästa dashboard. En HTML-/SVG-panel kan rita **flödet** som dashboarden mäter.

## 4. Färgspråk: neutralt, med en accent

- Grundpaletten är **grå/vit** (mörkt tema). **En accentfärg** används bara för det som är
  viktigt *just nu*: huvudserien i en graf, eller ett passerat tröskelvärde.
  Undvik `palette-classic`, som ger regnbågsfärger där allt ser lika viktigt ut.
- **Samma entitet har alltid samma färg** på alla dashboards: en central
  `SERVICE_COLORS`-map (tjänst → färg) som alla overrides använder.
- Hierarki med linjer: huvudserie = accent + `lineWidth 3`; jämförelse- eller sekundärserie =
  streckad (`dash`); bakgrundsserier = mörkare grå.
- Tröskelvärden: `stat` har basfärg vit → accent vid gränsen. I `timeseries` visas gränsen
  som streckad linje (`thresholdsStyle: dashed`, basfärg `transparent`).
- **Alltid enhet** (`s`, `percent`, `percentunit`, `bytes`, `Bps`, `short`) och rimliga `decimals`.

## 5. Koppla ihop signalerna (det är det här som gör dashboards användbara)

- `graphTooltip: 1` (**delad crosshair**) på alla dashboards: samma tidpunkt i alla paneler.
- **Exemplars** på latens-histogram (`exemplar: True`) så att man kan klicka från en punkt i grafen
  till exakt den trace som gav värdet. Kräver `exemplarTraceIdDestinations` på Prometheus-datakällan.
- Datakälle-länkar: trace → loggar (`tracesToLogsV2`), logg → trace (`derivedFields`),
  trace → metrics (`tracesToMetrics`). Det gör att man klickar sig fram istället för att kopiera id:n.
- Samma nyckel överallt (t.ex. `service_name`) så att metrics, loggar och traces kan
  ställas mot varandra, även i **en tabell** med Mixed-datakälla + `joinByField`.
- Dashboard-`links` med `keepTime: true` och en gemensam tagg så att man kan hoppa mellan dashboards.
- Variabler (t.ex. `$trace_id`, `$service`) där användaren vill filtrera.

## 6. Queries

- Använd **bara metrics, labels och loggfält som finns** i den befintliga dashboarden eller
  som går att verifiera i datakällan. **Hitta aldrig på metric-namn.** Är du osäker: skriv en
  `# TODO: verifiera metric` och säg det i PR-beskrivningen.
- `rate()`-fönster konsekvent (t.ex. `[1m]` eller `$__rate_interval`) i hela dashboarden.
- Percentiler med `histogram_quantile(0.95, sum by (le, ...) (rate(..._bucket[...])))`.
- Filtrera bort brus (health checks, interna routes) i frågan, inte i efterhand.
- Aldrig högkardinalitets-labels (user_id, request_id) i `by (...)` eller legend.

### Verifiera mot riktig data (Grafana MCP)

Om Grafana MCP-servern är ansluten ska du **använda den istället för att gissa**:
- Lista datakällor och deras `uid` innan du skriver queries.
- Lista metric-namn och label-värden i Prometheus, och labels i Loki, för det du ska visa.
- **Kör varje ny query** och kontrollera att den ger data innan den läggs i en panel.
- Hämta befintliga dashboards och deras panel-queries som utgångspunkt.
- Rendera gärna en panel som bild för att se resultatet, om rendering finns.
- **Skriv aldrig dashboards direkt till Grafana via MCP.** Ändringar går via generatorn och en PR.

## 7. Layout

- 24 kolumner. En rad ska summera till 24 (t.ex. 6×4 stats, 2×12 eller 3×8 grafer).
- Höjd: stat 4, graf 8–9, tabell/loggar 10–11.
- Inga överlappande `gridPos`. `y` räknas upp i koden, inga hårdkodade magiska tal.

## 8. Innan du är klar

1. Kör generatorn: `python3 <sökväg>/build_dashboards.py`. Inga fel, JSON skrivs.
2. Granska `git diff` på JSON: stabila `uid`, inga försvunna paneler som inte var avsiktliga.
3. Kontrollera att varje panel har titel, `description`, enhet, och att raderna summerar till 24.
4. Beskriv i PR:en per dashboard: frågan den svarar på, vad som behölls, lades till eller togs bort, och varför.
