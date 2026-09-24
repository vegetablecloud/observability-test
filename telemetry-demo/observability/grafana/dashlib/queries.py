"""
Queries som används på flera dashboards. Skrivs EN gång, så att samma siffra alltid betyder samma sak.
"""

APP_SERVICES = ["frontend", "backend", "ai-chat", "rag-api", "algorithm"]
APP_RE = "|".join(APP_SERVICES)

# ---- RED per tjänst, ur Tempos span-metrics (server-spans = det tjänsten själv tar emot) -----
CALLS = 'traces_spanmetrics_calls_total{span_kind="SPAN_KIND_SERVER"%s}'


def rate_by_service(extra="", window="1m"):
    return f'sum by (service) (rate({CALLS % extra}[{window}]))'


def error_ratio_by_service(window="2m"):
    err = rate_by_service(', status_code="STATUS_CODE_ERROR"', window)
    return f'({err} or {rate_by_service("", window)} * 0) / {rate_by_service("", window)}'


# p95 per tjänst ur HTTP-histogrammet (samma namn i .NET och Python tack vare semconv) – med exemplars
P95_BY_SERVICE = ('histogram_quantile(0.95, sum by (le, service_name) '
                  '(rate(http_server_request_duration_seconds_bucket{http_route!="/health", service_name=~"' + APP_RE + '"}[1m])))')

# Användarens väntetid: frontend /ask
ASK = 'http_server_request_duration_seconds%s{service_name="frontend", http_route="/ask"%s}'
ASK_RATE = f'sum(rate({ASK % ("_count", "")}[1m]))'
ASK_ERR_RATIO = (f'(sum(rate({ASK % ("_count", ", http_response_status_code=~\"5..\"")}[5m])) or vector(0)) '
                 f'/ sum(rate({ASK % ("_count", "")}[5m]))')
ASK_P95 = f'histogram_quantile(0.95, sum by (le) (rate({ASK % ("_bucket", "")}[5m])))'


# ---- status 0/1/2 per komponent (OK / STÖRD / NERE) ------------------------------------
def _named(expr, src):
    return f'label_replace({expr}, "komponent", "$1", "{src}", "(.*)")'


def status_app():
    """Push-tjänster: felkvot > 2 % = störd, > 50 % = nere. Tyst i 2 min men sett senaste timmen = nere."""
    ratio = error_ratio_by_service("2m")
    live = _named(f'(({ratio}) > bool 0.02) + (({ratio}) > bool 0.50)', "service")
    seen = _named(f'2 * group by (service_name) (max_over_time(target_info{{service_name=~"{APP_RE}"}}[1h]))', "service_name")
    return f'max by (komponent) ({live}) or max by (komponent) ({seen})'


def status_up(jobs):
    """Allt som skrapas: up = 0 -> nere."""
    expr = f'2 * (1 - max by (job) (up{{job=~"{jobs}"}}))'
    return f'max by (komponent) ({_named(expr, "job")})'


def status_vllm():
    """vLLM: nere om scrape misslyckas, störd om köer eller time-to-first-token sticker iväg."""
    up = 'max by (job) (up{job=~"vllm-.*"})'
    slow = ('(histogram_quantile(0.95, sum by (le, job) (rate({"vllm:time_to_first_token_seconds_bucket"}[2m]))) > bool 1)'
            ' or on (job) max by (job) (sum by (job) ({"vllm:num_requests_waiting"}) > bool 4)')
    expr = f'clamp_max(2 * (1 - {up}) + (({slow}) or on (job) (0 * {up})), 2)'
    return f'max by (komponent) ({_named(expr, "job")})'


def status_db():
    """Databaser via Collectorns postgresql-receiver: ingen färsk data men sedd senaste timmen = nere."""
    live = _named('0 * max by (service_name) (postgresql_backends)', "service_name")
    seen = _named('2 * max by (service_name) (max_over_time(postgresql_backends[1h]) >= 0)', "service_name")
    return f'max by (komponent) ({live}) or max by (komponent) ({seen})'
