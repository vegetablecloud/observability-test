# Prompt till Copilot-agenten

Klistra in texten nedan i Copilot Chat (Agent mode). Byt ut `<...>`.
Kör hellre **en dashboard i taget**: första gången sätter den mönstret, sedan går resten snabbt.

---

```text
Jag vill att du kraftigt förbättrar våra Grafana-dashboards i <sökväg till dashboards>.

Kopiera INTE blint. Behåll varje dashboards syfte, målgrupp och ungefärliga struktur,
men bygg om den så att den blir tydligare, mer visualiserande och ger mer kontext.

## Referenser (läs dessa först)
- docs/reference/HANDOFF.md: vad referensen är, varför den ser ut så, och fallgroparna.
- .github/instructions/grafana-dashboards.instructions.md: våra regler för dashboards.
- docs/reference/grafana/: ett fungerande exempel från ett annat projekt (dashlib/, boards/,
  build_dashboards.py, check_queries.py). Titta på MÖNSTRET: byggstenar i dashlib, en fil per
  dashboard, automatisk layout, validering, färgspråk, beskrivningar, exemplars, orsak bredvid
  verkan, startsida med status per komponent. Metric-namnen där gäller INTE för oss.
- docs/reference/agent_otel.py: hur en LangGraph-agent instrumenteras (nod, LLM, verktyg).

## Viktigaste ändringen
Sluta handskriva dashboard-JSON. Kopiera in docs/reference/grafana/dashlib/ till
<sökväg>/dashlib/ och anpassa theme.py (vår palett) och panels.py (våra datakälle-uid).
Skriv en boards/bNN_namn.py per dashboard. build_dashboards.py skriver JSON till samma
sökväg som idag. check_queries.py verifierar varje query mot vår Grafana.

## Grafana MCP (verktyget `grafana`)
Du har läsåtkomst till vår riktiga Grafana. Gissa inte, fråga Grafana:
datakällor och uid, metric-namn, label-värden, Loki-labels, och kör varje query du
tänker använda för att se att den ger data. Skriv ALDRIG dashboards direkt till Grafana.
Allt går via generatorn i repot.

## Arbeta i den här ordningen
0. KARTLÄGG DATAN. Via Grafana MCP: vilka tjänster finns (service_name eller job) och vilka
   signaler skickar varje tjänst (metrics, loggar, traces)? Finns histogram för latens,
   trace_id i loggarna, exemplars? Skriv en kort tabell tjänst × signal och lista luckor i
   instrumenteringen som begränsar vad dashboards kan visa. Det är inget fel, men säg det.
1. INVENTERA. Läs varje befintlig dashboard-JSON och skriv en kort tabell per dashboard:
   uid, titel, vem den är till för, vilken fråga den svarar på, panelerna (titel, typ,
   query, enhet) och vad som är svagt (saknar beskrivning/enhet, regnbågsfärger,
   metric-namn som titel, orsak och verkan långt ifrån varandra, inga länkar mellan signaler).
2. FÖRESLÅ. Per dashboard: ny struktur uppifrån och ned (KPI-rad → trender →
   orsak bredvid verkan → drill-down → loggar), vad som behålls, slås ihop, läggs till och tas bort,
   och varför. Visa förslaget och VÄNTA på mitt OK innan du skriver kod.
3. BYGG. Skriv generatorn och bygg om dashboards enligt förslaget.
4. VERIFIERA. Kör build_dashboards.py (stoppar på regelbrott) och check_queries.py mot vår
   Grafana. 0 FEL. Förklara varje tom panel. Kontrollera att uid är oförändrade. Visa diffen
   i sammanfattning.
5. INSTRUMENTERING. Lista det dashboards inte kan visa för att telemetrin saknas (t.ex. spans
   per LangGraph-nod, test.run.id, kvalitetsmetrics för RAG) och föreslå ändringen enligt
   docs/reference/agent_otel.py och kontraktet. Ändra inte applikationskod utan mitt OK.

## Regler
- Använd bara metrics, labels och loggfält som redan finns i våra dashboards eller som du
  kan verifiera i repot. Hitta aldrig på metric-namn. Vid osäkerhet: TODO-kommentar och
  nämn det i sammanfattningen.
- Behåll varje dashboards uid (länkar och bokmärken får inte gå sönder).
- Datakällornas uid: <t.ex. prometheus / loki / tempo / azure-monitor>. Använd dem, hitta inte på egna.
- Grafana-version: <t.ex. 11.x>. Använd en schemaVersion och paneltyper som finns i den versionen.
- Färger: neutral grå/vit bas + EN accentfärg <#hex> för det som är viktigt just nu.
  Samma tjänst har samma färg på alla dashboards.
- Varje panel ska svara på en fråga i titeln och förklara i description vad som är
  normalt och vad man gör när den avviker.
```

---

## Uppföljningsprompter som brukar behövas

- *"Titta på dashboard X igen som en person som har jour kl. 03. Vad saknas för att förstå
  om något är fel inom 10 sekunder? Förbättra KPI-raden och beskrivningarna."*
- *"Lägg orsak bredvid verkan: vilken resurs- eller beroende-panel förklarar latensgrafen?
  Flytta den bredvid, på samma rad."*
- *"Gå igenom alla timeseries: finns det regnbågsfärger kvar? Använd SERVICE_COLORS och
  accenten bara för huvudserien."*
- *"Lägg till en text-panel överst eller sist som förklarar hur man läser dashboarden och
  länkar till nästa dashboard i flödet."*
- *"Kan vi rita flödet (källor → pipeline → lagring) som en SVG i en text-panel i HTML-läge,
  som i exemplet?"*
