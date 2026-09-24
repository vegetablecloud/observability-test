# Prompt till Copilot-agenten

Klistra in texten nedan i Copilot Chat (Agent mode). Byt ut `<...>`.
Kör hellre **en dashboard i taget**: första gången sätter den mönstret, sedan går resten snabbt.

---

```text
Jag vill att du kraftigt förbättrar våra Grafana-dashboards i <sökväg till dashboards>.

Kopiera INTE blint. Behåll varje dashboards syfte, målgrupp och ungefärliga struktur,
men bygg om den så att den blir tydligare, mer visualiserande och ger mer kontext.

## Referenser (läs dessa först)
- .github/instructions/grafana-dashboards.instructions.md: våra regler för dashboards.
- docs/reference/build_dashboards.example.py: ett exempel från ett annat projekt på hur vi
  vill bygga dashboards. Titta på MÖNSTRET: byggstenar överst, en build-funktion per
  dashboard, färgspråk, beskrivningar, exemplars, orsak bredvid verkan. Metric-namnen där
  gäller INTE för oss.

## Viktigaste ändringen
Sluta handskriva dashboard-JSON. Skapa en generator `<sökväg>/build_dashboards.py`
(Python, bara standardbiblioteket) med ett litet bibliotek av byggstenar
(panel, stat, timeseries, table, logs, text, row, dashboard, color_override, thresholds,
query-hjälpare per datakälla). Varje dashboard blir en kort funktion. JSON-filerna blir
byggprodukter som skrivs av scriptet till samma sökväg som idag.

## Arbeta i den här ordningen
1. INVENTERA. Läs varje befintlig dashboard-JSON och skriv en kort tabell per dashboard:
   uid, titel, vem den är till för, vilken fråga den svarar på, panelerna (titel, typ,
   query, enhet) och vad som är svagt (saknar beskrivning/enhet, regnbågsfärger,
   metric-namn som titel, orsak och verkan långt ifrån varandra, inga länkar mellan signaler).
2. FÖRESLÅ. Per dashboard: ny struktur uppifrån och ned (KPI-rad → trender →
   orsak bredvid verkan → drill-down → loggar), vad som behålls, slås ihop, läggs till och tas bort,
   och varför. Visa förslaget och VÄNTA på mitt OK innan du skriver kod.
3. BYGG. Skriv generatorn och bygg om dashboards enligt förslaget.
4. VERIFIERA. Kör scriptet. Kontrollera att uid är oförändrade, att varje panel har
   titel, description och enhet, att raderna summerar till 24 kolumner och att inga gridPos
   överlappar. Visa diffen i sammanfattning.

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
