"""
algorithm – Python-tjänst som "poängsätter" en fråga (intent + prioritet).

Instrumentering i två lager:
  1. Zero-code: containern startas med `opentelemetry-instrument`, som
     automatiskt ger server-spans, HTTP-metrics (RED) och loggar via OTLP.
     Allt styrs av OTEL_*-miljövariabler i docker-compose.yml.
  2. Manuellt: en egen span runt själva algoritmen + två domän-metrics.
     Det är här du lägger instrumentering som betyder något för just din tjänst.
"""

import logging
import random
import re
import time

from fastapi import FastAPI, HTTPException
from opentelemetry import metrics, trace
from pydantic import BaseModel

log = logging.getLogger("algorithm")
log.setLevel(logging.INFO)
tracer = trace.get_tracer("algorithm")
meter = metrics.get_meter("algorithm")

# Histogram = fördelning (p50/p95/p99). Counter = växer bara. Håll labels få och stabila!
duration = meter.create_histogram(
    "algorithm.duration",
    unit="s",
    description="Tid för att poängsätta en fråga",
    explicit_bucket_boundaries_advisory=[0.01, 0.025, 0.05, 0.1, 0.15, 0.2, 0.3, 0.5, 1, 2],
)
items = meter.create_counter("algorithm.items.processed", unit="{token}", description="Antal tokens som poängsatts")
errors = meter.create_counter("algorithm.errors", unit="{error}", description="Fel i algoritmen")

INTENTS = {
    "metrics": ["metric", "p95", "latens", "prometheus", "counter", "histogram", "gauge", "cardinality"],
    "traces": ["trace", "span", "tempo", "propagation", "trace_id", "waterfall"],
    "logs": ["log", "loki", "logg", "warn", "error"],
    "infra": ["gpu", "cpu", "dgx", "minne", "vram", "container", "disk"],
    "collector": ["collector", "otlp", "pipeline", "batch", "sampling", "redaction"],
}

app = FastAPI(title="algorithm")


class ScoreReq(BaseModel):
    question: str


@app.get("/health")
def health():
    return {"ok": True}


@app.post("/score")
def score(req: ScoreReq):
    start = time.perf_counter()
    with tracer.start_as_current_span("score") as span:
        tokens = re.findall(r"\w+", req.question.lower())
        span.set_attribute("algorithm.tokens", len(tokens))

        # "Tung" beräkning – simulerat CPU-arbete så att latensen syns i grafer.
        with tracer.start_as_current_span("feature_extraction"):
            acc = 0
            for _ in range(20_000 + 400 * len(tokens)):
                acc = (acc * 31 + 7) % 1_000_003
            time.sleep(random.uniform(0.08, 0.16))

        with tracer.start_as_current_span("classify") as cspan:
            scores = {k: sum(any(w in t for w in words) for t in tokens) for k, words in INTENTS.items()}
            intent = max(scores, key=scores.get) if any(scores.values()) else "general"
            priority = round(min(1.0, 0.2 + 0.1 * len(tokens) / 4 + random.random() * 0.2), 2)
            cspan.set_attribute("algorithm.intent", intent)

        # ~1 % fel så att error rate inte är noll i dashboards.
        if random.random() < 0.01:
            errors.add(1, {"error.type": "ModelNotConverged"})
            log.error("score_failed reason=model_not_converged tokens=%d", len(tokens))
            raise HTTPException(500, "model did not converge")

        elapsed = time.perf_counter() - start
        duration.record(elapsed, {"algorithm.intent": intent})
        items.add(len(tokens))
        log.info("score_done intent=%s priority=%.2f ms=%d", intent, priority, elapsed * 1000)
        return {"intent": intent, "priority": priority, "scores": scores}
