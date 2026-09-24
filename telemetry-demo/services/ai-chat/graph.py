"""
Agenten: en LangGraph-graf med verktyg. Samma form som de flesta RAG-agenter.

    START → guard_input ─┬─(blockerad)──────────────────────────→ respond → END
                         └→ agent ─┬─(tool_calls)→ tools ─→ agent  (loop)
                                   └─(svar klart)─────────→ respond → END

  guard_input   validerar frågan, maskerar PII, klassar intent
  agent         LLM:en (Gemma via vLLM) väljer verktyg eller svarar
  tools         kör alla tool calls parallellt: search_documents (rag-api), get_project_insight (algorithm)
  respond       sammanställer svaret och källorna

Varje nod dekoreras med @tel.node(...). Det är hela instrumenteringen av grafen.
"""

import asyncio
import json
import logging
import operator
import os
import re
from typing import Annotated, TypedDict

import httpx
from langgraph.graph import END, START, StateGraph

from agent_otel import AgentTelemetry

LLM_BASE = os.getenv("LLM_BASE_URL", "http://vllm-gemma:8000/v1")
LLM_MODEL = os.getenv("LLM_MODEL", "gemma")
LLM_TIMEOUT = float(os.getenv("LLM_TIMEOUT_S", "2.5"))
LLM_ATTEMPTS = int(os.getenv("LLM_MAX_ATTEMPTS", "2"))
RAG_URL = os.getenv("RAG_API_URL", "http://rag-api:8080")
ALGO_URL = os.getenv("ALGORITHM_URL", "http://algorithm:8080")

log = logging.getLogger("ai-chat.graph")
log.setLevel(logging.INFO)
tel = AgentTelemetry("chat-agent")
http = httpx.AsyncClient(timeout=10)

SYSTEM = ("Du är en assistent för projekt och observability. Använd verktygen för att hämta underlag "
          "och svara kort på svenska. Hitta inte på siffror.")
INTENTS = {
    "projekt": ["projekt", "prognos", "budget", "risk", "leverans", "status", "p-1"],
    "traces": ["trace", "span", "tempo", "propagation", "waterfall"],
    "logs": ["log", "loki", "logg"],
    "metrics": ["metric", "p95", "prometheus", "counter", "histogram", "cardinality", "exemplar"],
    "agent": ["agent", "langgraph", "verktyg", "tool", "nod"],
    "infra": ["gpu", "cpu", "dgx", "minne", "container"],
}
EMAIL = re.compile(r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}")

TOOLS = [
    {"type": "function", "function": {
        "name": "search_documents", "description": "Sök i kunskapsbasen (hybrid BM25 + vektor).",
        "parameters": {"type": "object", "required": ["query"], "properties": {
            "query": {"type": "string"}, "top_k": {"type": "integer", "default": 5}}}}},
    {"type": "function", "function": {
        "name": "get_project_insight", "description": "Hämta förberäknad prognos, risk eller status för ett projekt.",
        "parameters": {"type": "object", "required": ["project_id", "metric"], "properties": {
            "project_id": {"type": "string", "pattern": "^P-\\d+$"},
            "metric": {"type": "string", "enum": ["forecast", "risk", "status"]}}}}},
]


class LLMUnavailable(Exception):
    pass


class ToolArgumentError(Exception):
    pass


class State(TypedDict, total=False):
    question: str
    conversation_id: str
    intent: str
    blocked: str
    messages: Annotated[list, operator.add]
    sources: Annotated[list, operator.add]
    tool_log: Annotated[list, operator.add]
    trail: Annotated[list, operator.add]
    answer: str
    usage: Annotated[list, operator.add]


# ---- noder -----------------------------------------------------------------------------------
@tel.node("guard_input")
async def guard_input(state: State, config):
    q = state["question"].strip()
    if not q:
        return {"blocked": "empty_question", "intent": "none"}
    if len(q) > 2000:
        return {"blocked": "too_long", "intent": "none"}
    masked = EMAIL.sub("[email]", q)  # PII lämnar aldrig tjänsten mot modellen
    ql = q.lower()
    intent = next((k for k, words in INTENTS.items() if any(w in ql for w in words)), "general")
    return {"intent": intent, "messages": [{"role": "system", "content": SYSTEM}, {"role": "user", "content": masked}]}


@tel.node("agent")
async def agent(state: State, config):
    body = {"model": LLM_MODEL, "messages": state["messages"], "tools": TOOLS, "max_tokens": 256, "temperature": 0.2}
    async with tel.llm_call(LLM_MODEL, state["messages"], TOOLS) as call:
        last = None
        for attempt in range(1, LLM_ATTEMPTS + 1):
            try:
                r = await http.post(f"{LLM_BASE}/chat/completions", json=body, timeout=LLM_TIMEOUT)
                r.raise_for_status()
                data = r.json()
                call.span.set_attribute("llm.attempts", attempt)
                call.response(data)
                break
            except (httpx.TimeoutException, httpx.HTTPStatusError) as e:
                last = "timeout" if isinstance(e, httpx.TimeoutException) else f"http_{e.response.status_code}"
                call.span.add_event("llm.attempt_failed", {"attempt": attempt, "reason": last})
                if attempt < LLM_ATTEMPTS:
                    log.warning("llm_request_retry model=%s attempt=%d reason=%s", LLM_MODEL, attempt + 1, last)
        else:
            raise LLMUnavailable(f"{LLM_MODEL} failed after {LLM_ATTEMPTS} attempts: {last}")
    msg = data["choices"][0]["message"]
    return {"messages": [msg], "usage": [data.get("usage", {})]}


def _parse_args(raw: str, required: list[str]) -> dict:
    try:
        args = json.loads(raw or "{}")
    except json.JSONDecodeError as e:
        raise ToolArgumentError(f"invalid JSON arguments: {e.msg} at pos {e.pos}") from e
    missing = [k for k in required if k not in args]
    if missing:
        raise ToolArgumentError(f"missing arguments: {missing}")
    return args


async def search_documents(args: dict) -> dict:
    r = await http.post(f"{RAG_URL}/search", json={"query": args["query"], "top_k": int(args.get("top_k", 5))})
    r.raise_for_status()
    return r.json()


async def get_project_insight(args: dict) -> dict:
    r = await http.get(f"{ALGO_URL}/insight/{args['project_id']}", params={"metric": args["metric"]})
    r.raise_for_status()
    return r.json()


REGISTRY = {
    "search_documents": (search_documents, ["query"]),
    "get_project_insight": (get_project_insight, ["project_id", "metric"]),
}


async def run_tool(call: dict) -> tuple[dict, dict, list]:
    name, raw, cid = call["function"]["name"], call["function"].get("arguments", ""), call["id"]
    entry = {"tool": name, "ok": True}
    try:
        async with tel.tool_call(name, cid, raw) as t:
            fn, required = REGISTRY[name]
            result = await fn(_parse_args(raw, required))
            t.result(result)
    except Exception as e:  # noqa: BLE001 – felet går tillbaka till modellen, precis som LangGraphs ToolNode
        msg = str(e).splitlines()[0].split(" for url ")[0]
        result, entry = {"error": f"{type(e).__name__}: {msg}"}, {"tool": name, "ok": False, "error": type(e).__name__}
    sources = [{"title": d["title"], "similarity": d.get("similarity")} for d in result.get("documents", [])[:3]]
    msg = {"role": "tool", "tool_call_id": cid, "name": name, "content": json.dumps(result, ensure_ascii=False)}
    return msg, entry, sources


@tel.node("tools")
async def tools(state: State, config):
    calls = state["messages"][-1].get("tool_calls", [])
    results = await asyncio.gather(*(run_tool(c) for c in calls))
    return {"messages": [m for m, _, _ in results], "tool_log": [e for _, e, _ in results],
            "sources": [s for _, _, src in results for s in src]}


@tel.node("respond")
async def respond(state: State, config):
    if state.get("blocked"):
        return {"answer": f"Frågan kunde inte behandlas ({state['blocked']})."}
    return {"answer": state["messages"][-1].get("content") or ""}


# ---- kanter ----------------------------------------------------------------------------------
def after_guard(state: State) -> str:
    return "respond" if state.get("blocked") else "agent"


def after_agent(state: State) -> str:
    return "tools" if state["messages"][-1].get("tool_calls") else "respond"


def build():
    g = StateGraph(State)
    g.add_node("guard_input", guard_input)
    g.add_node("agent", agent)
    g.add_node("tools", tools)
    g.add_node("respond", respond)
    g.add_edge(START, "guard_input")
    g.add_conditional_edges("guard_input", after_guard, {"agent": "agent", "respond": "respond"})
    g.add_conditional_edges("agent", after_agent, {"tools": "tools", "respond": "respond"})
    g.add_edge("tools", "agent")
    g.add_edge("respond", END)
    return g.compile()


GRAPH = build()
