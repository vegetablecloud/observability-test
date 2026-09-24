"""
rag-api – retrieval som egen tjänst: embed (Harrier via vLLM) -> hybrid-sökning i ParadeDB.

  POST /search {query, top_k}

  rag.search                          (manuell)
   ├ embeddings harrier               (manuell, GenAI-semconv)
   │  └ POST vllm-embed/v1/embeddings (auto: httpx)
   ├ rag.retrieve.bm25                (manuell)  – ParadeDB pg_search, nyckelord
   │  └ SELECT rag                    (auto: psycopg)
   ├ rag.retrieve.vector              (manuell)  – pgvector, semantisk likhet
   │  └ SELECT rag                    (auto: psycopg)
   └ rag.fuse                         (manuell)  – Reciprocal Rank Fusion + rerank

Varför en egen tjänst? Retrieval har andra fel (tomt index, långsam DB, dålig träffkvalitet)
än agenten. Med egna spans och metrics syns skillnaden direkt: är det agenten, modellen
eller sökningen som är problemet?

Kvalitetssignaler som metrics (det är dem AI-utvecklarna vill se över tid):
  rag.retrieval.top_score   – hur bra är bästa träffen? Sjunker den: sämre svar.
  rag.search.empty          – sökningar utan träff alls.

Chaos: rag_error (40 % 500) · db_slow (pg_sleep i BM25-frågan)
"""

import asyncio
import logging
import os
import random
import time
from contextlib import asynccontextmanager

import httpx
import psycopg
from fastapi import FastAPI, HTTPException
from opentelemetry import metrics, trace
from opentelemetry.trace import Status, StatusCode
from psycopg_pool import AsyncConnectionPool
from pydantic import BaseModel

from knowledge import DOCS

DSN = os.getenv("RAG_DB_DSN", "postgresql://demo:demo@paradedb:5432/rag")
EMBED_BASE = os.getenv("EMBED_BASE_URL", "http://vllm-embed:8000/v1")
EMBED_MODEL = os.getenv("EMBED_MODEL", "harrier")
DIM = int(os.getenv("EMBED_DIM", "384"))
RRF_K = 60

log = logging.getLogger("rag-api")
log.setLevel(logging.INFO)
logging.getLogger("httpx").setLevel(logging.WARNING)
tracer = trace.get_tracer("rag-api")
meter = metrics.get_meter("rag-api")

SEC = [0.005, 0.01, 0.025, 0.05, 0.1, 0.25, 0.5, 1, 1.5, 2, 3, 5]
stage_duration = meter.create_histogram("rag.search.duration", unit="s", explicit_bucket_boundaries_advisory=SEC,
                                        description="Tid per steg i sökningen (rag.stage=embed|bm25|vector|fuse|total)")
docs_returned = meter.create_histogram("rag.documents.returned", unit="{document}", description="Dokument per sökning",
                                       explicit_bucket_boundaries_advisory=[0, 1, 2, 3, 4, 5, 8, 10])
top_score = meter.create_histogram("rag.retrieval.top_score", unit="1", description="Cosine-likhet för bästa träffen",
                                   explicit_bucket_boundaries_advisory=[0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9, 1.0])
empty = meter.create_counter("rag.search.empty", unit="{search}", description="Sökningar utan träff")
searches = meter.create_counter("rag.search.requests", unit="{search}", description="Sökningar per utfall")
emb_duration = meter.create_histogram("gen_ai.client.operation.duration", unit="s", explicit_bucket_boundaries_advisory=SEC,
                                      description="Embedding-anropets längd")
emb_tokens = meter.create_histogram("gen_ai.client.token.usage", unit="{token}", description="Tokens per anrop",
                                    explicit_bucket_boundaries_advisory=[8, 16, 32, 64, 128, 256, 512, 1024])

STATE = {"mode": "normal"}
http = httpx.AsyncClient(timeout=10)
pool = AsyncConnectionPool(DSN, min_size=1, max_size=8, open=False)


async def embed(texts: list[str]) -> list[list[float]]:
    attrs = {"gen_ai.operation.name": "embeddings", "gen_ai.request.model": EMBED_MODEL}
    with tracer.start_as_current_span(f"embeddings {EMBED_MODEL}", kind=trace.SpanKind.CLIENT) as s:
        for k, v in attrs.items():
            s.set_attribute(k, v)
        s.set_attribute("gen_ai.system", "vllm")
        t0 = time.perf_counter()
        r = await http.post(f"{EMBED_BASE}/embeddings", json={"model": EMBED_MODEL, "input": texts})
        r.raise_for_status()
        data = r.json()
        n = data.get("usage", {}).get("prompt_tokens", 0)
        s.set_attribute("gen_ai.usage.input_tokens", n)
        s.set_attribute("gen_ai.embeddings.dimension.count", DIM)
        emb_duration.record(time.perf_counter() - t0, attrs)
        emb_tokens.record(n, {**attrs, "gen_ai.token.type": "input"})
        return [d["embedding"] for d in data["data"]]


def vec(v: list[float]) -> str:
    return "[" + ",".join(f"{x:.5f}" for x in v) + "]"


async def seed():
    """Skapar tabell + index och laddar kunskapsbasen. Väntar in DB och embeddings-modellen."""
    for attempt in range(60):
        try:
            await pool.open(wait=True, timeout=5)
            async with pool.connection() as c:
                await c.execute("CREATE EXTENSION IF NOT EXISTS pg_search CASCADE")
                await c.execute(f"""CREATE TABLE IF NOT EXISTS documents (
                    id serial PRIMARY KEY, topic text NOT NULL, title text NOT NULL, body text NOT NULL,
                    embedding vector({DIM}) NOT NULL)""")
                n = (await (await c.execute("SELECT count(*) FROM documents")).fetchone())[0]
                if n >= len(DOCS) and await (await c.execute(
                        "SELECT 1 FROM pg_indexes WHERE indexname = 'documents_bm25_sv'")).fetchone():
                    log.info("knowledge_base_ready docs=%d", n)
                    return
                await c.execute("DROP INDEX IF EXISTS documents_bm25")
                await c.execute("TRUNCATE documents")
                vectors = await embed([f"{t}. {b}" for _, t, b in DOCS])
                async with c.cursor() as cur:
                    await cur.executemany("INSERT INTO documents (topic, title, body, embedding) VALUES (%s, %s, %s, %s)",
                                          [(tp, t, b, vec(v)) for (tp, t, b), v in zip(DOCS, vectors)])
                # BM25 med svensk stemming: "prognosen" matchar "Budgetprognos", "risken" matchar "risk"
                await c.execute("CREATE INDEX IF NOT EXISTS documents_bm25_sv ON documents USING bm25 "
                                "(id, (title::pdb.simple('stemmer=swedish')), (body::pdb.simple('stemmer=swedish'))) WITH (key_field='id')")
                await c.execute("CREATE INDEX IF NOT EXISTS documents_vec ON documents USING hnsw (embedding vector_cosine_ops)")
                log.info("knowledge_base_seeded docs=%d", len(DOCS))
                return
        except Exception as e:  # noqa: BLE001
            log.warning("rag_not_ready attempt=%d error=%s", attempt + 1, type(e).__name__)
            await asyncio.sleep(2)


@asynccontextmanager
async def lifespan(_: FastAPI):
    await seed()
    yield
    await pool.close()


app = FastAPI(title="rag-api", lifespan=lifespan)


class SearchReq(BaseModel):
    query: str
    top_k: int = 5


@app.get("/health")
def health():
    return {"ok": True, "mode": STATE["mode"]}


@app.post("/chaos/{mode}")
def chaos(mode: str):
    STATE["mode"] = mode if mode in ("rag_error", "db_slow") else "normal"
    return STATE


async def _timed(stage: str, coro):
    t0 = time.perf_counter()
    try:
        return await coro
    finally:
        stage_duration.record(time.perf_counter() - t0, {"rag.stage": stage})


async def bm25(q: str, k: int):
    with tracer.start_as_current_span("rag.retrieve.bm25") as s:
        s.set_attribute("db.system.name", "postgresql")
        s.set_attribute("rag.retriever", "bm25")
        sql = "SELECT id, pdb.score(id) FROM documents WHERE title ||| %s OR body ||| %s ORDER BY 2 DESC LIMIT %s"
        async with pool.connection() as c:
            if STATE["mode"] == "db_slow":  # simulerar en DB under last (lås, full disk-cache, …)
                await c.execute("SELECT pg_sleep(%s)", [random.uniform(0.8, 1.6)])
            rows = await (await c.execute(sql, [q, q, k])).fetchall()
        s.set_attribute("rag.hits", len(rows))
        return rows


async def vector(v: list[float], k: int):
    with tracer.start_as_current_span("rag.retrieve.vector") as s:
        s.set_attribute("db.system.name", "postgresql")
        s.set_attribute("rag.retriever", "pgvector")
        async with pool.connection() as c:
            rows = await (await c.execute(
                "SELECT id, 1 - (embedding <=> %s::vector) AS sim FROM documents ORDER BY embedding <=> %s::vector LIMIT %s",
                [vec(v), vec(v), k])).fetchall()
        s.set_attribute("rag.hits", len(rows))
        return rows


@app.post("/search")
async def search(req: SearchReq):
    t0 = time.perf_counter()
    with tracer.start_as_current_span("rag.search") as span:
        span.set_attribute("rag.top_k", req.top_k)
        span.set_attribute("rag.query.length", len(req.query))
        try:
            if STATE["mode"] == "rag_error" and random.random() < 0.4:
                raise RuntimeError("bm25 index unavailable (simulated)")
            [qv] = await _timed("embed", embed([req.query]))
            kw, sem = await asyncio.gather(_timed("bm25", bm25(req.query, req.top_k * 2)),
                                           _timed("vector", vector(qv, req.top_k * 2)))

            with tracer.start_as_current_span("rag.fuse") as s:
                t1 = time.perf_counter()
                fused, sims = {}, {i: sim for i, sim in sem}
                for ranked in (kw, sem):
                    for rank, (doc_id, _) in enumerate(ranked):
                        fused[doc_id] = fused.get(doc_id, 0.0) + 1.0 / (RRF_K + rank + 1)
                best = sorted(fused, key=fused.get, reverse=True)[: req.top_k]
                s.set_attribute("rag.fusion", "rrf")
                s.set_attribute("rag.candidates", len(fused))
                s.set_attribute("rag.documents.kept", len(best))
                stage_duration.record(time.perf_counter() - t1, {"rag.stage": "fuse"})

            docs = []
            if best:
                async with pool.connection() as c:
                    rows = await (await c.execute("SELECT id, topic, title, body FROM documents WHERE id = ANY(%s)", [best])).fetchall()
                by_id = {r[0]: r for r in rows}
                docs = [{"id": i, "topic": by_id[i][1], "title": by_id[i][2], "text": by_id[i][3],
                         "score": round(fused[i], 4), "similarity": round(sims.get(i, 0.0), 3)} for i in best if i in by_id]

            best_sim = max((d["similarity"] for d in docs), default=0.0)
            docs_returned.record(len(docs))
            top_score.record(best_sim)
            span.set_attribute("rag.documents.returned", len(docs))
            span.set_attribute("rag.retrieval.top_score", best_sim)
            span.set_attribute("rag.bm25.hits", len(kw))
            if not docs:
                empty.add(1)
                log.warning("search_empty query_chars=%d", len(req.query))
            searches.add(1, {"outcome": "ok"})
            ms = (time.perf_counter() - t0) * 1000
            log.info("search_done docs=%d bm25_hits=%d top_similarity=%.2f ms=%d", len(docs), len(kw), best_sim, ms)
            return {"documents": docs, "stats": {"bm25_hits": len(kw), "vector_hits": len(sem), "top_similarity": best_sim}}
        except (psycopg.Error, httpx.HTTPError, RuntimeError) as e:
            searches.add(1, {"outcome": "error", "error.type": type(e).__name__})
            span.record_exception(e)
            span.set_status(Status(StatusCode.ERROR, str(e)))
            log.error("search_failed error=%s detail=%s", type(e).__name__, e)
            raise HTTPException(503, f"search failed: {e}") from e
        finally:
            stage_duration.record(time.perf_counter() - t0, {"rag.stage": "total"})
