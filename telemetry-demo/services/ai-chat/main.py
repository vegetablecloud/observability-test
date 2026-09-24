"""
ai-chat – RAG-pipeline i Python: embed -> retrieve (Qdrant) -> rerank -> LLM (vLLM).

Det här är tjänsten där MANUELLA spans verkligen lönar sig. Auto-instrumenteringen
ger oss server-spanen och varje HTTP-anrop (httpx -> Qdrant / LLM). Men det är de
egna spanen som gör att en trace-waterfall visar *vilket steg* i AI-flödet som tog tid:

  POST /chat                        (auto: FastAPI)
   └ rag.pipeline                   (manuell)
      ├ rag.embed                   (manuell)
      ├ rag.retrieve                (manuell)
      │  └ POST qdrant/.../query    (auto: httpx)
      ├ rag.rerank                  (manuell)
      └ chat local-model            (manuell, GenAI-semconv)
         ├ POST llm/v1/chat/...     (auto: httpx)  attempt 1 -> timeout
         └ POST llm/v1/chat/...     (auto: httpx)  attempt 2
"""

import asyncio
import hashlib
import logging
import math
import os
import re
import time
from contextlib import asynccontextmanager

import httpx
from fastapi import FastAPI, HTTPException
from opentelemetry import metrics, trace
from opentelemetry.trace import Status, StatusCode
from pydantic import BaseModel

from knowledge import DOCS

QDRANT = os.getenv("QDRANT_URL", "http://qdrant:6333")
LLM_BASE = os.getenv("LLM_BASE_URL", "http://llm:8000/v1")
LLM_MODEL = os.getenv("LLM_MODEL", "local-model")
LLM_TIMEOUT = float(os.getenv("LLM_TIMEOUT_S", "2.5"))
LLM_ATTEMPTS = int(os.getenv("LLM_MAX_ATTEMPTS", "2"))
COLLECTION = "kb"
DIM = 256

log = logging.getLogger("ai-chat")
log.setLevel(logging.INFO)
logging.getLogger("httpx").setLevel(logging.WARNING)  # en INFO-rad per HTTP-anrop = brus
tracer = trace.get_tracer("ai-chat")
meter = metrics.get_meter("ai-chat")

SEC_BUCKETS = [0.01, 0.025, 0.05, 0.1, 0.25, 0.5, 1, 1.5, 2, 3, 4, 6, 10]
# GenAI semantic conventions (samma namn som OTel-specen -> färdiga dashboards funkar)
llm_duration = meter.create_histogram("gen_ai.client.operation.duration", unit="s",
                                      description="LLM-anropets längd", explicit_bucket_boundaries_advisory=SEC_BUCKETS)
llm_tokens = meter.create_histogram("gen_ai.client.token.usage", unit="{token}", description="Tokens per anrop",
                                    explicit_bucket_boundaries_advisory=[8, 16, 32, 64, 128, 256, 512, 1024, 2048])
# Domänmetrics för RAG
retrieval_duration = meter.create_histogram("rag.retrieval.duration", unit="s", description="Tid för vektorsökning",
                                            explicit_bucket_boundaries_advisory=SEC_BUCKETS)
retrieved_docs = meter.create_histogram("rag.documents.retrieved", unit="{document}", description="Antal dokument efter rerank",
                                        explicit_bucket_boundaries_advisory=[0, 1, 2, 3, 4, 5, 6, 8, 10])
rag_requests = meter.create_counter("rag.requests", unit="{request}", description="RAG-förfrågningar per utfall")
llm_retries = meter.create_counter("gen_ai.client.retries", unit="{retry}", description="Omförsök mot LLM")

http = httpx.AsyncClient(timeout=10)


def embed(text: str) -> list[float]:
    """Deterministisk 'hash-embedding' – ingen modell att ladda ner, men ger vettig likhet."""
    v = [0.0] * DIM
    words = re.findall(r"\w+", text.lower())
    grams = words + [w[i:i + 4] for w in words for i in range(max(1, len(w) - 3))]
    for g in grams:
        h = int(hashlib.md5(g.encode()).hexdigest(), 16)
        v[h % DIM] += 1.0 if (h >> 8) & 1 else -1.0
    n = math.sqrt(sum(x * x for x in v)) or 1.0
    return [x / n for x in v]


async def seed_qdrant():
    for attempt in range(30):
        try:
            r = await http.get(f"{QDRANT}/collections/{COLLECTION}")
            if r.status_code == 200 and r.json()["result"]["points_count"] >= len(DOCS):
                return
            await http.put(f"{QDRANT}/collections/{COLLECTION}", json={"vectors": {"size": DIM, "distance": "Cosine"}})
            points = [{"id": i + 1, "vector": embed(t), "payload": {"topic": topic, "text": t}} for i, (topic, t) in enumerate(DOCS)]
            r = await http.put(f"{QDRANT}/collections/{COLLECTION}/points?wait=true", json={"points": points})
            r.raise_for_status()
            log.info("knowledge_base_seeded docs=%d", len(points))
            return
        except Exception as e:  # noqa: BLE001
            log.warning("qdrant_not_ready attempt=%d error=%s", attempt + 1, type(e).__name__)
            await asyncio.sleep(2)


@asynccontextmanager
async def lifespan(_: FastAPI):
    await seed_qdrant()
    yield


app = FastAPI(title="ai-chat", lifespan=lifespan)


class ChatReq(BaseModel):
    question: str
    intent: str | None = None


@app.get("/health")
def health():
    return {"ok": True}


async def call_llm(question: str, context: list[str]) -> dict:
    system = "Du är en hjälpsam assistent. Svara kort på svenska utifrån kontexten:\n" + "\n".join(f"- {c}" for c in context)
    body = {"model": LLM_MODEL, "max_tokens": 200, "temperature": 0.2,
            "messages": [{"role": "system", "content": system}, {"role": "user", "content": question}]}

    with tracer.start_as_current_span(f"chat {LLM_MODEL}") as span:
        span.set_attribute("gen_ai.operation.name", "chat")
        span.set_attribute("gen_ai.system", "vllm")
        span.set_attribute("gen_ai.request.model", LLM_MODEL)
        span.set_attribute("gen_ai.request.max_tokens", 200)
        start = time.perf_counter()
        attrs = {"gen_ai.operation.name": "chat", "gen_ai.request.model": LLM_MODEL}
        last_err = None
        for attempt in range(1, LLM_ATTEMPTS + 1):
            try:
                r = await http.post(f"{LLM_BASE}/chat/completions", json=body, timeout=LLM_TIMEOUT)
                r.raise_for_status()
                data = r.json()
                usage = data.get("usage", {})
                span.set_attribute("gen_ai.response.model", data.get("model", LLM_MODEL))
                span.set_attribute("gen_ai.usage.input_tokens", usage.get("prompt_tokens", 0))
                span.set_attribute("gen_ai.usage.output_tokens", usage.get("completion_tokens", 0))
                span.set_attribute("gen_ai.response.finish_reasons", [c.get("finish_reason", "") for c in data["choices"]])
                span.set_attribute("llm.attempts", attempt)
                llm_tokens.record(usage.get("prompt_tokens", 0), {**attrs, "gen_ai.token.type": "input"})
                llm_tokens.record(usage.get("completion_tokens", 0), {**attrs, "gen_ai.token.type": "output"})
                llm_duration.record(time.perf_counter() - start, attrs)
                return data
            except (httpx.TimeoutException, httpx.HTTPStatusError) as e:
                reason = "timeout" if isinstance(e, httpx.TimeoutException) else f"http_{e.response.status_code}"
                last_err = reason
                span.add_event("llm.attempt_failed", {"attempt": attempt, "reason": reason})
                if attempt < LLM_ATTEMPTS:
                    llm_retries.add(1, {**attrs, "error.type": reason})
                    # Den här raden är den som "förklarar" incidenten i Loki
                    log.warning("llm_request_retry model=%s attempt=%d reason=%s", LLM_MODEL, attempt + 1, reason)
        llm_duration.record(time.perf_counter() - start, {**attrs, "error.type": last_err})
        span.set_status(Status(StatusCode.ERROR, f"LLM failed after {LLM_ATTEMPTS} attempts: {last_err}"))
        log.error("llm_request_failed model=%s attempts=%d reason=%s", LLM_MODEL, LLM_ATTEMPTS, last_err)
        raise HTTPException(502, f"LLM unavailable ({last_err})")


@app.post("/chat")
async def chat(req: ChatReq):
    with tracer.start_as_current_span("rag.pipeline") as pipe:
        pipe.set_attribute("rag.intent", req.intent or "general")
        try:
            with tracer.start_as_current_span("rag.embed") as s:
                vec = embed(req.question)
                s.set_attribute("rag.embedding.dimensions", DIM)

            with tracer.start_as_current_span("rag.retrieve") as s:
                t0 = time.perf_counter()
                s.set_attribute("db.system.name", "qdrant")
                s.set_attribute("db.collection.name", COLLECTION)
                s.set_attribute("rag.top_k", 8)
                r = await http.post(f"{QDRANT}/collections/{COLLECTION}/points/query",
                                    json={"query": vec, "limit": 8, "with_payload": True})
                r.raise_for_status()
                hits = r.json()["result"]["points"]
                elapsed = time.perf_counter() - t0
                retrieval_duration.record(elapsed, {"db.system.name": "qdrant"})
                s.set_attribute("rag.documents.retrieved", len(hits))
                log.info("retrieval_done docs=%d ms=%d", len(hits), elapsed * 1000)

            with tracer.start_as_current_span("rag.rerank") as s:
                q = set(re.findall(r"\w+", req.question.lower()))
                for h in hits:
                    words = set(re.findall(r"\w+", h["payload"]["text"].lower()))
                    h["rerank"] = h["score"] + 0.15 * len(q & words) + (0.2 if h["payload"]["topic"] == req.intent else 0)
                top = sorted(hits, key=lambda h: h["rerank"], reverse=True)[:3]
                s.set_attribute("rag.documents.kept", len(top))
                retrieved_docs.record(len(top))

            data = await call_llm(req.question, [h["payload"]["text"] for h in top])
            answer = data["choices"][0]["message"]["content"]
            rag_requests.add(1, {"outcome": "ok"})
            return {"answer": answer, "sources": [{"topic": h["payload"]["topic"], "score": round(h["rerank"], 3)} for h in top],
                    "usage": data.get("usage", {})}
        except HTTPException:
            rag_requests.add(1, {"outcome": "llm_error"})
            pipe.set_status(Status(StatusCode.ERROR))
            raise
        except Exception as e:
            rag_requests.add(1, {"outcome": "error"})
            pipe.record_exception(e)
            pipe.set_status(Status(StatusCode.ERROR, str(e)))
            log.exception("rag_failed")
            raise HTTPException(500, "rag pipeline failed") from e
