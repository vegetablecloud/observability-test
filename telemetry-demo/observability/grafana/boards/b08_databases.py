"""
08 · Databaser – postgres (app-data) och paradedb (RAG: BM25 + pgvector).
Svarar på: "Mår databaserna bra, och är det de som gör appen långsam?"

Två perspektiv, bredvid varandra:
  * inifrån  – Collectorns postgresql-receiver loggar in och läser statistik (pull): anslutningar,
               commits, cache-träff, storlek, tabeller och index
  * utifrån  – det apparna upplever (push): hur lång tid tar frågorna, sett från backend och rag-api
"""

from dashlib import (ACCENT, G300, G500, WHITE, Board, bargauge, color_override, prom, stat, table, tempo_columns, thresholds,
                     timeseries, traceql)

DB = 'service_name=~"$db"'


def build():
    b = Board("databases", "08 · Databaser", "Mår databaserna bra, och är det de som gör appen långsam?", tags=["drift"])
    b.custom("db", "databas", ["postgres", "paradedb"], include_all=True, multi=True, default="All")
    b.variables[-1]["current"] = {"text": "All", "value": "$__all"}

    b.add(stat("Anslutningar", [prom(f"sum by (service_name) (postgresql_backends{{{DB}}})", "{{service_name}}")], decimals=0,
               text_mode="value_and_name", desc="Öppna anslutningar per databas (connection pools i apparna)."), w=4, h=4)
    b.add(stat("Av max", [prom(f"sum by (service_name) (postgresql_backends{{{DB}}}) / max by (service_name) (postgresql_connection_max{{{DB}}})",
                               "{{service_name}}")], unit="percentunit", decimals=0, text_mode="value_and_name",
               th=thresholds((None, WHITE), (0.8, ACCENT)), desc="Andel av max_connections. Över 80 %: nästa topp ger 'too many clients'."),
          w=4, h=4)
    b.add(stat("Commits / s", [prom(f"sum by (service_name) (rate(postgresql_commits_total{{{DB}}}[1m]))", "{{service_name}}")], decimals=1,
               text_mode="value_and_name", desc="Transaktioner som lyckats per sekund."), w=4, h=4)
    b.add(stat("Cache-träff", [prom(f"sum by (service_name) (rate(postgresql_blks_hit_total{{{DB}}}[5m])) / (sum by (service_name) "
                                    f"(rate(postgresql_blks_hit_total{{{DB}}}[5m])) + sum by (service_name) (rate(postgresql_blks_read_total{{{DB}}}[5m])))",
                                    "{{service_name}}")], unit="percentunit", decimals=1, text_mode="value_and_name",
               th=thresholds((None, ACCENT), (0.95, WHITE)),
               desc="Andel block som lästs från minnet i stället för disk. Under 95 %: shared_buffers räcker inte."), w=4, h=4)
    b.add(stat("Deadlocks · 1 h", [prom(f"sum(increase(postgresql_deadlocks_total{{{DB}}}[1h])) or vector(0)")], decimals=0,
               th=thresholds((None, WHITE), (1, ACCENT)), desc="Transaktioner som dödades för att de låste varandra. Ska vara 0."), w=4, h=4)
    b.add(stat("Storlek", [prom(f"sum by (service_name) (postgresql_db_size_bytes{{{DB}}})", "{{service_name}}")], unit="bytes",
               decimals=0, text_mode="value_and_name", desc="Databasernas storlek på disk."), w=4, h=4)

    b.row("① Utifrån · hur lång tid tar frågorna för apparna?")
    b.add(timeseries("DB-frågor p95 · backend (Npgsql) och algorithm/rag-api (psycopg)", [
        prom('histogram_quantile(0.95, sum by (le, service_name) (rate(db_client_operation_duration_seconds_bucket[1m])))', "{{service_name}}"),
        prom('histogram_quantile(0.95, sum by (le, service) (rate(traces_spanmetrics_latency_bucket{span_kind="SPAN_KIND_CLIENT", '
             'span_name=~"SELECT.*|INSERT.*"}[1m])))', "{{service}} (ur traces)")],
        unit="s", overrides=[color_override("backend", WHITE), color_override("rag-api (ur traces)", ACCENT, width=3),
                             color_override("algorithm (ur traces)", G500, dash=True), color_override("backend (ur traces)", G300, dash=True)],
        desc="Latensen apparna ser, inklusive nätverk och connection pool. Stiger den men inte ① inifrån: problemet är mellan app och DB."),
          w=12, h=8)
    b.add(timeseries("rag-api · BM25 vs vektor · p95", [
        prom('histogram_quantile(0.95, sum by (le, rag_stage) (rate(rag_search_duration_seconds_bucket{rag_stage=~"bm25|vector"}[1m])))',
             "{{rag_stage}}")], unit="s", overrides=[color_override("bm25", ACCENT, width=3), color_override("vector", WHITE)],
        desc="Samma ParadeDB, två sorters index: pg_search (BM25, nyckelord) och pgvector (HNSW, semantik)."), w=12, h=8)
    b.add(table("Långsamma DB-frågor (> 100 ms) · klicka för trace", [traceql(
        '{ kind = client && (span.db.system = "postgresql" || span.db.system.name = "postgresql") && duration > 100ms }'
        ' | select(resource.service.name, span.db.statement, span.db.query.text)', limit=20, table="spans")],
        transformations=[tempo_columns({"service.name": "Tjänst", "db.statement": "SQL (psycopg)", "db.query.text": "SQL (Npgsql)"},
                                       hide=["traceIdHidden"])],
        desc="Varje DB-anrop som tog mer än 100 ms, med SQL-texten. Prova chaos-läget db_slow."), w=24, h=8)

    b.row("② Inifrån · Collectorns postgresql-receiver")
    b.add(timeseries("Transaktioner / s", [
        prom(f"sum by (service_name) (rate(postgresql_commits_total{{{DB}}}[1m]))", "commits · {{service_name}}"),
        prom(f"sum by (service_name) (rate(postgresql_rollbacks_total{{{DB}}}[1m]))", "rollbacks · {{service_name}}")],
        overrides=[color_override("commits · postgres", WHITE), color_override("commits · paradedb", G300),
                   color_override("rollbacks · postgres", ACCENT), color_override("rollbacks · paradedb", ACCENT, dash=True)],
        desc="Rollbacks (gult) = transaktioner som avbröts. Enstaka är normalt, en växande kurva är det inte."), w=8, h=8)
    b.add(timeseries("Rader in / läst per sekund", [
        prom(f"sum by (service_name) (rate(postgresql_tup_inserted_total{{{DB}}}[1m]))", "insert · {{service_name}}"),
        prom(f"sum by (service_name) (rate(postgresql_tup_fetched_total{{{DB}}}[1m]))", "hämtade · {{service_name}}")],
        overrides=[color_override("insert · postgres", ACCENT), color_override("hämtade · postgres", WHITE),
                   color_override("hämtade · paradedb", G300), color_override("insert · paradedb", ACCENT, dash=True)],
        desc="postgres skriver en rad per konversation. paradedb läses vid varje sökning."), w=8, h=8)
    b.add(timeseries("Sekventiella scans vs index-scans", [
        prom(f"sum by (service_name) (rate(postgresql_sequential_scans_total{{{DB}}}[1m]))", "seq scan · {{service_name}}"),
        prom(f"sum by (service_name) (rate(postgresql_index_scans_total{{{DB}}}[1m]))", "index scan · {{service_name}}")],
        overrides=[color_override("seq scan · postgres", ACCENT), color_override("seq scan · paradedb", ACCENT, dash=True),
                   color_override("index scan · postgres", WHITE), color_override("index scan · paradedb", G300)],
        desc="Sekventiella scans (gult) på stora tabeller = saknat index. Kvotfrågan i backend använder conversations_user_time."),
          w=8, h=8)
    b.add(bargauge("Största tabellerna", [prom(f"topk(8, sum by (service_name, postgresql_table_name) (postgresql_table_size_bytes{{{DB}}}))",
                                              "{{postgresql_table_name}} · {{service_name}}", instant=True)],
                   unit="bytes", decimals=0, mode="basic", color=G300, names="left",
                   desc="Tabellstorlek per tabell. documents i paradedb är kunskapsbasen, conversations i postgres växer med varje fråga."),
          w=12, h=8)
    b.add(bargauge("Index", [prom(f"topk(8, sum by (service_name, postgresql_index_name) (postgresql_index_size_bytes{{{DB}}}))",
                                  "{{postgresql_index_name}} · {{service_name}}", instant=True)],
                   unit="bytes", decimals=0, mode="basic", color=G500, names="left",
                   desc="documents_bm25_sv = BM25-indexet (pg_search), documents_vec = vektorindexet (HNSW)."), w=12, h=8)
    return b
