"""
Generatorn granskar sig själv. Bygget avbryts om en regel bryts, så ingen behöver
komma ihåg reglerna vid review: titel, beskrivning, enhet, layout, datakällor, länkar.
"""

import re

from .board import GRID
from .panels import DATASOURCE_UIDS

NEEDS_UNIT = {"stat", "timeseries", "bargauge", "gauge", "heatmap"}
NO_DESC_OK = {"row", "text"}


def _overlaps(a, b):
    return not (a["x"] + a["w"] <= b["x"] or b["x"] + b["w"] <= a["x"] or a["y"] + a["h"] <= b["y"] or b["y"] + b["h"] <= a["y"])


def validate(dashboards: list[dict]) -> list[str]:
    errors, uids = [], {}
    for d in dashboards:
        uids.setdefault(d["uid"], []).append(d["title"])
    for uid, titles in uids.items():
        if len(titles) > 1:
            errors.append(f"uid '{uid}' används av flera dashboards: {titles}")

    for d in dashboards:
        where = d["title"]
        if not d.get("description"):
            errors.append(f"{where}: dashboarden saknar description (vilken fråga svarar den på?)")
        placed = []
        flat = [p for top in d["panels"] for p in [top] + top.get("panels", [])]
        for p in flat:
            name = f"{where} › {p.get('title') or p['type']}"
            g = p["gridPos"]
            if g["x"] + g["w"] > GRID:
                errors.append(f"{name}: sticker ut utanför {GRID} kolumner")
            for other in placed:
                if _overlaps(g, other[1]):
                    errors.append(f"{name}: överlappar '{other[0]}'")
            placed.append((p.get("title") or p["type"], g))
            if p["type"] not in NO_DESC_OK and not p.get("description"):
                errors.append(f"{name}: saknar description")
            if p["type"] not in ("row", "text") and not p.get("title"):
                errors.append(f"{name}: saknar titel")
            if p["type"] in NEEDS_UNIT and not p.get("fieldConfig", {}).get("defaults", {}).get("unit"):
                errors.append(f"{name}: saknar enhet")
            refs = [t.get("refId") for t in p.get("targets", [])]
            if len(refs) != len(set(refs)):
                errors.append(f"{name}: dubbla refId {refs}")
            for t in p.get("targets", []):
                uid = t.get("datasource", {}).get("uid")
                if uid not in DATASOURCE_UIDS:
                    errors.append(f"{name}: okänd datakälla '{uid}'")
                expr = t.get("expr", "")
                if expr.count("(") != expr.count(")") or expr.count("{") != expr.count("}"):
                    errors.append(f"{name}: obalanserade parenteser i query: {expr[:80]}")
            content = p.get("options", {}).get("content", "")
            for link in re.findall(r"/d/([a-z0-9-]+)", content + str(p.get("fieldConfig", {}))):
                if link not in uids:
                    errors.append(f"{name}: länkar till okänd dashboard '/d/{link}'")
    return errors
