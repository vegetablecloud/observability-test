"""
Board: en dashboard med automatisk layout.

    b = Board("ai-agent", "03 · AI-agent · LangGraph", "Hur arbetar agenten, steg för steg?")
    b.row("① Hur mår agenten?")
    b.add(stat(...), w=4, h=4)      # läggs till höger om föregående, radbryts vid 24 kolumner
    b.add(timeseries(...), w=12, h=8)
    b.newline()

Inga x/y-koordinater för hand: ordningen i koden ÄR ordningen på skärmen.
"""

GRID = 24
TAG = "telemetry-demo"

# Vertikala markörer i alla grafer när någon slår på ett chaos-läge. Loggraden kommer från
# frontend ("chaos_mode_set mode=slow ..."), så markören är samma sanning som loggarna.
CHAOS_ANNOTATION = {
    "name": "Chaos", "enable": True, "iconColor": "#FFB400", "hide": False,
    "datasource": {"type": "loki", "uid": "loki"},
    "expr": '{service_name="frontend"} |= "chaos_mode_set" | regexp "mode=(?P<mode>[a-z_]+)"',
    "titleFormat": "chaos: {{mode}}", "textFormat": "{{mode}}", "tagKeys": "mode", "instant": False,
}


class Board:
    def __init__(self, uid, title, desc, time="now-30m", refresh="10s", tags=None):
        self.uid, self.title, self.desc = uid, title, desc
        self.time, self.refresh = time, refresh
        self.tags = [TAG] + (tags or [])
        self.panels, self.variables = [], []
        self._x = self._y = self._line_h = 0
        self._id = 0
        self._collapsed = None  # hopfälld rad: panelerna läggs INUTI raden

    # ---- layout -------------------------------------------------------------------------
    def _next_id(self):
        self._id += 1
        return self._id

    def newline(self):
        if self._x:
            self._y += self._line_h
        self._x = self._line_h = 0

    def add(self, p, w, h):
        if self._x + w > GRID:
            self.newline()
        p = dict(p, id=self._next_id(), gridPos={"x": self._x, "y": self._y, "w": w, "h": h})
        (self._collapsed["panels"] if self._collapsed else self.panels).append(p)
        self._x += w
        self._line_h = max(self._line_h, h)
        if self._x == GRID:
            self.newline()
        return p

    def row(self, title, collapsed=False):
        self.newline()
        r = {"id": self._next_id(), "type": "row", "title": title, "collapsed": collapsed,
             "gridPos": {"x": 0, "y": self._y, "w": GRID, "h": 1}, "panels": []}
        self.panels.append(r)
        self._collapsed = r if collapsed else None
        self._y += 1

    # ---- variabler ----------------------------------------------------------------------
    def textbox(self, name, label, default=""):
        self.variables.append({"type": "textbox", "name": name, "label": label, "query": default,
                               "current": {"text": default, "value": default}, "hide": 0, "options": []})

    def custom(self, name, label, values, default=None, include_all=False, multi=False):
        default = default or values[0]
        self.variables.append({
            "type": "custom", "name": name, "label": label, "query": ",".join(values), "multi": multi,
            "includeAll": include_all, "allValue": ".*" if include_all else None, "hide": 0,
            "current": {"text": default, "value": default},
            "options": [{"text": v, "value": v, "selected": v == default} for v in values]})

    def prom_values(self, name, label, metric, label_name, include_all=True, regex=""):
        self.variables.append({
            "type": "query", "name": name, "label": label, "datasource": {"type": "prometheus", "uid": "prometheus"},
            "query": {"qryType": 1, "query": f"label_values({metric}, {label_name})", "refId": "vars"},
            "definition": f"label_values({metric}, {label_name})", "refresh": 2, "regex": regex, "sort": 1,
            "includeAll": include_all, "allValue": ".*" if include_all else None, "multi": include_all,
            "current": {"text": "All", "value": "$__all"} if include_all else {}, "hide": 0, "options": []})

    # ---- JSON ---------------------------------------------------------------------------
    def to_json(self):
        return {
            "uid": self.uid, "title": self.title, "description": self.desc, "tags": self.tags,
            "editable": True, "graphTooltip": 1,  # delad crosshair: samma tidpunkt i alla paneler
            "time": {"from": self.time, "to": "now"}, "refresh": self.refresh, "schemaVersion": 41, "version": 1,
            "timepicker": {}, "timezone": "browser", "fiscalYearStartMonth": 0, "liveNow": False,
            "templating": {"list": self.variables}, "annotations": {"list": [CHAOS_ANNOTATION]},
            "links": [
                {"title": "00 · Start", "type": "link", "url": "/d/start", "icon": "apps", "keepTime": True,
                 "includeVars": False, "targetBlank": False, "tooltip": "Startsidan", "asDropdown": False, "tags": []},
                {"title": "Dashboards", "type": "dashboards", "tags": [TAG], "asDropdown": True, "includeVars": False,
                 "keepTime": True, "targetBlank": False, "icon": "external link"},
            ],
            "panels": self.panels,
        }
