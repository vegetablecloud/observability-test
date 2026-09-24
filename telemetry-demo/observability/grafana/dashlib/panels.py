"""
Byggstenar: queries och paneler. All mångordig Grafana-JSON finns HÄR, en gång.

En panelfunktion returnerar en dict utan position. Board.add(...) placerar den.
Datakällan räknas fram ur panelens queries (flera olika -> Mixed), så den anges aldrig för hand.
"""

from .theme import ACCENT, G300, G700, SERVICE_COLORS, WHITE

PROM = {"type": "prometheus", "uid": "prometheus"}
LOKI = {"type": "loki", "uid": "loki"}
TEMPO = {"type": "tempo", "uid": "tempo"}
MIXED = {"type": "datasource", "uid": "-- Mixed --"}
DATASOURCE_UIDS = {"prometheus", "loki", "tempo", "-- Mixed --"}


# ---------------------------------------------------------------------------------------------
# Queries
# ---------------------------------------------------------------------------------------------
def prom(expr, legend="", ref=None, instant=False, exemplar=False, fmt=None, interval=None):
    t = {"datasource": PROM, "refId": ref, "expr": expr, "legendFormat": legend or "__auto",
         "range": not instant, "instant": instant, "exemplar": exemplar, "editorMode": "code"}
    if fmt:
        t["format"] = fmt
    if interval:
        t["interval"] = interval
    return t


def loki(expr, legend="", ref=None, instant=False, direction=None):
    t = {"datasource": LOKI, "refId": ref, "expr": expr, "legendFormat": legend, "editorMode": "code",
         "queryType": "instant" if instant else "range"}
    if direction:
        t["direction"] = direction
    return t


def traceql(query, ref=None, limit=20, table="traces", spss=3):
    """TraceQL-sökning. table='traces' -> en rad per trace, 'spans' -> en rad per matchande span."""
    return {"datasource": TEMPO, "refId": ref, "queryType": "traceql", "query": query, "limit": limit,
            "tableType": table, "spss": spss, "filters": []}


def trace_by_id(var="$trace_id", ref=None):
    return {"datasource": TEMPO, "refId": ref, "queryType": "traceql", "query": var, "limit": 20, "filters": []}


def service_map(ref=None):
    return {"datasource": TEMPO, "refId": ref, "queryType": "serviceMap", "serviceMapIncludeNamespace": False,
            "filters": []}


def _ds_for(targets):
    uids = {t["datasource"]["uid"] for t in targets}
    if not uids:
        return None
    return MIXED if len(uids) > 1 else targets[0]["datasource"]


def _refs(targets):
    for i, t in enumerate(targets):
        if not t.get("refId"):
            t["refId"] = chr(ord("A") + i)
    return targets


# ---------------------------------------------------------------------------------------------
# Overrides och trösklar
# ---------------------------------------------------------------------------------------------
def thresholds(*steps):
    """thresholds((None, WHITE), (2, ACCENT)) – första steget är basen."""
    return {"mode": "absolute", "steps": [{"value": v, "color": c} for v, c in steps]}


def _props(color=None, dash=False, width=None, fill=None, axis_right=False, unit=None, hidden=False):
    p = []
    if color:
        p.append({"id": "color", "value": {"mode": "fixed", "fixedColor": color}})
    if dash:
        p.append({"id": "custom.lineStyle", "value": {"fill": "dash", "dash": [6, 4]}})
    if width:
        p.append({"id": "custom.lineWidth", "value": width})
    if fill is not None:
        p.append({"id": "custom.fillOpacity", "value": fill})
    if axis_right:
        p.append({"id": "custom.axisPlacement", "value": "right"})
    if unit:
        p.append({"id": "unit", "value": unit})
    if hidden:
        p.append({"id": "custom.hideFrom", "value": {"legend": True, "tooltip": True, "viz": True}})
    return p


def color_override(name, color, **kw):
    """Serien som heter exakt `name` (legend-texten)."""
    return {"matcher": {"id": "byName", "options": name}, "properties": _props(color, **kw)}


def regex_override(regex, color=None, **kw):
    return {"matcher": {"id": "byRegexp", "options": regex}, "properties": _props(color, **kw)}


def field_override(name, **props):
    """Godtyckliga properties på ett fält, t.ex. field_override("Tid", unit="ms")."""
    p = []
    for k, v in props.items():
        p.append({"id": {"unit": "unit", "decimals": "decimals", "width": "custom.width", "display": "custom.cellOptions",
                         "name": "displayName", "links": "links", "mappings": "mappings", "thresholds": "thresholds",
                         "color": "color"}[k], "value": v})
    return {"matcher": {"id": "byName", "options": name}, "properties": p}


def service_overrides(names=None, emphasize="ai-chat"):
    names = names or SERVICE_COLORS.keys()
    return [color_override(n, SERVICE_COLORS[n], width=3 if n == emphasize else None, dash=(n in ("algorithm", "vllm-embed")))
            for n in names if n in SERVICE_COLORS]


def cell(kind, mode=None):
    """Tabellcell: cell('color-background'), cell('gauge', 'basic'), cell('color-text')."""
    c = {"type": kind}
    if mode:
        c["mode"] = mode
    return c


# ---------------------------------------------------------------------------------------------
# Paneler
# ---------------------------------------------------------------------------------------------
def panel(kind, title, targets=None, desc="", **kw):
    targets = _refs(targets or [])
    p = {"type": kind, "title": title, "description": desc, "targets": targets}
    ds = _ds_for(targets)
    if ds:
        p["datasource"] = ds
    p.update(kw)
    return p


def stat(title, targets, unit="short", desc="", th=None, decimals=None, spark=True, text_mode="value",
         mappings=None, color_mode="value", orientation="auto", reduce="lastNotNull", no_value=None, links=None,
         text_size=None, min_=None, max_=None):
    d = {"unit": unit, "color": {"mode": "thresholds"}, "thresholds": th or thresholds((None, WHITE)), "links": links or []}
    if decimals is not None:
        d["decimals"] = decimals
    if mappings:
        d["mappings"] = mappings
    if no_value is not None:
        d["noValue"] = no_value
    if min_ is not None:
        d["min"] = min_
    if max_ is not None:
        d["max"] = max_
    opts = {"reduceOptions": {"calcs": [reduce], "fields": "", "values": False},
            "colorMode": color_mode, "graphMode": "area" if spark else "none", "textMode": text_mode,
            "justifyMode": "center" if color_mode.startswith("background") else "auto",
            "orientation": orientation, "wideLayout": True, "showPercentChange": False}
    if text_size:
        opts["text"] = {"titleSize": text_size[0], "valueSize": text_size[1]}
    return panel("stat", title, targets, desc, fieldConfig={"defaults": d, "overrides": []}, options=opts)


def timeseries(title, targets, unit="short", desc="", overrides=None, fill=0, stack=False, th=None, th_style="off",
               color=None, legend="list", decimals=None, max_=None, min_=None, bars=False, points=False, log=False,
               legend_calcs=None):
    custom = {"drawStyle": "bars" if bars else ("points" if points else "line"), "lineWidth": 2,
              "fillOpacity": 80 if bars else fill, "gradientMode": "opacity" if (fill and not bars) else "none",
              "showPoints": "always" if points else "never", "pointSize": 6, "spanNulls": True, "axisBorderShow": False,
              "axisSoftMin": 0, "barAlignment": 0, "stacking": {"mode": "normal" if stack else "none", "group": "A"},
              "thresholdsStyle": {"mode": th_style}, "lineInterpolation": "smooth"}
    if log:
        custom["scaleDistribution"] = {"type": "log", "log": 10}
    d = {"unit": unit, "custom": custom,
         "color": {"mode": "fixed", "fixedColor": color} if color else {"mode": "palette-classic"}}
    if th:
        d["thresholds"] = th
    for k, v in (("decimals", decimals), ("max", max_), ("min", min_)):
        if v is not None:
            d[k] = v
    leg = {"displayMode": legend, "placement": "bottom", "showLegend": legend != "hidden", "calcs": legend_calcs or []}
    return panel("timeseries", title, targets, desc, fieldConfig={"defaults": d, "overrides": overrides or []},
                 options={"legend": leg, "tooltip": {"mode": "multi", "sort": "desc"}})


def bargauge(title, targets, unit="short", desc="", th=None, mode="gradient", orientation="horizontal", decimals=None,
             max_=None, min_=0, color=None, names="auto", overrides=None, value_mode="color", sort=None):
    d = {"unit": unit, "min": min_, "thresholds": th or thresholds((None, G300)),
         "color": {"mode": "fixed", "fixedColor": color} if color else {"mode": "thresholds"}}
    if max_ is not None:
        d["max"] = max_
    if decimals is not None:
        d["decimals"] = decimals
    p = panel("bargauge", title, targets, desc, fieldConfig={"defaults": d, "overrides": overrides or []},
              options={"reduceOptions": {"calcs": ["lastNotNull"], "fields": "", "values": False},
                       "orientation": orientation, "displayMode": mode, "valueMode": value_mode,
                       "namePlacement": names, "showUnfilled": True, "sizing": "auto", "minVizHeight": 16,
                       "minVizWidth": 8, "maxVizHeight": 36, "legend": {"showLegend": False}})
    if sort:
        p["transformations"] = [{"id": "sortBy", "options": {"sort": [{"field": sort, "desc": True}]}}]
    return p


def table(title, targets, desc="", transformations=None, overrides=None, unit="short", sort=None, links=None,
          cell_height="sm", filterable=False, footer=False, min_width=None, time_from=None):
    """time_from="10m" = panelen visar alltid bara de senaste 10 minuterna (t.ex. 'senaste körningarna')."""
    opts = {"showHeader": True, "cellHeight": cell_height, "footer": {"show": footer, "reducer": ["sum"], "fields": ""}}
    if sort:
        opts["sortBy"] = [{"displayName": sort[0], "desc": sort[1] if isinstance(sort, tuple) else True}] \
            if isinstance(sort, tuple) else [{"displayName": sort, "desc": True}]
    custom = {"align": "auto", "cellOptions": {"type": "auto"}, "filterable": filterable}
    if min_width:
        custom["minWidth"] = min_width
    extra = {"timeFrom": time_from} if time_from else {}
    return panel("table", title, targets, desc,
                 fieldConfig={"defaults": {"unit": unit, "custom": custom, "links": links or []},
                              "overrides": overrides or []},
                 options=opts, transformations=transformations or [], **extra)


def logs(title, expr, desc="", ascending=False, labels=False, wrap=True):
    return panel("logs", title, [loki(expr, direction="forward" if ascending else "backward")], desc,
                 options={"showTime": True, "showLabels": labels, "showCommonLabels": False, "wrapLogMessage": wrap,
                          "prettifyLogMessage": False, "enableLogDetails": True,
                          "sortOrder": "Ascending" if ascending else "Descending", "dedupStrategy": "none",
                          "enableInfiniteScrolling": True})


def text(content, title="", mode="markdown", transparent=True, desc=""):
    return panel("text", title, [], desc, options={"mode": mode, "content": content, "code": {"language": "plaintext"}},
                 transparent=transparent)


def node_graph(title, targets, desc="", transformations=None):
    return panel("nodeGraph", title, targets, desc, options={"nodes": {}, "edges": {}},
                 transformations=transformations or [])


def traces(title, desc="", var="$trace_id"):
    """Hela trace-waterfallen direkt i dashboarden."""
    return panel("traces", title, [trace_by_id(var)], desc, options={})


def heatmap(title, targets, unit="s", desc=""):
    return panel("heatmap", title, targets, desc,
                 fieldConfig={"defaults": {"unit": unit, "custom": {"hideFrom": {"legend": False, "tooltip": False, "viz": False},
                                                                     "scaleDistribution": {"type": "linear"}}}, "overrides": []},
                 options={"calculate": False, "cellGap": 1, "yAxis": {"axisPlacement": "left", "unit": unit, "decimals": 1},
                          "color": {"mode": "opacity", "fill": ACCENT, "exponent": 0.5, "scale": "exponential", "steps": 64,
                                    "reverse": False},
                          "rowsFrame": {"layout": "auto"}, "filterValues": {"le": 1e-9}, "showValue": "never",
                          "tooltip": {"mode": "single", "yHistogram": True, "showColorScale": True},
                          "legend": {"show": True}, "exemplars": {"color": WHITE}, "cellValues": {"unit": "short"}})


def state_timeline(title, targets, desc="", mappings=None, th=None, unit="short", row_height=0.8):
    return panel("state-timeline", title, targets, desc,
                 fieldConfig={"defaults": {"unit": unit, "color": {"mode": "thresholds"}, "mappings": mappings or [],
                                           "thresholds": th or thresholds((None, G700)),
                                           "custom": {"fillOpacity": 85, "lineWidth": 0}}, "overrides": []},
                 options={"showValue": "never", "rowHeight": row_height, "mergeValues": True, "alignValue": "center",
                          "legend": {"showLegend": False}, "tooltip": {"mode": "single"}})


# Enkla transformationer som återkommer
def organize(rename=None, exclude=None, order=None):
    o = {"renameByName": rename or {}, "excludeByName": {k: True for k in (exclude or [])}}
    if order:
        o["indexByName"] = {k: i for i, k in enumerate(order)}
    return {"id": "organize", "options": o}


def join(field, mode="outer"):
    return {"id": "joinByField", "options": {"byField": field, "mode": mode}}


def merge():
    return {"id": "merge", "options": {}}


def sort_by(field, desc=True):
    return {"id": "sortBy", "options": {"sort": [{"field": field, "desc": desc}]}}


# TraceQL-tabeller (table="spans"): Tempo ger kolumnerna visningsnamn. organize arbetar på visningsnamnen.
TEMPO_BASE = {"Start time": "Start", "Name": "Steg", "Duration": "Tid", "Span ID": "Span", "traceIdHidden": "trace_id"}
TEMPO_HIDE = ["Trace Service", "Trace Name", "kind"]


def tempo_columns(attrs=None, order=None, hide=()):
    """Svenska kolumnnamn och ordning för en TraceQL-tabell. attrs: {"agent.outcome": "Utfall", ...}."""
    return organize(rename={**TEMPO_BASE, **(attrs or {})}, exclude=TEMPO_HIDE + list(hide), order=order)


def limit(n):
    return {"id": "limit", "options": {"limitField": n}}


