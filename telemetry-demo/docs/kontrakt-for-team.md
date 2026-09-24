# Kontrakt för team som pushar telemetri

Du äger Collectorn. Teamen äger sina tjänster och sin instrumentering. Det här är vad
de behöver veta, och vad du kan kräva, för att allt ska gå att koppla ihop i Grafana.

## 1. Vart ska det skickas?

| Protokoll | Endpoint | När |
|---|---|---|
| OTLP/gRPC | `http://<collector>:4317` | standard för backend-SDK:er (.NET, Java, Go, Python) |
| OTLP/HTTP | `http://<collector>:4318` (`/v1/traces`, `/v1/logs`, `/v1/metrics`) | browser, serverless, när gRPC krånglar |

Alla officiella SDK:er läser samma miljövariabler, så ingen kod behöver ändras mellan miljöer:

```bash
OTEL_EXPORTER_OTLP_ENDPOINT=http://otel-collector:4317
OTEL_EXPORTER_OTLP_PROTOCOL=grpc            # eller http/protobuf mot :4318
OTEL_SERVICE_NAME=orders-api
OTEL_RESOURCE_ATTRIBUTES=deployment.environment.name=prod,service.version=1.8.2,service.namespace=commerce
```

## 2. Krav (måste)

1. **`service.name`** är unikt och stabilt. Det blir `service_name` i Prometheus och Loki och
   noden i service graph. Byter det namn försvinner historiken.
2. **`deployment.environment.name`** och **`service.version`** som resource-attribut.
3. **W3C Trace Context** (`traceparent`) propageras på alla utgående anrop. Det är default i alla
   SDK:er. Ett team som bryter kedjan ger "föräldralösa" traces.
4. **Loggar via OTel** (eller med `trace_id`/`span_id` i varje rad) så att Grafana kan hoppa
   från span till logg.
5. **Inga höga cardinality-värden som metric-labels**: `user_id`, `request_id`, `email`, fria
   strängar, fil-namn. De hör hemma som span-attribut.
6. **Ingen PII i klartext.** Collectorn redigerar några kända fält, men den är ett skyddsnät
   och inte en policy.

## 3. Baseline (bör) – "every service is observable"

| Signal | Minimum |
|---|---|
| Traces | inkommande och utgående HTTP/gRPC, DB-anrop, egna spans runt viktiga steg (t.ex. varje RAG-steg) |
| Metrics | `http.server.request.duration` (ger rate, errors och duration), runtime-metrics, några domänmetrics |
| Logs | INFO/WARN/ERROR, strukturerade (`key=value` eller attribut), inte DEBUG i prod |

Följ **semantic conventions** för namn (`http.server.request.duration`, `gen_ai.client.operation.duration`,
`db.client.operation.duration`). Då fungerar samma dashboards för alla team.

## 4. Om de inte kan pusha

Exponerar produkten `/metrics` (Prometheus-format) lägger **du** till ett scrape-jobb, antingen
i `prometheus.yml` eller i Collectorns `prometheus`-receiver. Sätt `job_name` till det
`service.name` du vill se i Grafana.

## 5. Så verifierar teamet att det fungerar

```bash
./scripts/send-test-telemetry.sh      # ren OTLP/HTTP med curl, ingen SDK
```

I Grafana: **01 · Telemetriflödet → Push-tjänster** ska visa tjänsten med spans/s,
metric-serier och loggrader/s.

## 6. Extra för AI-tjänster (agenter, RAG, LLM)

Samma kontrakt, plus några namn som gör att dashboards 03 och 04 fungerar för alla agenter:

| Vad | Krav | Exempel i demot |
|---|---|---|
| En span per agentkörning | `invoke_agent <agent>` med `gen_ai.operation.name=invoke_agent`, `gen_ai.agent.name`, `gen_ai.conversation.id` | `services/ai-chat/agent_otel.py` → `run()` |
| En span per nod | `node <namn>` med `langgraph.node`, `langgraph.step` | `@tel.node("agent")` |
| En span per LLM-anrop | `chat <modell>` enligt GenAI-semconv: `gen_ai.request.model`, `gen_ai.usage.input_tokens/output_tokens`, `gen_ai.response.finish_reasons` | `tel.llm_call(...)` |
| En span per verktyg | `execute_tool <verktyg>` med `gen_ai.tool.name`, `gen_ai.tool.call.id`, `error.type` vid fel | `tel.tool_call(...)` |
| Metrics | `gen_ai.client.operation.duration`, `gen_ai.client.token.usage`, `langgraph.node.duration`, `langgraph.transitions`, `agent.tool.calls` | labels: modell, nod, verktyg, `outcome` – aldrig id:n |
| Innehåll | prompter och svar på spans **bara** med `OTEL_INSTRUMENTATION_GENAI_CAPTURE_MESSAGE_CONTENT=true`, klippt | av i prod om det är känsligt |
| Kvalitet (RAG) | `rag.retrieval.top_score`, `rag.search.empty`, `rag.documents.returned` | `services/rag-api/main.py` |

Använder teamet LangChain/LangGraph och vill ha noll kod: `openinference-instrumentation-langchain`
ger spans för kedjor, LLM-anrop och verktyg via en callback. Attributnamnen följer då OpenInference
(`openinference.span.kind`, `input.value`, `llm.token_count.*`) i stället för GenAI-semconv, så
dashboard-queries behöver anpassas.
