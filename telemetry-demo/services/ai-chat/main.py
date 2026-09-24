"""
ai-chat – chatten: en LangGraph-agent (graph.py) bakom ett HTTP-API.

    POST /chat {question, conversation_id}

Auto-instrumenteringen (opentelemetry-instrument) ger server-spanen och varje HTTP-anrop.
agent_otel.py ger resten: en span per agentkörning, per nod, per LLM-anrop och per verktyg.
Svaret innehåller också agentens väg genom grafen, så UI:t och testarna ser den direkt.
"""

import logging
import os
import uuid

from fastapi import FastAPI, HTTPException
from langgraph.errors import GraphRecursionError
from pydantic import BaseModel

from graph import GRAPH, LLMUnavailable, tel

MAX_STEPS = int(os.getenv("AGENT_MAX_STEPS", "8"))

log = logging.getLogger("ai-chat")
log.setLevel(logging.INFO)
logging.getLogger("httpx").setLevel(logging.WARNING)  # en INFO-rad per HTTP-anrop = brus

app = FastAPI(title="ai-chat")


class ChatReq(BaseModel):
    question: str
    conversation_id: str | None = None


@app.get("/health")
def health():
    return {"ok": True}


@app.post("/chat")
async def chat(req: ChatReq):
    cid = req.conversation_id or uuid.uuid4().hex[:16]
    async with tel.run(cid, req.question) as run:
        try:
            state = await GRAPH.ainvoke({"question": req.question, "conversation_id": cid},
                                        config={"recursion_limit": MAX_STEPS, "run_name": "chat-agent"})
        except GraphRecursionError as e:
            run["outcome_on_error"] = "recursion_limit"
            log.error("agent_recursion_limit limit=%d conversation=%s", MAX_STEPS, cid)
            raise HTTPException(508, f"agent exceeded {MAX_STEPS} steps") from e
        except LLMUnavailable as e:
            run["outcome_on_error"] = "llm_unavailable"
            raise HTTPException(502, str(e)) from e
        run["trail"] = state.get("trail", [])
        if state.get("blocked"):
            run["outcome"] = "guard_blocked"
        tools = state.get("tool_log", [])
        return {
            "answer": state.get("answer", ""),
            "intent": state.get("intent", "general"),
            "sources": state.get("sources", []),
            "steps": run["trail"],
            "tools": tools,
            "usage": {"input_tokens": sum(u.get("prompt_tokens", 0) for u in state.get("usage", [])),
                      "output_tokens": sum(u.get("completion_tokens", 0) for u in state.get("usage", []))},
            "outcome": run["outcome"],
        }
