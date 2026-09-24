# Observability-arkitektur med OpenTelemetry

_Started 2026-09-24 14:55 UTC_

---

## User

Arbetade i 24s

Nej. För en applikation med ~20 containers och flera repos är din grundarkitektur väldigt rimlig. OpenTelemetry beskriver Collector just som det centrala lagret som tar emot, processar och exporterar telemetry från flera tjänster, och Grafanas stack är byggd för precis kombinationen Loki + Tempo + Prometheus + Grafana. 

Jag skulle bara ändra en del av din mentala modell:

> Målet är inte “fånga så mycket som möjligt”.
Målet är “fånga tillräckligt för att kunna förstå systemets tillstånd och förklara varför något händer.”



Det är en viktig skillnad.

Din arkitektur

Ungefär så här bör du tänka:

APPLICATION
────────────────────────────────────────────────────

Frontend
Backend C#
Algorithm Python
AI / RAG Python
Audio
Analytics
...
~20 containers

      │
      │ OTLP
      │
      ├──── Logs
      ├──── Traces
      └──── Metrics
             │
             ▼
      ┌────────────────────┐
      │ OpenTelemetry      │
      │ Collector          │
      │                    │
      │ receive            │
      │ process            │
      │ batch/filter/etc   │
      │ export             │
      └─────────┬──────────┘
                │
       ┌────────┼────────┐
       ▼        ▼        ▼
     Loki     Tempo   Prometheus
     logs     traces    metrics
       │        │        │
       └────────┼────────┘
                ▼
             Grafana

Det är en fullt normal observability-arkitektur. OpenTelemetry rekommenderar dessutom Collector/pipeline mellan applikationen och tracing-backenden eftersom den ger batching, retries och frikopplar applikationen från backendens tillgänglighet. 

Det viktigaste frågetecknet: metrics

Här skulle jag korrigera dig ganska tydligt:

Metrics är inte mindre vanligt än logs/traces. Tvärtom är metrics extremt centralt för observability.

OpenTelemetry beskriver application/request metrics som viktiga indikatorer för availability och performance. Metrics-signalen är dessutom Stable i både Python, .NET, JavaScript, Go m.fl. 

Tänk:

METRICS
"Är något fel?"

TRACES
"Var händer det?"

LOGS
"Vad exakt hände?"

Det är en förenkling, men en väldigt användbar sådan.

Anta att systemet plötsligt blir långsamt.

Metrics:

request_duration_p95
200ms → 4300ms

Du ser direkt:

> Något har hänt klockan 14:32.



Sedan går du till traces:

Frontend       40ms
 └ Backend     4200ms
    └ Algorithm 180ms
       └ AI     3950ms  ← här
          └ LLM 3900ms

Nu vet du:

> Problemet är i AI-tjänsten.



Sedan klickar du in på spanen och hittar korrelerade logs:

WARN llm_request_retry
model=local-model
attempt=2
reason=timeout
trace_id=abc123

Nu vet du:

> LLM-anropet timeoutade, retryades och gjorde hela requesten långsam.



Det är där observability blir kraftfullt.

Grafana bygger explicit stöd för den modellen: Tempo kan länka traces till både logs och metrics, och Prometheus exemplars kan användas för att hoppa från en metric till den trace som producerade observationen. 


---

Du har egentligen två olika typer av metrics

Det är förmodligen här din bild har blivit lite skev.

Du verkar hittills huvudsakligen ha hittat:

CPU
RAM
GPU
VRAM
disk
network
container CPU
container memory

Det är infrastructure metrics.

Exempel hos er:

node-exporter
      ↓
CPU / RAM / disk

cAdvisor
      ↓
container CPU / RAM

dcgm-exporter
      ↓
GPU utilization / memory / temperature

De är bra.

Men det finns också application metrics.

Exempel backend:

http.server.request.count

http.server.request.duration

http.server.error.count

active_requests

Algorithm:

algorithm_duration_seconds
algorithm_errors_total
items_processed_total

AI:

rag_requests_total

retrieval_duration_seconds

retrieved_documents

llm_request_duration_seconds

llm_errors_total

tool_calls_total

Och exempelvis:

queue_length = 47

är en Gauge.

requests_total = 15 493

är en Counter.

request_duration_seconds

är typiskt en Histogram.

Det är exakt de typerna OpenTelemetry Metrics API är byggt för. 


---

Ska alla 20 containers instrumenteras?

Jag skulle säga:

Alla viktiga applikationstjänster: ja.

Men inte:

> “Vi måste manuellt skapa 50 spans, 80 metrics och 200 log statements i varje repo.”



Det vore observability-teater.

Istället skulle jag sätta en baseline för varje service.

SERVICE
│
├── Resource metadata
│     service.name
│     service.version
│     deployment.environment
│
├── Logs
│     INFO
│     WARN
│     ERROR
│
├── Traces
│     inbound requests
│     outbound requests
│     DB calls
│     HTTP calls
│     important internal operations
│
└── Metrics
      request count
      errors
      latency
      runtime/process metrics

Sedan lägger man specialinstrumentation där det faktiskt betyder något.

I AI-repot exempelvis:

HTTP request
  ↓
agent
  ↓
retrieval
  ↓
reranker
  ↓
LLM
  ↓
tool call
  ↓
response

Här är manuella spans väldigt värdefulla eftersom du faktiskt vill förstå varje del.


---

Och trace propagation är nästan viktigare än mängden telemetry

Det här skulle jag prioritera väldigt högt.

Du vill inte ha:

frontend trace:   ABC

backend trace:    DEF

algorithm trace:  GHI

AI trace:         JKL

Du vill ha:

TRACE ID = ABC123

Frontend
   │
   ▼
Backend
   │
   ▼
Algorithm
   │
   ▼
AI
   │
   ├── Retrieval
   ├── Reranker
   ├── LLM
   └── Tool

Trace context ska propagateras mellan processgränser. TraceId används just för att gruppera spans från olika processer till samma distribuerade trace. 

Och sedan:

trace_id=ABC123
span_id=XYZ789

även i loggarna.

OpenTelemetry har explicit stöd för TraceId och SpanId i log records för att kunna korrelera logs från olika delar av ett distribuerat system med samma trace. 

Det är mycket mer värdefullt än att bara samla miljontals separata loggrader.


---

Men “ju mer vi samlar desto bättre” skulle jag släppa

Här finns egentligen din största potentiella designmiss.

Mer telemetry innebär också:

mer disk
mer CPU
mer network
mer Collector-load
mer Loki-data
mer Tempo-data
fler time series
mer brus
svårare queries
risk för känslig data

Och metrics har ytterligare problemet cardinality.

Gör exempelvis inte:

http_requests{
    user_id="938293",
    request_id="ABC123",
    filename="whatever.pdf"
}

Nu kan du skapa miljontals time series.

Däremot:

http_requests{
    service="backend",
    method="POST",
    status_code="200"
}

är mycket rimligare.

OpenTelemetry har särskild hantering av cardinality limits i metrics av just den anledningen. 


---

Så här hade jag satt målet för er

Inte:

> Every container sends everything.



Utan:

> Every service is observable.



Det är en mycket bättre princip.

Det betyder att om någon frågar:

> “Varför tog användarens request 12 sekunder?”



ska ni kunna svara.

Om någon frågar:

> “Vilken service börjar få fler fel?”



ska ni kunna svara.

Om någon frågar:

> “Var systemet CPU-, GPU-, nätverks- eller LLM-begränsat?”



ska ni kunna svara.

Om någon frågar:

> “Vad hände exakt med request ABC123?”



ska ni kunna svara.

Det är observability.

OpenTelemetry definierar faktiskt ett väl instrumenterat system ungefär i den riktningen: utvecklare ska kunna felsöka problem utan att först behöva lägga till ny instrumentation. 


---

En sak till som är ganska intressant för just er

Du behöver inte ens skapa alla application metrics manuellt från början.

Tempo kan generera RED metrics från era traces:

R = Rate
E = Errors
D = Duration

Alltså från spans kan Tempo exempelvis härleda:

requests/sec

error rate

request duration

och även skapa service graphs. 

Det skulle kunna vara väldigt intressant för er första version:

┌─ Loki ───── logs
Apps → Collector ┼─ Tempo ──── traces
                 └─ Prometheus metrics
                       ↑
                 infra exporters

Tempo traces
     │
     └── RED metrics / service graph

Då behöver du inte gå till varje utvecklare och säga:

> “Nu måste du implementera 25 custom metrics.”



Ni kan få ganska mycket gratis från tracing först.

Min rekommenderade ambitionsnivå

För era ~20 containers hade jag velat nå:

1. Alla applikationstjänster: strukturerade INFO/WARN/ERROR-logs med service.name och helst trace/span correlation.

2. Alla request-baserade tjänster: distributed tracing med korrekt context propagation.

3. Infrastruktur: CPU/RAM/disk/container/GPU metrics.

4. Applikationer: grundläggande RED-metrics automatiskt där instrumentation ger dem.

5. Custom metrics: bara där de faktiskt säger något domänspecifikt.

6. Collector: gemensam ingestion point där ni kan batcha, filtrera, berika, redigera känslig data och senare sampla. Collector har processors för bland annat batching, filtering/transformation, memory limiting och trace sampling. 

Och då hade jag absolut inte krävt DEBUG överallt. INFO/WARN/ERROR + bra traces + metrics är en mycket bättre grund.

Det fina är att du då bygger ett observability-system, inte bara “en Grafana-dashboard”. Det är egentligen den större arkitekturgrejen i det du håller på med.


Med contexten ovan. 

Kan du visualisera detta i en animation hur ett riktigt bra grafana upplägg borde se ut. 

Tänker att animeringen ska ge en känslan "Aha det är så traces, metrics, logs ger värde när det är liksom 20 containers som körs ochallt samlas och lagras i Loki, tempo, Prometheus via Otel Collector   till grafana liksom? Hur performance från en Nvidia dgx spark som allt körs på till att applikationen körs o allt. Ahaa helheten.. där ser man jätte bra nu tack vare allt detta. Osv osv."

## Assistant



## User

Answered — audience: Utvecklarteamet; length: ~2–3 min; language: Svenska; arc: Bottom-up: DGX Spark → 20 containers → OTel Collector → Loki/Tempo/Prometheus → Grafana → incident 14:32 löses via metrics → traces → logs; scenes: GPU/VRAM från DGX Spark kopplat till LLM-latens, Trace propagation (ett trace_id genom alla tjänster), Tempo genererar RED-metrics + service graph, Cardinality-varning (user_id i labels), Collector:…; text: Captions (fristående video)

## Assistant

_[tool: ask_user]_

_[tool: copy_starter_component]_

_[tool: copy_starter_component]_

_[tool: list_files]_

_[tool: read_file]_

_[tool: read_file]_

_[tool: list_files]_

_[tool: grep]_

_[tool: read_file]_

_[tool: grep]_

_[tool: read_file]_

_[tool: read_file]_

_[tool: copy_files]_

_[tool: read_file]_

## Assistant

_[tool: read_skill_prompt]_

_[tool: read_file]_

_[tool: list_files]_

_[tool: read_file]_

_[tool: read_file]_

_[tool: read_file]_

_[tool: read_file]_

_[tool: grep]_

_[tool: read_file]_

_[tool: read_file]_

_[tool: grep]_

_[tool: read_file]_

_[tool: write_file]_

_[tool: write_file]_

_[tool: dc_write]_

_[tool: show_html]_

_[tool: get_webview_logs]_

_[tool: multi_screenshot]_

_[tool: get_webview_logs]_

_[tool: sleep]_

_[tool: save_screenshot]_

_[tool: get_webview_logs]_

_[tool: read_file]_

_[tool: show_html]_

_[tool: save_screenshot]_

_[tool: get_webview_logs]_

Rendering works. Filmstrip:

_[tool: multi_screenshot]_

_[tool: multi_screenshot]_

_[tool: run_script]_

_[tool: ready_for_verification]_

Animationen finns i **Observability Film.dc.html**. Den är 2:40 lång och byggd i Conpanions stil: svart bakgrund och gult för det som är aktivt just då.

**Så går berättelsen:**
1. Den börjar på DGX Spark och fortsätter uppåt genom de 20 containrarna.
2. Tjänsterna skickar logs, traces och metrics över OTLP. Prometheus hämtar hårdvarans metrics direkt från exporters.
3. Collectorns pipeline visas steg för steg: batch, filter, redaction och sampling. Därefter kommer Loki, Tempo och Prometheus, där Tempo räknar fram RED-metrics.
4. Ett avsnitt om cardinality visar hur user_id i en label får antalet tidsserier att explodera.
5. Kameran zoomar ut över hela stacken och in i Grafana.
6. Incidenten 14:32 löses i tre steg. Först visar p95-grafen spiken. Ett exemplar leder till tracen, där LLM-anropet tar 3 880 ms. Loggarna, filtrerade på trace_id, visar timeout och retry.
7. Under "Helheten" ritas en gul tråd från larmet genom alla lager ner till GPU:n.
8. Den slutar med de tre frågorna och ett slutkort: "Every service is observable."

**Att tänka på:**
- Incidentens detaljer är påhittade för att illustrera, bland annat att GPU:n slog i taket 14:31, containernamnen och Collector-inställningarna. Byt gärna till era riktiga tjänstnamn.
- Tider och tempo kan du justera per scen i tidslinjen under förhandsvisningen. Därifrån kan du också exportera som video.

