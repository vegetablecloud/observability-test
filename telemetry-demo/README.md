# Telemetry-demo: AI-plattform + OpenTelemetry → Loki · Tempo · Prometheus → Grafana

En körbar referens för att **förstå hur slutresultatet ser ut** när många tjänster
(som du inte alltid äger) skickar telemetri till en gemensam OTel Collector, och hur
det blir till *en* bild i Grafana. Det här är filmen "Observability arkitektur" i
riktig kod.

Tjänsterna är medvetet enkla. Det är **telemetrin** som ska vara fullständig.

```bash
cd telemetry-demo
cp .env.example .env               # profiler och experiment-reglage
docker compose up -d --build        # ~15 containers, första bygget tar några minuter
open http://localhost:8080          # chatt-UI:t (frontend)
open http://localhost:3000          # Grafana, startar på 01 · Telemetriflödet
./scripts/incident.sh slow          # simulera incidenten (eller knappen i UI:t)
./scripts/incident.sh normal
```

---

## 1. Vad som körs

```
                         ┌───────────── APPLIKATIONEN (push: OTel-SDK → OTLP) ────────────┐
 loadgen ──HTTP──▶ frontend (C#) ──▶ backend (C#) ──▶ algorithm (Python)                  │
   (användare)        │                  │   └──────▶ ai-chat (Python, RAG) ──▶ qdrant    │
                      │                  └──▶ postgres               └────────▶ llm (vLLM) │
                      └────────────── alla 4 skickar logs + traces + metrics ──────────────┘
                                                   │ OTLP gRPC :4317
                                                   ▼
 ┌──────────── PULL ────────────┐     ┌──────────────────────────────┐
 │ llm /metrics (vLLM-format)   │◀────│      OpenTelemetry Collector │◀── externa team pushar
 │ qdrant /metrics              │◀────│ receive → process → export   │    hit (:4317/:4318)
 │ postgres (SQL-statistik)     │◀────│                              │
 └──────────────────────────────┘     └───────┬──────────┬───────────┘
                                         logs │   traces │   metrics
                                              ▼          ▼          ▼
 node-exporter, cAdvisor,  ◀──scrape──   Loki       Tempo ──RED──▶ Prometheus
 dcgm-exporter (GPU)                        └──────────┼──────────────┘
                                                       ▼
                                                    Grafana  (lagrar ingenting – frågar de tre)
```

| Container | Roll | Hur telemetrin kommer ut |
|---|---|---|
| `frontend` | C# ASP.NET Core, chatt-UI + BFF. Här **startar** varje trace | **Push** (OTel .NET SDK) |
| `backend` | C# API: anropar algorithm → ai-chat → Postgres | **Push** (+ Npgsql-spans) |
| `algorithm` | Python FastAPI, "poängsätter" frågan | **Push** (zero-code `opentelemetry-instrument` + egna spans) |
| `ai-chat` | Python RAG: embed → Qdrant → rerank → LLM, med timeout + retry | **Push** (auto + manuella spans, GenAI-semconv) |
| `llm` | Mock av **vLLM** (OpenAI-API + `vllm:*`-metrics + simulerad GPU). Byt mot riktig vLLM med `--profile gpu` | **Pull** – ingen SDK, bara `/metrics` |
| `qdrant` | Vektordatabas | **Pull** – `/metrics` |
| `postgres` | Konversationer | **Pull** – Collectorn loggar in och läser statistik |
| `loadgen` | Simulerade användare (~2 frågor/s) | ingen (den är "användaren") |
| `otel-collector` | Den enda ingången | tar emot, filtrerar, redigerar PII, samplar, batchar |
| `loki` / `tempo` / `prometheus` | Lagring per signal | skrapas själva av Prometheus |
| `grafana` | 5 färdiga dashboards + länkade datakällor | |
| `node-exporter` / `cadvisor` | Värd- och container-metrics | **Pull** av Prometheus |

---

## 2. Push vs pull – vem ansvarar för vad?

Den här frågan avgör hur du bygger det. Två regler:

**Push (OTLP).** Tjänsten har en OpenTelemetry-SDK och *skickar själv*. Teamet som äger
tjänsten ansvarar för instrumenteringen. Du ansvarar för att det finns en endpoint som tar emot.
Det du ger dem är ett **kontrakt**, inte kod (se [docs/kontrakt-for-team.md](docs/kontrakt-for-team.md)):

```bash
OTEL_EXPORTER_OTLP_ENDPOINT=http://<din-collector>:4317     # eller :4318 för HTTP
OTEL_SERVICE_NAME=<unikt, stabilt namn>
OTEL_RESOURCE_ATTRIBUTES=deployment.environment.name=prod,service.version=1.2.3
```

Testa kontraktet utan någon SDK: `./scripts/send-test-telemetry.sh` skickar en span, en
loggrad och en metric som `partner-service` med curl. Den dyker upp i Grafana precis som
de egna tjänsterna.

**Pull (scrape).** Produkten exponerar `/metrics` (Prometheus-format), och **du** hämtar.
Du kan inte ändra koden, så det här är normalfallet för vLLM, databaser, exporters och köer.
Det finns två ställen att hämta från, och demot visar båda:

| Vem hämtar | Används här för | Varför |
|---|---|---|
| **Prometheus** (`prometheus.yml`) | node-exporter, cAdvisor, dcgm-exporter, stacken själv | Klassiskt, enkelt, `up`-metric per mål |
| **Collectorn** (`prometheus`/`postgresql`-receivers) | vLLM, Qdrant, Postgres | Samma pipeline som allt annat: berikning, filtrering, samma `service.name` |

> **Hur det blir i slutet:** alla signaler hamnar i tre lager (Loki, Tempo, Prometheus),
> oavsett om de pushades eller hämtades. Grafana lagrar ingenting. Det frågar de tre och
> **kopplar ihop dem via `service.name`, tidsaxeln och `trace_id`**. Därför spelar det ingen
> roll för slutanvändaren vem som pushar och vem som pullar. Det som spelar roll är att alla
> följer samma namngivning.

---

## 3. Dashboards

Alla ligger i mappen *Telemetry-demo* och har delad crosshair, alltså samma tidpunkt i alla paneler.

| | Dashboard | Svarar på |
|---|---|---|
| 01 | **Telemetriflödet** (startsida) | Hur rör sig datan? Vem pushar/pullar, vad Collectorn tar emot, filtrerar, samplar och skickar, vad backends tar emot |
| 02 | **Plattform · Översikt** | Dashboarden från filmen: p95 per tjänst **med exemplars**, GPU & minne, service graph, långsamma traces, WARN/ERROR-loggar |
| 03 | **AI · RAG & LLM** | Var i AI-flödet går tiden (p95 per RAG-steg ur spans), LLM klient- vs serverlatens, TTFT, tokens/s, retries, KV-cache |
| 04 | **Infrastruktur · DGX Spark** | CPU/minne/disk/nät, GPU (util, minne, temp, effekt), CPU/minne per container, .NET-runtime, Postgres |
| 05 | **Cardinality & kostnad** | Serier per metric och per tjänst, loggvolym, spans/s. Varför "mer är bättre" inte stämmer |

Dashboards genereras från `observability/grafana/build_dashboards.py`. Ändra där, kör
`python3 observability/grafana/build_dashboards.py`, och Grafana laddar om inom 30 s.

### Följ incidenten (metrics → traces → logs)

1. `./scripts/incident.sh slow` (eller knappen **slow** i chatt-UI:t).
2. **02 · Översikt**: p95 går från ~0,6 s till flera sekunder, och GPU-panelen går mot 100 % *innan*.
   **Metrics: är något fel?**
3. Klicka på en **◆ exemplar-punkt** i p95-grafen → *View trace*. Waterfallen visar att
   `chat local-model` i `ai-chat` tar tiden, med två HTTP-försök mot `llm` där det första timeoutar.
   **Traces: var händer det?**
4. I tracen: klicka **Logs for this span** → Loki visar
   `WARN llm_request_retry model=local-model attempt=2 reason=timeout` för exakt det `trace_id`.
   **Logs: vad exakt hände?**
5. **03 · AI** visar samma sak från vLLM:s egna metrics (pull): time-to-first-token och KV-cache stiger.

---

## 4. Vad Collectorn gör (`observability/otel-collector/config.yaml`)

| Steg | Processor | I demot |
|---|---|---|
| Skydda sig själv | `memory_limiter` | backar av vid 80 % minne |
| Berika | `resource/env` | sätter `deployment.environment.name` om den saknas |
| Rensa brus | `filter/noise` | slänger `/health`-spans och DEBUG-loggar |
| Ta bort PII | `transform/redact` | `user.email` på spans och e-post i loggtext → `[REDACTED]` (backend skickar den med flit) |
| Sampla | `tail_sampling` | behåll **alla fel** och **alla > 2 s**, plus `TRACE_SAMPLING_PERCENT` av resten |
| Batcha | `batch` | färre, större skrivningar |

Prova: sätt `TRACE_SAMPLING_PERCENT=10` i `.env` och kör `docker compose up -d otel-collector`.
Titta sedan på *Tail sampling* i dashboard 01. Obs: service graph och span-metrics räknas i Tempo
**efter** sampling, så de underskattar trafiken. Vill du ha exakta RED-metrics trots sampling
räknar du dem i Collectorn före sampling med `spanmetrics`-connectorn.

## 5. Experiment

| Ändra i `.env` | Vad du ser |
|---|---|
| `BAD_CARDINALITY=true` + `docker compose up -d backend` | `app_ask_requests_total` får `user_id` och `request_id` som labels. Dashboard 05: antalet serier rusar |
| `TRACE_SAMPLING_PERCENT=10` | färre traces i Tempo, men fel och långsamma finns kvar |
| `RPS=10` | mer last: vLLM-kö, GPU, batch-storlek i Collectorn |
| `LLM_TIMEOUT_S=1.0` | fler retries och fel även utan incident |

## 6. På DGX Spark med riktig GPU

```bash
COMPOSE_PROFILES=gpu VLLM_MODEL=Qwen/Qwen2.5-1.5B-Instruct docker compose up -d --build
```

- `vllm` ersätter mocken (samma nätverksnamn `llm`, samma `/metrics`). vLLM **pushar dessutom egna
  traces** via `--otlp-traces-endpoint`, så spans inne i LLM-servern hamnar i samma trace.
- `dcgm-exporter` ersätter den simulerade GPU:n. På GB10 kan vissa DCGM-fält (t.ex. framebuffer)
  saknas eftersom minnet är unified. Unified memory syns då i node-exporterns minnespanel.
- `VLLM_IMAGE` / `DCGM_IMAGE` kan behöva pekas på NVIDIA:s arm64-images för Spark (NGC).
- Höj `LLM_TIMEOUT_S` om modellen är större.

## 7. Filer

```
docker-compose.yml               alla containers + OTel-miljövariablerna (kontraktet)
.env.example                     mall för .env (profiler och experiment-reglage)
services/frontend|backend        C#  – Program.cs visar hela OTel-setupen (~15 rader)
services/algorithm|ai-chat       Python – zero-code + manuella spans/metrics
services/llm-mock                "tredjepart" utan SDK, bara /metrics
observability/otel-collector     receivers, processors, exporters
observability/prometheus|loki|tempo
observability/grafana            datakällor med länkar (exemplar→trace→logs) + dashboards
scripts/incident.sh              simulera incident (slow|error|normal|story)
scripts/send-test-telemetry.sh   "externt team" pushar med ren OTLP/HTTP
docs/kontrakt-for-team.md        vad du kräver av team som pushar
```

## Begränsningar (medvetet)

- Ingen autentisering, TLS eller HA. Collectorn tar emot från vem som helst på 4317/4318.
  I produktion: TLS, `bearertokenauth` eller mTLS, och en gateway-Collector per miljö.
- Lokal disk som lagring. I produktion: objektlagring (S3/MinIO) för Loki och Tempo.
- Browser-telemetri (RUM) saknas. Frontendens traces startar på servern. Collectorn har CORS
  påslaget för OTLP/HTTP, så en browser-SDK (eller Grafana Faro) kan pekas på `:4318`.
- cAdvisor kräver en vanlig Docker-värd (cgroup v2). I nästlade/sandlådade miljöer blir
  containerpanelerna tomma.
