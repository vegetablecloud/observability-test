"""
llm-server (mock av vLLM)

Den här tjänsten spelar rollen av en TREDJEPARTSKOMPONENT som du inte äger.
Den är medvetet INTE instrumenterad med OpenTelemetry-SDK:t. I stället gör den
som vLLM, Qdrant, Postgres och de flesta färdiga produkter gör:

  * exponerar Prometheus-metrics på /metrics  -> någon måste HÄMTA (pull)
  * pratar ett standard-API (OpenAI-kompatibelt /v1/chat/completions)

Den som anropar (ai-chat) skapar client-spans runt anropet, så i traces syns
ändå hur lång tid LLM-anropet tog.

Port 8000 : OpenAI-API + vLLM-lika metrics (vllm:*)
Port 9400 : Simulerad dcgm-exporter (DCGM_FI_DEV_*) så att GPU-panelerna har
            data även utan riktig GPU. På DGX Spark kör du i stället profilen
            "gpu" med riktig vLLM + dcgm-exporter.

Incident-simulering:
  POST /chaos/slow    -> LLM-svar tar 2-4 s, GPU går mot 100 %
  POST /chaos/error   -> 30 % av anropen ger 500
  POST /chaos/normal  -> tillbaka till normalläge
"""

import asyncio
import math
import os
import random
import time
import uuid

from fastapi import FastAPI, HTTPException
from prometheus_client import (
    CollectorRegistry,
    Counter,
    Gauge,
    Histogram,
    make_asgi_app,
    start_http_server,
)
from prometheus_client.core import GaugeMetricFamily
from pydantic import BaseModel

MODEL = os.getenv("MODEL_NAME", "local-model")
SIMULATE_GPU = os.getenv("SIMULATE_GPU", "true").lower() == "true"

STATE = {"mode": os.getenv("CHAOS_MODE", "normal"), "since": time.time()}

# ---------------------------------------------------------------------------
# vLLM-lika metrics (samma namn som riktig vLLM exponerar)
# ---------------------------------------------------------------------------
vllm_registry = CollectorRegistry()
LBL = ["model_name"]
running = Gauge("vllm:num_requests_running", "Requests currently running on GPU", LBL, registry=vllm_registry)
waiting = Gauge("vllm:num_requests_waiting", "Requests waiting to be processed", LBL, registry=vllm_registry)
kv_cache = Gauge("vllm:kv_cache_usage_perc", "KV-cache usage. 1 means 100 percent usage", LBL, registry=vllm_registry)
prompt_tokens = Counter("vllm:prompt_tokens", "Number of prefill tokens processed", LBL, registry=vllm_registry)
gen_tokens = Counter("vllm:generation_tokens", "Number of generation tokens processed", LBL, registry=vllm_registry)
req_success = Counter("vllm:request_success", "Count of successfully processed requests", LBL + ["finished_reason"], registry=vllm_registry)
LAT_BUCKETS = (0.05, 0.1, 0.25, 0.5, 1, 1.5, 2, 3, 4, 6, 10)
ttft = Histogram("vllm:time_to_first_token_seconds", "Time to first token", LBL, buckets=LAT_BUCKETS, registry=vllm_registry)
e2e = Histogram("vllm:e2e_request_latency_seconds", "End to end request latency", LBL, buckets=LAT_BUCKETS, registry=vllm_registry)
tpot = Histogram("vllm:time_per_output_token_seconds", "Time per output token", LBL,
                 buckets=(0.005, 0.01, 0.02, 0.04, 0.08, 0.15, 0.3), registry=vllm_registry)

for g in (running, waiting, kv_cache):
    g.labels(MODEL).set(0)


# ---------------------------------------------------------------------------
# Simulerad dcgm-exporter (samma metric-namn som NVIDIA dcgm-exporter)
# ---------------------------------------------------------------------------
class GpuSim:
    """Räknar fram GPU-värden vid varje scrape, kopplat till last och chaos-läge."""

    TOTAL_MIB = 128 * 1024  # DGX Spark: 128 GB unified memory

    def collect(self):
        load = running.labels(MODEL)._value.get() + waiting.labels(MODEL)._value.get()
        t = time.time()
        wobble = (random.random() - 0.5) * 6
        if STATE["mode"] == "slow":
            util = min(100.0, 97 + random.random() * 3)
            mem_frac = 0.97
        else:
            util = max(3.0, min(95.0, 38 + load * 9 + 6 * math.sin(t / 40) + wobble))
            mem_frac = 0.71 + 0.01 * math.sin(t / 90)
        used = self.TOTAL_MIB * mem_frac
        labels = ["gpu", "UUID", "modelName", "Hostname"]
        vals = ["0", "GPU-simulated-0000", "NVIDIA GB10 (simulated)", "dgx-spark-sim"]

        def g(name, doc, v):
            m = GaugeMetricFamily(name, doc, labels=labels)
            m.add_metric(vals, v)
            return m

        yield g("DCGM_FI_DEV_GPU_UTIL", "GPU utilization (in %).", util)
        yield g("DCGM_FI_DEV_FB_USED", "Framebuffer memory used (in MiB).", used)
        yield g("DCGM_FI_DEV_FB_FREE", "Framebuffer memory free (in MiB).", self.TOTAL_MIB - used)
        yield g("DCGM_FI_DEV_GPU_TEMP", "GPU temperature (in C).", 48 + util * 0.3 + wobble / 3)
        yield g("DCGM_FI_DEV_POWER_USAGE", "Power draw (in W).", 40 + util * 1.1 + wobble)


# ---------------------------------------------------------------------------
# API
# ---------------------------------------------------------------------------
app = FastAPI(title="llm-server (vLLM mock)")
app.mount("/metrics", make_asgi_app(registry=vllm_registry))


class Msg(BaseModel):
    role: str
    content: str


class ChatReq(BaseModel):
    model: str | None = None
    messages: list[Msg]
    max_tokens: int | None = 256
    temperature: float | None = 0.2


def _compose_answer(messages: list[Msg]) -> str:
    """Bygger ett trovärdigt svar av kontexten som RAG-steget skickade med."""
    system = next((m.content for m in messages if m.role == "system"), "")
    question = next((m.content for m in reversed(messages) if m.role == "user"), "")
    ctx = [l.strip("- ").strip() for l in system.splitlines() if l.startswith("- ")]
    if not ctx:
        return f"Jag har ingen kontext om \"{question}\", men metrics, traces och logs hjälper dig hitta svaret."
    picked = ctx[:2]
    return "Kort svar: " + " ".join(picked)


@app.get("/health")
def health():
    return {"ok": True, "mode": STATE["mode"]}


@app.get("/v1/models")
def models():
    return {"object": "list", "data": [{"id": MODEL, "object": "model", "owned_by": "demo"}]}


@app.post("/chaos/{mode}")
def chaos(mode: str):
    if mode not in ("normal", "slow", "error"):
        raise HTTPException(400, "mode must be normal|slow|error")
    STATE["mode"], STATE["since"] = mode, time.time()
    return STATE


@app.post("/v1/chat/completions")
async def chat(req: ChatReq):
    lm = MODEL
    waiting.labels(lm).inc()
    # lite kö-tid när det är mycket last
    await asyncio.sleep(random.uniform(0.0, 0.03))
    waiting.labels(lm).dec()
    running.labels(lm).inc()
    kv_cache.labels(lm).set(min(1.0, 0.15 + running.labels(lm)._value.get() * 0.08 + (0.8 if STATE["mode"] == "slow" else 0)))
    start = time.perf_counter()
    try:
        mode = STATE["mode"]
        if mode == "error" and random.random() < 0.3:
            raise HTTPException(500, "CUDA error: out of memory (simulated)")

        answer = _compose_answer(req.messages)
        n_prompt = sum(len(m.content.split()) for m in req.messages) * 4 // 3
        n_gen = max(8, len(answer.split()) * 4 // 3)

        if mode == "slow":
            # GPU mättad: allt blir långsammare och ~1/3 av anropen "fastnar" > timeout.
            first = random.uniform(0.8, 1.4) + (random.uniform(1.4, 2.2) if random.random() < 0.35 else 0)
            per_tok = random.uniform(0.008, 0.015)
        else:
            first = random.uniform(0.05, 0.14)
            per_tok = random.uniform(0.004, 0.009)

        await asyncio.sleep(first)
        ttft.labels(lm).observe(first)
        await asyncio.sleep(per_tok * n_gen)
        tpot.labels(lm).observe(per_tok)

        prompt_tokens.labels(lm).inc(n_prompt)
        gen_tokens.labels(lm).inc(n_gen)
        req_success.labels(lm, "stop").inc()
        return {
            "id": "chatcmpl-" + uuid.uuid4().hex[:12],
            "object": "chat.completion",
            "created": int(time.time()),
            "model": lm,
            "choices": [{"index": 0, "finish_reason": "stop", "message": {"role": "assistant", "content": answer}}],
            "usage": {"prompt_tokens": n_prompt, "completion_tokens": n_gen, "total_tokens": n_prompt + n_gen},
        }
    finally:
        e2e.labels(lm).observe(time.perf_counter() - start)
        running.labels(lm).dec()
        kv_cache.labels(lm).set(max(0.0, 0.15 + running.labels(lm)._value.get() * 0.08 + (0.8 if STATE["mode"] == "slow" else 0)))


@app.on_event("startup")
def _start_gpu_exporter():
    if SIMULATE_GPU:
        reg = CollectorRegistry()
        reg.register(GpuSim())
        start_http_server(9400, registry=reg)
