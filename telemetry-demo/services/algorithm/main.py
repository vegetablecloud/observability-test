"""
algorithm – förberäknar tunga resultat (prognoser, risk, status) så att agenten får svar direkt.

  bakgrundsjobb (var PRECOMPUTE_INTERVAL_S):   precompute.run            ← en EGEN trace per körning
                                                 ├ SELECT demo (psycopg)   läser affärsdata ur Postgres
                                                 └ precompute.project ×N   klassiska beräkningar per projekt
  agentens verktyg:                           GET /insight/{project_id}?metric=forecast|risk|status
                                                 └ insight.lookup          cache.hit = true  -> ~5 ms
                                                                            cache.hit = false -> räknar nu, ~1 s

Det viktiga att se i telemetrin är att förberäkningen gör sitt jobb:
  algorithm.cache.lookups{result=hit|miss|stale}   – träffkvot, ska ligga nära 100 %
  algorithm.precompute.age                         – hur gammal är senaste lyckade körningen?
  algorithm.precompute.duration                    – hur lång tid tar ett jobb?

Chaos: stale -> bakgrundsjobbet pausar, cachen blir inaktuell och varje verktygsanrop blir långsamt.
"""

import asyncio
import logging
import os
import random
import time
from contextlib import asynccontextmanager

import psycopg
from fastapi import FastAPI, HTTPException
from opentelemetry import metrics, trace
from opentelemetry.metrics import Observation
from opentelemetry.trace import Status, StatusCode

DSN = os.getenv("APP_DB_DSN", "postgresql://demo:demo@postgres:5432/demo")
INTERVAL = float(os.getenv("PRECOMPUTE_INTERVAL_S", "20"))
PROJECTS = [f"P-{n}" for n in range(101, 109)]
METRICS = ("forecast", "risk", "status")

log = logging.getLogger("algorithm")
log.setLevel(logging.INFO)
tracer = trace.get_tracer("algorithm")
meter = metrics.get_meter("algorithm")

CACHE: dict[tuple[str, str], dict] = {}
STATE = {"mode": "normal", "last_success": 0.0}

run_duration = meter.create_histogram("algorithm.precompute.duration", unit="s", description="Tid för en förberäkningskörning",
                                      explicit_bucket_boundaries_advisory=[0.1, 0.25, 0.5, 1, 2, 3, 5, 8])
lookups = meter.create_counter("algorithm.cache.lookups", unit="{lookup}", description="Uppslag per resultat (hit/miss/stale)")
lookup_duration = meter.create_histogram("algorithm.lookup.duration", unit="s", description="Tid för ett uppslag",
                                         explicit_bucket_boundaries_advisory=[0.001, 0.005, 0.01, 0.05, 0.1, 0.25, 0.5, 1, 2])
meter.create_observable_gauge("algorithm.precompute.age", unit="s", description="Sekunder sedan senaste lyckade körning",
                              callbacks=[lambda _: [Observation(time.time() - STATE["last_success"] if STATE["last_success"] else 0)]])
meter.create_observable_gauge("algorithm.cache.entries", unit="{entry}", description="Antal förberäknade resultat",
                              callbacks=[lambda _: [Observation(len(CACHE))]])


def compute(project: str, metric: str, rows: int) -> dict:
    """'Klassisk' beräkning: CPU-tung loop + lite väntan, deterministisk per projekt."""
    seed = sum(map(ord, project + metric))
    acc = seed
    for _ in range(40_000):
        acc = (acc * 31 + 7) % 1_000_003
    rnd = random.Random(seed + int(time.time() // 300))
    if metric == "forecast":
        dev = rnd.uniform(-6, 14)
        text = f"Prognosen för {project} visar {dev:+.1f} % mot budget ({'över' if dev > 10 else 'inom'} rapportgränsen)."
    elif metric == "risk":
        text = f"{project} har {rnd.randint(1, 4)} öppna risker, största: {rnd.choice(['materialleverans', 'bemanning', 'myndighetsbeslut'])}."
    else:
        text = f"{project} är {rnd.choice(['grön', 'grön', 'gul'])}: tidplan {rnd.choice(['enligt plan', '1 vecka sen'])}."
    return {"project_id": project, "metric": metric, "insight": text, "based_on_rows": rows, "computed_at": time.time()}


async def precompute_once():
    with tracer.start_as_current_span("precompute.run", kind=trace.SpanKind.INTERNAL) as span:
        t0 = time.perf_counter()
        try:
            async with await psycopg.AsyncConnection.connect(DSN, connect_timeout=3) as c:
                rows = (await (await c.execute(
                    "SELECT count(*) FROM information_schema.tables WHERE table_schema = 'public'")).fetchone())[0]
            for p in PROJECTS:
                with tracer.start_as_current_span("precompute.project") as s:
                    s.set_attribute("app.project.id", p)
                    for m in METRICS:
                        CACHE[(p, m)] = compute(p, m, rows)
                    await asyncio.sleep(random.uniform(0.02, 0.08))
            STATE["last_success"] = time.time()
            elapsed = time.perf_counter() - t0
            span.set_attribute("algorithm.results", len(PROJECTS) * len(METRICS))
            run_duration.record(elapsed, {"outcome": "ok"})
            log.info("precompute_done projects=%d results=%d ms=%d", len(PROJECTS), len(CACHE), elapsed * 1000)
        except Exception as e:  # noqa: BLE001
            run_duration.record(time.perf_counter() - t0, {"outcome": "error"})
            span.record_exception(e)
            span.set_status(Status(StatusCode.ERROR, str(e)))
            log.error("precompute_failed error=%s", type(e).__name__)


async def scheduler():
    while True:
        if STATE["mode"] == "stale":
            log.warning("precompute_paused reason=chaos_stale age_s=%d", time.time() - STATE["last_success"])
        else:
            await precompute_once()
        await asyncio.sleep(INTERVAL)


@asynccontextmanager
async def lifespan(_: FastAPI):
    task = asyncio.create_task(scheduler())
    yield
    task.cancel()


app = FastAPI(title="algorithm", lifespan=lifespan)


@app.get("/health")
def health():
    return {"ok": True, "cache_entries": len(CACHE), "mode": STATE["mode"]}


@app.post("/chaos/{mode}")
def chaos(mode: str):
    STATE["mode"] = "stale" if mode == "stale" else "normal"
    return STATE


@app.get("/insight/{project_id}")
async def insight(project_id: str, metric: str = "status"):
    t0 = time.perf_counter()
    with tracer.start_as_current_span("insight.lookup") as span:
        span.set_attribute("app.project.id", project_id)
        span.set_attribute("algorithm.metric", metric)
        if project_id not in PROJECTS or metric not in METRICS:
            lookups.add(1, {"result": "not_found"})
            log.warning("insight_not_found project=%s metric=%s", project_id, metric)
            raise HTTPException(404, f"unknown project or metric: {project_id}/{metric}")
        hit = CACHE.get((project_id, metric))
        fresh = hit and time.time() - hit["computed_at"] < INTERVAL * 3
        result = "hit" if fresh else ("stale" if hit else "miss")
        span.set_attribute("cache.hit", bool(fresh))
        span.set_attribute("cache.result", result)
        if not fresh:
            # Ingen färsk förberäkning: räkna nu. Det är exakt det här förberäkningen ska undvika.
            with tracer.start_as_current_span("compute.on_demand"):
                await asyncio.sleep(random.uniform(0.7, 1.4))
                hit = CACHE[(project_id, metric)] = compute(project_id, metric, 0)
            log.warning("cache_%s project=%s metric=%s computed_on_demand=true", result, project_id, metric)
        lookups.add(1, {"result": result})
        lookup_duration.record(time.perf_counter() - t0, {"result": result})
        return {**hit, "cache": result, "age_s": round(time.time() - hit["computed_at"], 1)}
