"""
04 · LLM & RAG – modellerna och sökningen under agenten.
Svarar på: "Är det modellen, embeddings eller sökningen som är långsam eller dålig?"

  ① Modellerna (vLLM, pull)   gemma (chat) och harrier (embeddings): latens, köer, KV-cache, tokens, prefix cache
  ② Sökningen (rag-api, push) tid per steg (embed, BM25, vektor, fusion), träffkvalitet, tomma sökningar, fel
"""

from dashlib import (ACCENT, G300, G500, G700, WHITE, Board, bargauge, color_override, heatmap, logs, prom, stat, thresholds,
                     timeseries)

VLLM = "vllm:%s"
M = 'model_name=~"$model"'


def v(metric, extra=""):
    return '{"' + VLLM % metric + f'", {M}{extra}' + "}"


def q95(metric, by="model_name", window="1m"):
    return f'histogram_quantile(0.95, sum by (le, {by}) (rate({v(metric + "_bucket")}[{window}])))'


def build():
    b = Board("llm-rag", "04 · LLM & RAG", "Är det modellen, embeddings eller sökningen som är långsam eller dålig?", tags=["ai"])
    b.prom_values("model", "modell", '{__name__="vllm:num_requests_running"}', "model_name")

    b.row("① Modellerna · vLLM (Collectorn hämtar /metrics)")
    b.add(stat("Time to first token p95 · gemma", [prom(q95("time_to_first_token_seconds").replace(M, 'model_name="gemma"'))],
               unit="s", th=thresholds((None, WHITE), (1, ACCENT)),
               desc="Hur länge användaren väntar innan första ordet. Stiger när GPU:n är mättad eller kön växer."), w=4, h=4)
    b.add(stat("Tokens / s · genererade", [prom(f'sum(rate({v("generation_tokens_total")}[1m]))')], decimals=0,
               desc="Genererade tokens per sekund, valda modeller. Genomströmningen i GPU:n."), w=4, h=4)
    b.add(stat("Kö · väntar", [prom(f'sum({v("num_requests_waiting")})')], decimals=0, th=thresholds((None, WHITE), (4, ACCENT)),
               desc="Requests som väntar på GPU. Över 4 = modellen hinner inte med."), w=4, h=4)
    b.add(stat("KV-cache · gemma", [prom('100 * max({"vllm:kv_cache_usage_perc", model_name="gemma"})')], unit="percent", decimals=0,
               th=thresholds((None, WHITE), (85, ACCENT)),
               desc="Hur full KV-cachen är. Nära 100 %: vLLM måste pausa (preempt) requests, latensen hoppar."), w=4, h=4)
    b.add(stat("Prefix cache träff", [prom(f'sum(rate({v("prefix_cache_hits_total")}[5m])) / sum(rate({v("prefix_cache_queries_total")}[5m]))')],
               unit="percentunit", decimals=0,
               desc="Andel prompt-tokens som redan fanns i cachen (systemprompten återanvänds). Högre = billigare prefill."), w=4, h=4)
    b.add(stat("Embeddings / s · harrier", [prom('sum(rate({"vllm:e2e_request_latency_seconds_count", model_name="harrier"}[1m]))')],
               decimals=1, desc="Embedding-anrop per sekund från rag-api (en per sökning)."), w=4, h=4)

    b.add(timeseries("Latens per modell · p95", [
        prom(q95("time_to_first_token_seconds"), "TTFT · {{model_name}}"),
        prom(q95("e2e_request_latency_seconds"), "e2e · {{model_name}}"),
        prom(q95("request_queue_time_seconds"), "kö · {{model_name}}")],
        unit="s", th=thresholds((None, "transparent"), (1, ACCENT)), th_style="dashed",
        overrides=[color_override("e2e · gemma", ACCENT, width=3), color_override("TTFT · gemma", WHITE),
                   color_override("kö · gemma", G500, dash=True), color_override("e2e · harrier", G300, dash=True),
                   color_override("TTFT · harrier", G700), color_override("kö · harrier", G700, dash=True)],
        desc="e2e = hela requesten i vLLM. TTFT = till första token. kö = väntan innan GPU:n tog den. Växer 'kö': kapacitetsproblem."),
          w=12, h=9)
    b.add(heatmap("gemma · e2e-latens, fördelning", [prom('sum by (le) (increase({"vllm:e2e_request_latency_seconds_bucket", model_name="gemma"}[1m]))',
                                                          "{{le}}", fmt="heatmap")],
                  desc="Varje kolumn = en minut. Ljusare ruta = fler requests med den latensen. Två band = två sorters requests "
                       "(välja verktyg vs skriva svar)."), w=12, h=9)
    b.add(timeseries("Tokens / s per modell", [
        prom(f'sum by (model_name) (rate({v("prompt_tokens_total")}[1m]))', "prompt (in) · {{model_name}}"),
        prom(f'sum by (model_name) (rate({v("generation_tokens_total")}[1m]))', "genererat (ut) · {{model_name}}")],
        overrides=[color_override("genererat (ut) · gemma", ACCENT, width=3), color_override("prompt (in) · gemma", WHITE, dash=True),
                   color_override("prompt (in) · harrier", G500)],
        desc="Embeddings-modellen har bara prompt-tokens. Chat-modellens prompt växer med agentens varv (verktygsresultat)."), w=8, h=8)
    b.add(timeseries("Köer och körning", [
        prom(f'sum by (model_name) (avg_over_time({v("num_requests_running")}[1m]))', "körs · {{model_name}}"),
        prom(f'sum by (model_name) (avg_over_time({v("num_requests_waiting")}[1m]))', "väntar · {{model_name}}")],
        overrides=[color_override("väntar · gemma", ACCENT, width=3), color_override("körs · gemma", WHITE),
                   color_override("väntar · harrier", ACCENT, dash=True), color_override("körs · harrier", G500)],
        desc="Medel per minut. running = på GPU:n nu, waiting = i kö. vLLM batchar körande requests, så running kan vara > 1."), w=8, h=8)
    b.add(timeseries("KV-cache & GPU", [
        prom('100 * max by (model_name) ({"vllm:kv_cache_usage_perc"})', "KV-cache · {{model_name}}"),
        prom("avg(DCGM_FI_DEV_GPU_UTIL)", "GPU")],
        unit="percent", max_=100, overrides=[color_override("GPU", ACCENT, width=3), color_override("KV-cache · gemma", WHITE),
                                             color_override("KV-cache · harrier", G500, dash=True)],
        desc="KV-cache och GPU på samma axel: stiger båda samtidigt är det last, inte en bugg."), w=8, h=8)

    b.row("② Sökningen · rag-api (embeddings → BM25 + vektor i ParadeDB → fusion)")
    b.add(stat("Sökningar / s", [prom('sum(rate(rag_search_requests_total[1m]))')], decimals=1,
               desc="Anrop till rag-api /search. Varje search_documents-verktyg i agenten = en sökning."), w=4, h=4)
    b.add(stat("p95 · hela sökningen", [prom('histogram_quantile(0.95, sum by (le) (rate(rag_search_duration_seconds_bucket{rag_stage="total"}[5m])))')],
               unit="s", th=thresholds((None, WHITE), (0.5, ACCENT)),
               desc="Embedding + BM25 + vektor + fusion. Gul över 0,5 s."), w=4, h=4)
    b.add(stat("Sökfel", [prom('(sum(rate(rag_search_requests_total{outcome="error"}[5m])) or vector(0)) / sum(rate(rag_search_requests_total[5m]))')],
               unit="percentunit", decimals=1, th=thresholds((None, WHITE), (0.01, ACCENT)),
               desc="Sökningar som gav 503 (index nere, DB-fel, embeddings nere)."), w=4, h=4)
    b.add(stat("Tomma sökningar", [prom('(sum(rate(rag_search_empty_total[5m])) or vector(0)) / sum(rate(rag_search_requests_total[5m]))')],
               unit="percentunit", decimals=1, th=thresholds((None, WHITE), (0.05, ACCENT)),
               desc="Sökningar utan en enda träff. Agenten svarar då utan underlag: risk för hallucination."), w=4, h=4)
    b.add(stat("Bästa träffens likhet · median", [prom('histogram_quantile(0.5, sum by (le) (rate(rag_retrieval_top_score_bucket[5m])))')],
               unit="percentunit", decimals=0, th=thresholds((None, ACCENT), (0.15, WHITE)),
               desc="Cosine-likhet för bästa dokumentet. KVALITETSSIGNAL: sjunker den efter en ändring (ny embeddings-modell, "
                    "ny chunkning) blir svaren sämre, även om inget är 'trasigt'."), w=4, h=4)
    b.add(stat("Dokument per sökning", [prom('sum(rate(rag_documents_returned_sum[5m])) / sum(rate(rag_documents_returned_count[5m]))')],
               decimals=1, desc="Hur många dokument som skickas vidare till modellen per sökning (efter fusion)."), w=4, h=4)

    b.add(timeseries("Tid per steg · p95", [
        prom('histogram_quantile(0.95, sum by (le, rag_stage) (rate(rag_search_duration_seconds_bucket{rag_stage!="total"}[1m])))', "{{rag_stage}}")],
        unit="s", overrides=[color_override("embed", WHITE), color_override("bm25", ACCENT, width=3), color_override("vector", G300),
                             color_override("fuse", G500, dash=True)],
        desc="Vilket steg i sökningen tar tiden? bm25 och vector körs parallellt. Hoppar bm25: titta på ParadeDB i 08 · Databaser."),
          w=12, h=8)
    b.add(bargauge("Bästa träffens likhet · fördelning senaste 15 min",
                   [prom('sum by (le) (increase(rag_retrieval_top_score_bucket[15m]))', "≤ {{le}}", instant=True, fmt="heatmap")],
                   unit="short", decimals=0, mode="basic", orientation="vertical", color=G300,
                   desc="Hur många sökningar som hade bästa träff med likhet ≤ värdet. Mer åt höger = bättre retrieval."), w=12, h=8)
    b.add(logs("rag-api · sökningar och fel", '{service_name="rag-api"} |~ "search_done|search_failed|search_empty|rag_not_ready"',
               desc="search_done visar bm25_hits och top_similarity per sökning. search_failed visar exakt vilket fel."), w=24, h=8)
    return b
