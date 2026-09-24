"""
vLLM-mock: spelar två vLLM-instanser, som i er riktiga stack.

  MODEL_KIND=chat        "gemma"   – OpenAI-kompatibelt /v1/chat/completions MED tool calling
  MODEL_KIND=embedding   "harrier" – /v1/embeddings

Den här tjänsten är en TREDJEPARTSKOMPONENT som du inte äger. Den är medvetet INTE
instrumenterad med OpenTelemetry-SDK:t. Den gör som riktig vLLM:

  * exponerar Prometheus-metrics på /metrics (vllm:*)  -> Collectorn HÄMTAR (pull)
  * pratar OpenAI-API:t

Anroparen (ai-chat, rag-api) skapar client-spans runt anropen, så traces visar ändå
hur lång tid varje LLM- och embedding-anrop tog.

Port 8000 : API + vllm:*-metrics
Port 9400 : simulerad dcgm-exporter (DCGM_FI_DEV_*) om SIMULATE_GPU=true. På DGX Spark kör du
            i stället profilen "gpu" med riktig vLLM + dcgm-exporter.

Chaos (sätts för hela stacken via frontend: POST /demo/chaos/{mode}):
  slow      GPU mättad: svaren tar 1-4 s -> timeouts + retry i ai-chat
  error     30 % av anropen ger 500
  loop      chat-modellen slutar aldrig anropa verktyg -> LangGraph når recursion_limit
  bad_args  hälften av tool calls får trasig JSON -> verktygsnoden fångar felet
"""

import asyncio
import hashlib
import json
import math
import os
import random
import re
import time
import uuid

from fastapi import FastAPI, HTTPException
from prometheus_client import CollectorRegistry, Counter, Gauge, Histogram, make_asgi_app, start_http_server
from prometheus_client.core import GaugeMetricFamily
from pydantic import BaseModel

MODEL = os.getenv("MODEL_NAME", "gemma")
KIND = os.getenv("MODEL_KIND", "chat")
SIMULATE_GPU = os.getenv("SIMULATE_GPU", "false").lower() == "true"
EMBED_DIM = int(os.getenv("EMBED_DIM", "384"))
CHAOS_MODES = {"normal", "slow", "error", "loop", "bad_args"}

STATE = {"mode": "normal", "since": time.time()}

# ---------------------------------------------------------------------------
# vLLM-metrics (samma namn som riktig vLLM exponerar)
# ---------------------------------------------------------------------------
reg = CollectorRegistry()
LBL = ["model_name"]
running = Gauge("vllm:num_requests_running", "Requests currently running on GPU", LBL, registry=reg)
waiting = Gauge("vllm:num_requests_waiting", "Requests waiting to be processed", LBL, registry=reg)
kv_cache = Gauge("vllm:kv_cache_usage_perc", "KV-cache usage. 1 means 100 percent usage", LBL, registry=reg)
prompt_tokens = Counter("vllm:prompt_tokens", "Number of prefill tokens processed", LBL, registry=reg)
gen_tokens = Counter("vllm:generation_tokens", "Number of generation tokens processed", LBL, registry=reg)
req_success = Counter("vllm:request_success", "Count of successfully processed requests", LBL + ["finished_reason"], registry=reg)
prefix_hits = Counter("vllm:prefix_cache_hits", "Prefix cache hits, in terms of number of cached tokens", LBL, registry=reg)
prefix_queries = Counter("vllm:prefix_cache_queries", "Prefix cache queries, in terms of number of queried tokens", LBL, registry=reg)
LAT = (0.01, 0.025, 0.05, 0.1, 0.25, 0.5, 1, 1.5, 2, 3, 4, 6, 10)
ttft = Histogram("vllm:time_to_first_token_seconds", "Time to first token", LBL, buckets=LAT, registry=reg)
e2e = Histogram("vllm:e2e_request_latency_seconds", "End to end request latency", LBL, buckets=LAT, registry=reg)
queue_time = Histogram("vllm:request_queue_time_seconds", "Time spent waiting in queue", LBL, buckets=LAT, registry=reg)
tpot = Histogram("vllm:time_per_output_token_seconds", "Time per output token", LBL,
                 buckets=(0.005, 0.01, 0.02, 0.04, 0.08, 0.15, 0.3), registry=reg)
for g in (running, waiting, kv_cache):
    g.labels(MODEL).set(0)


class GpuSim:
    """Räknar fram GPU-värden vid varje scrape, kopplat till last och chaos-läge."""

    TOTAL_MIB = 128 * 1024  # DGX Spark: 128 GB unified memory

    def collect(self):
        load = running.labels(MODEL)._value.get() + waiting.labels(MODEL)._value.get()
        t = time.time()
        wobble = (random.random() - 0.5) * 6
        if STATE["mode"] == "slow":
            util, mem_frac = min(100.0, 97 + random.random() * 3), 0.97
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
        yield g("DCGM_FI_DEV_SM_CLOCK", "SM clock frequency (in MHz).", 2400 - (300 if util > 95 else 0) + wobble * 5)


# ---------------------------------------------------------------------------
# API
# ---------------------------------------------------------------------------
app = FastAPI(title=f"vllm-mock ({MODEL})")
app.mount("/metrics", make_asgi_app(registry=reg))


class ChatReq(BaseModel):
    model: str | None = None
    messages: list[dict]
    tools: list[dict] | None = None
    max_tokens: int | None = 256
    temperature: float | None = 0.2


class EmbedReq(BaseModel):
    model: str | None = None
    input: str | list[str]


@app.get("/health")
def health():
    return {"ok": True, "model": MODEL, "mode": STATE["mode"]}


@app.get("/v1/models")
def models():
    return {"object": "list", "data": [{"id": MODEL, "object": "model", "owned_by": "demo"}]}


@app.post("/chaos/{mode}")
def chaos(mode: str):
    STATE["mode"], STATE["since"] = (mode if mode in CHAOS_MODES else "normal"), time.time()
    return STATE


def _tokens(text: str) -> int:
    return max(1, len(text.split()) * 4 // 3)


async def _run(n_prompt: int, n_gen: int):
    """Gemensam 'GPU-körning': kö, time-to-first-token, generering och alla vllm:*-metrics."""
    lm = MODEL
    waiting.labels(lm).inc()
    q = random.uniform(0.0, 0.02) + (random.uniform(0.2, 0.6) if STATE["mode"] == "slow" else 0)
    await asyncio.sleep(q)
    queue_time.labels(lm).observe(q)
    waiting.labels(lm).dec()
    running.labels(lm).inc()
    kv_cache.labels(lm).set(min(1.0, 0.15 + running.labels(lm)._value.get() * 0.08 + (0.8 if STATE["mode"] == "slow" else 0)))
    start = time.perf_counter()
    try:
        if STATE["mode"] == "error" and random.random() < 0.3:
            raise HTTPException(500, "CUDA error: out of memory (simulated)")
        if STATE["mode"] == "slow":
            first = random.uniform(0.8, 1.4) + (random.uniform(1.4, 2.2) if random.random() < 0.35 else 0)
            per_tok = random.uniform(0.008, 0.015)
        else:
            first = random.uniform(0.04, 0.12) if KIND == "chat" else random.uniform(0.008, 0.025)
            per_tok = random.uniform(0.004, 0.009)
        await asyncio.sleep(first)
        ttft.labels(lm).observe(first)
        if n_gen:
            await asyncio.sleep(per_tok * n_gen)
            tpot.labels(lm).observe(per_tok)
        prompt_tokens.labels(lm).inc(n_prompt)
        gen_tokens.labels(lm).inc(n_gen)
        cached = int(n_prompt * random.uniform(0.3, 0.7))  # systemprompten återanvänds -> prefix cache
        prefix_queries.labels(lm).inc(n_prompt)
        prefix_hits.labels(lm).inc(cached)
        req_success.labels(lm, "stop").inc()
    finally:
        e2e.labels(lm).observe(time.perf_counter() - start + q)
        running.labels(lm).dec()
        kv_cache.labels(lm).set(max(0.0, 0.15 + running.labels(lm)._value.get() * 0.08 + (0.8 if STATE["mode"] == "slow" else 0)))


# ---- chat + tool calling ----------------------------------------------------
INSIGHT_WORDS = ("projekt", "prognos", "kpi", "budget", "risk", "status", "försen", "leverans", "kostnad")


def _plan_tool_calls(question: str, tools: list[str]) -> list[dict]:
    """Så 'resonerar' mock-modellen: vilka verktyg behövs för frågan?"""
    q = question.lower()
    calls = []
    if "search_documents" in tools:
        calls.append(("search_documents", {"query": question, "top_k": 5}))
    if "get_project_insight" in tools and any(w in q for w in INSIGHT_WORDS):
        pid = (re.search(r"p-?\d+", q) or re.search(r"\d+", q))
        project = f"P-{pid.group(0).strip('p-')}" if pid else random.choice(["P-101", "P-102", "P-103", "P-104"])
        metric = "forecast" if "prognos" in q else ("risk" if "risk" in q else "status")
        calls.append(("get_project_insight", {"project_id": project, "metric": metric}))
    out = []
    for name, args in calls:
        raw = json.dumps(args, ensure_ascii=False)
        if STATE["mode"] == "bad_args" and random.random() < 0.5:
            raw = raw[: len(raw) // 2]  # modellen "tappar bort sig" mitt i JSON-argumenten
        out.append({"id": "call_" + uuid.uuid4().hex[:10], "type": "function", "function": {"name": name, "arguments": raw}})
    return out


def _answer(question: str, tool_msgs: list[dict]) -> str:
    facts = []
    for m in tool_msgs:
        try:
            data = json.loads(m.get("content") or "{}")
        except json.JSONDecodeError:
            continue
        if data.get("error"):
            facts.append(f"(verktyget {m.get('name', '?')} misslyckades: {data['error']})")
        for d in data.get("documents", [])[:2]:
            facts.append(d.get("text", ""))
        if "insight" in data:
            facts.append(data["insight"])
    if not facts:
        return f"Jag hittade inget underlag för \"{question}\"."
    return "Kort svar: " + " ".join(facts)


@app.post("/v1/chat/completions")
async def chat(req: ChatReq):
    if KIND != "chat":
        raise HTTPException(400, f"{MODEL} is an embedding model")
    msgs = req.messages
    last_user = max(i for i, m in enumerate(msgs) if m.get("role") == "user")
    tool_msgs = [m for m in msgs[last_user + 1:] if m.get("role") == "tool"]
    question = msgs[last_user].get("content", "")
    tool_names = [t["function"]["name"] for t in (req.tools or [])]

    if tool_names and (STATE["mode"] == "loop" or not tool_msgs):
        calls = _plan_tool_calls(question, tool_names) if STATE["mode"] != "loop" else [
            {"id": "call_" + uuid.uuid4().hex[:10], "type": "function",
             "function": {"name": "search_documents", "arguments": json.dumps({"query": f"{question} (försök {len(tool_msgs) + 1})"})}}]
        message = {"role": "assistant", "content": None, "tool_calls": calls}
        finish, n_gen = "tool_calls", 20 * len(calls)
    else:
        message = {"role": "assistant", "content": _answer(question, tool_msgs)}
        finish, n_gen = "stop", _tokens(message["content"])

    n_prompt = sum(_tokens(str(m.get("content") or "")) for m in msgs) + 60 * len(tool_names)
    await _run(n_prompt, n_gen)
    return {
        "id": "chatcmpl-" + uuid.uuid4().hex[:12], "object": "chat.completion", "created": int(time.time()), "model": MODEL,
        "choices": [{"index": 0, "finish_reason": finish, "message": message}],
        "usage": {"prompt_tokens": n_prompt, "completion_tokens": n_gen, "total_tokens": n_prompt + n_gen},
    }


# ---- embeddings -------------------------------------------------------------
def embed(text: str) -> list[float]:
    """Deterministisk 'hash-embedding': ingen modell att ladda ner, men ger vettig likhet."""
    v = [0.0] * EMBED_DIM
    words = re.findall(r"\w+", text.lower())
    for g in words + [w[i:i + 4] for w in words for i in range(max(1, len(w) - 3))]:
        h = int(hashlib.md5(g.encode()).hexdigest(), 16)
        v[h % EMBED_DIM] += 1.0 if (h >> 8) & 1 else -1.0
    n = math.sqrt(sum(x * x for x in v)) or 1.0
    return [x / n for x in v]


@app.post("/v1/embeddings")
async def embeddings(req: EmbedReq):
    if KIND != "embedding":
        raise HTTPException(400, f"{MODEL} is a chat model")
    texts = [req.input] if isinstance(req.input, str) else req.input
    n = sum(_tokens(t) for t in texts)
    await _run(n, 0)
    return {"object": "list", "model": MODEL, "usage": {"prompt_tokens": n, "total_tokens": n},
            "data": [{"object": "embedding", "index": i, "embedding": embed(t)} for i, t in enumerate(texts)]}


@app.on_event("startup")
def _start_gpu_exporter():
    if SIMULATE_GPU:
        r = CollectorRegistry()
        r.register(GpuSim())
        start_http_server(9400, registry=r)
