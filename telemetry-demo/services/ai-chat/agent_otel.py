"""
agent_otel – OpenTelemetry för en LangGraph-agent. Ingen magi, ~150 rader, går att lyfta in i ert projekt.

Vad det ger (enligt OTel GenAI semantic conventions där de finns):

  invoke_agent chat-agent                 root: en span per agentkörning
   ├ node guard_input                     en span per LangGraph-nod (steg, triggers, nästa nod)
   ├ node agent
   │  └ chat gemma                        LLM-anropet: modell, tokens, finish_reason, input/output
   ├ node tools
   │  ├ execute_tool search_documents     verktyget: namn, argument, resultat, fel
   │  └ execute_tool get_project_insight
   ├ node agent
   │  └ chat gemma
   └ node respond

Metrics (labels är få och stabila, aldrig id:n):
  langgraph.node.duration{langgraph.node, outcome}     hur lång tid tar varje nod?
  langgraph.transitions{langgraph.from, langgraph.to}  vilka kanter i grafen används? (-> node graph)
  agent.tool.calls{gen_ai.tool.name, outcome}          hur ofta och hur ofta fel?
  agent.tool.duration{gen_ai.tool.name}
  agent.runs{outcome} · agent.run.duration · agent.run.steps

Användning:
    tel = AgentTelemetry("chat-agent")
    @tel.node("agent")
    async def agent(state, config): ...
    async with tel.llm_call(model, messages) as call: ...; call.response(data)
    async with tel.tool_call(name, call_id, args) as t: ...; t.result(obj)

Innehåll (prompter, svar, verktygsargument) loggas på spans när
OTEL_INSTRUMENTATION_GENAI_CAPTURE_MESSAGE_CONTENT=true. Klipps vid 2000 tecken.
Collectorn redigerar e-postadresser innan lagring. Stäng av i prod om innehållet är känsligt.
"""

import json
import logging
import os
import time
from contextlib import asynccontextmanager
from functools import wraps

from opentelemetry import metrics, trace
from opentelemetry.trace import SpanKind, Status, StatusCode

CAPTURE = os.getenv("OTEL_INSTRUMENTATION_GENAI_CAPTURE_MESSAGE_CONTENT", "false").lower() == "true"
MAX_CHARS = 2000
SEC = [0.005, 0.01, 0.025, 0.05, 0.1, 0.25, 0.5, 1, 1.5, 2, 3, 4, 6, 10, 15]

log = logging.getLogger("ai-chat.agent")
log.setLevel(logging.INFO)


def clip(value) -> str:
    s = value if isinstance(value, str) else json.dumps(value, ensure_ascii=False, default=str)
    return s if len(s) <= MAX_CHARS else s[:MAX_CHARS] + "…"


class _Call:
    def __init__(self, span):
        self.span = span
        self.data = None

    def response(self, data):
        self.data = data

    def result(self, data):
        self.data = data


class AgentTelemetry:
    def __init__(self, agent_name: str):
        self.agent = agent_name
        self.tracer = trace.get_tracer("ai-chat.agent")
        m = metrics.get_meter("ai-chat.agent")
        self.node_duration = m.create_histogram("langgraph.node.duration", unit="s", description="Tid per LangGraph-nod",
                                                explicit_bucket_boundaries_advisory=SEC)
        self.transitions = m.create_counter("langgraph.transitions", unit="{transition}", description="Använda kanter i grafen")
        self.tool_calls = m.create_counter("agent.tool.calls", unit="{call}", description="Verktygsanrop per verktyg och utfall")
        self.tool_duration = m.create_histogram("agent.tool.duration", unit="s", description="Tid per verktygsanrop",
                                                explicit_bucket_boundaries_advisory=SEC)
        self.runs = m.create_counter("agent.runs", unit="{run}", description="Agentkörningar per utfall")
        self.run_duration = m.create_histogram("agent.run.duration", unit="s", description="Tid för hela agentkörningen",
                                               explicit_bucket_boundaries_advisory=SEC)
        self.run_steps = m.create_histogram("agent.run.steps", unit="{step}", description="Antal nod-steg per körning",
                                            explicit_bucket_boundaries_advisory=[1, 2, 3, 4, 5, 6, 8, 10, 12, 16])
        self.llm_duration = m.create_histogram("gen_ai.client.operation.duration", unit="s", description="LLM-anropets längd",
                                               explicit_bucket_boundaries_advisory=SEC)
        self.llm_tokens = m.create_histogram("gen_ai.client.token.usage", unit="{token}", description="Tokens per anrop",
                                             explicit_bucket_boundaries_advisory=[8, 16, 32, 64, 128, 256, 512, 1024, 2048, 4096])

    # ---- en körning -----------------------------------------------------------------------
    @asynccontextmanager
    async def run(self, conversation_id: str, question: str):
        with self.tracer.start_as_current_span(f"invoke_agent {self.agent}", kind=SpanKind.INTERNAL) as span:
            span.set_attribute("gen_ai.operation.name", "invoke_agent")
            span.set_attribute("gen_ai.agent.name", self.agent)
            span.set_attribute("gen_ai.conversation.id", conversation_id)
            if CAPTURE:
                span.set_attribute("gen_ai.input.messages", clip([{"role": "user", "content": question}]))
            t0 = time.perf_counter()
            summary = {"outcome": "ok", "steps": 0, "trail": []}
            try:
                yield summary
            except Exception as e:
                summary["outcome"] = summary.get("outcome_on_error") or type(e).__name__
                span.record_exception(e)
                span.set_status(Status(StatusCode.ERROR, f"{type(e).__name__}: {e}"))
                span.set_attribute("error.type", type(e).__name__)
                raise
            finally:
                trail = summary["trail"]
                if trail and summary["outcome"] == "ok":
                    self.transitions.add(1, {"langgraph.from": trail[-1], "langgraph.to": "__end__"})
                dt = time.perf_counter() - t0
                span.set_attribute("agent.outcome", summary["outcome"])
                span.set_attribute("agent.steps", len(trail))
                span.set_attribute("agent.trail", " → ".join(trail))
                self.runs.add(1, {"outcome": summary["outcome"]})
                self.run_duration.record(dt, {"outcome": summary["outcome"]})
                self.run_steps.record(len(trail))
                log.info("agent_done outcome=%s steps=%d trail=%s ms=%d", summary["outcome"], len(trail), ">".join(trail), dt * 1000)

    # ---- noder ----------------------------------------------------------------------------
    def node(self, name: str):
        """Dekorerar en LangGraph-nod: span + duration + kant från föregående nod + loggrad."""

        def deco(fn):
            @wraps(fn)
            async def wrapper(state, config):
                md = (config or {}).get("metadata", {})
                trail = state.get("trail") or []
                prev = trail[-1] if trail else "__start__"
                self.transitions.add(1, {"langgraph.from": prev, "langgraph.to": name})
                with self.tracer.start_as_current_span(f"node {name}") as span:
                    span.set_attribute("langgraph.node", name)
                    span.set_attribute("langgraph.step", int(md.get("langgraph_step", len(trail) + 1)))
                    span.set_attribute("langgraph.previous", prev)
                    span.set_attribute("langgraph.triggers", [str(t) for t in md.get("langgraph_triggers", [])])
                    span.set_attribute("gen_ai.agent.name", self.agent)
                    t0, outcome = time.perf_counter(), "ok"
                    try:
                        update = dict(await fn(state, config) or {})
                    except Exception as e:
                        outcome = "error"
                        span.record_exception(e)
                        span.set_status(Status(StatusCode.ERROR, f"{type(e).__name__}: {e}"))
                        span.set_attribute("error.type", type(e).__name__)
                        log.error("node_failed node=%s step=%s error=%s detail=%s", name, md.get("langgraph_step"),
                                  type(e).__name__, str(e).splitlines()[0][:200])
                        raise
                    finally:
                        dt = time.perf_counter() - t0
                        self.node_duration.record(dt, {"langgraph.node": name, "outcome": outcome})
                    span.set_attribute("langgraph.update", sorted(update))
                    log.info("node_done node=%s step=%s from=%s ms=%d", name, md.get("langgraph_step"), prev, dt * 1000)
                    update["trail"] = [name]
                    return update

            return wrapper

        return deco

    # ---- LLM-anrop ------------------------------------------------------------------------
    @asynccontextmanager
    async def llm_call(self, model: str, messages: list, tools: list | None = None, max_tokens: int = 256):
        attrs = {"gen_ai.operation.name": "chat", "gen_ai.request.model": model}
        with self.tracer.start_as_current_span(f"chat {model}", kind=SpanKind.CLIENT) as span:
            span.set_attribute("gen_ai.operation.name", "chat")
            span.set_attribute("gen_ai.provider.name", "vllm")
            span.set_attribute("gen_ai.request.model", model)
            span.set_attribute("gen_ai.request.max_tokens", max_tokens)
            if tools:
                span.set_attribute("gen_ai.request.tools", [t["function"]["name"] for t in tools])
            if CAPTURE:
                span.set_attribute("gen_ai.input.messages", clip(messages))
            call, t0, err = _Call(span), time.perf_counter(), None
            try:
                yield call
            except Exception as e:
                err = type(e).__name__
                raise
            finally:
                self.llm_duration.record(time.perf_counter() - t0, {**attrs, **({"error.type": err} if err else {})})
            data = call.data or {}
            usage = data.get("usage", {})
            choice = (data.get("choices") or [{}])[0]
            msg = choice.get("message", {})
            span.set_attribute("gen_ai.response.model", data.get("model", model))
            span.set_attribute("gen_ai.response.id", data.get("id", ""))
            span.set_attribute("gen_ai.response.finish_reasons", [choice.get("finish_reason", "")])
            span.set_attribute("gen_ai.usage.input_tokens", usage.get("prompt_tokens", 0))
            span.set_attribute("gen_ai.usage.output_tokens", usage.get("completion_tokens", 0))
            if msg.get("tool_calls"):
                span.set_attribute("gen_ai.response.tool_calls", [c["function"]["name"] for c in msg["tool_calls"]])
            if CAPTURE:
                span.set_attribute("gen_ai.output.messages", clip([msg]))
            self.llm_tokens.record(usage.get("prompt_tokens", 0), {**attrs, "gen_ai.token.type": "input"})
            self.llm_tokens.record(usage.get("completion_tokens", 0), {**attrs, "gen_ai.token.type": "output"})

    # ---- verktyg --------------------------------------------------------------------------
    @asynccontextmanager
    async def tool_call(self, name: str, call_id: str, raw_args: str):
        with self.tracer.start_as_current_span(f"execute_tool {name}") as span:
            span.set_attribute("gen_ai.operation.name", "execute_tool")
            span.set_attribute("gen_ai.tool.name", name)
            span.set_attribute("gen_ai.tool.type", "function")
            span.set_attribute("gen_ai.tool.call.id", call_id)
            if CAPTURE:
                span.set_attribute("gen_ai.tool.call.arguments", clip(raw_args))
            call, t0, outcome = _Call(span), time.perf_counter(), "ok"
            try:
                yield call
            except Exception as e:
                outcome = "error"
                span.record_exception(e)
                span.set_status(Status(StatusCode.ERROR, f"{type(e).__name__}: {e}"))
                span.set_attribute("error.type", type(e).__name__)
                self.tool_calls.add(1, {"gen_ai.tool.name": name, "outcome": "error", "error.type": type(e).__name__})
                log.error("tool_failed tool=%s error=%s detail=%s", name, type(e).__name__, str(e).splitlines()[0][:200])
                raise
            finally:
                dt = time.perf_counter() - t0
                self.tool_duration.record(dt, {"gen_ai.tool.name": name, "outcome": outcome})
            if CAPTURE and call.data is not None:
                span.set_attribute("gen_ai.tool.call.result", clip(call.data))
            self.tool_calls.add(1, {"gen_ai.tool.name": name, "outcome": "ok"})
            log.info("tool_done tool=%s ms=%d", name, dt * 1000)
