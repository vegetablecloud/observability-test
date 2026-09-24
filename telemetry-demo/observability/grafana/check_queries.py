#!/usr/bin/env python3
"""
Kör VARJE query i varje dashboard mot en riktig Grafana och listar paneler som inte ger data.

    python3 observability/grafana/check_queries.py                          # http://localhost:3000
    GRAFANA_URL=https://grafana.x GRAFANA_TOKEN=glsa_… python3 check_queries.py
    python3 check_queries.py --only ai-agent                                # en dashboard

Går via Grafanas /api/ds/query, alltså samma väg som panelerna, med samma datakällor.
Använd det efter varje ändring: en query som "ser rätt ut" men ger tomt svar är den
vanligaste buggen i dashboards (fel metric-namn, fel label, saknat _total-suffix).

Exit-kod 1 om någon query ger fel. Tomma svar är varningar: vissa paneler är tomma med flit
tills något händer (fel, omstarter, chaos-lägen).
"""

import json
import os
import sys
import time
import urllib.request
from pathlib import Path

GRAFANA = os.getenv("GRAFANA_URL", "http://localhost:3000").rstrip("/")
TOKEN = os.getenv("GRAFANA_TOKEN", "")
HERE = Path(__file__).parent

# Standardvärden för dashboard-variabler när queries körs utanför en webbläsare
VARS = {"$model": ".*", "$db": ".*", "$__rate_interval": "1m", "$__range": "30m", "$__interval": "30s"}


def ds_query(target, minutes=30):
    now = int(time.time() * 1000)
    body = {"queries": [dict(target, refId="A", intervalMs=30000, maxDataPoints=200)],
            "from": str(now - minutes * 60_000), "to": str(now)}
    req = urllib.request.Request(f"{GRAFANA}/api/ds/query", data=json.dumps(body).encode(),
                                 headers={"content-type": "application/json", **({"Authorization": f"Bearer {TOKEN}"} if TOKEN else {})})
    try:
        res = json.load(urllib.request.urlopen(req, timeout=30))["results"]["A"]
    except urllib.error.HTTPError as e:
        try:
            return "error", json.load(e)["results"]["A"].get("error", str(e))
        except Exception:  # noqa: BLE001
            return "error", str(e)
    if res.get("error"):
        return "error", res["error"]
    rows = sum(len(f["data"]["values"][0]) if f["data"]["values"] else 0 for f in res.get("frames", []))
    return ("ok", rows) if rows else ("empty", 0)


def substitute(t, variables):
    s = json.dumps(t)
    for k, v in {**VARS, **variables}.items():
        s = s.replace(k, v)
    return json.loads(s)


def main():
    only = sys.argv[sys.argv.index("--only") + 1] if "--only" in sys.argv else None
    errors = empties = total = 0
    for path in sorted((HERE / "dashboards").glob("*.json")):
        d = json.loads(path.read_text())
        if only and d["uid"] != only:
            continue
        variables = {f"${v['name']}": (v.get("query") or "") for v in d["templating"]["list"] if v["type"] == "textbox"}
        if not variables.get("$trace_id"):
            variables["$trace_id"] = ""
        print(f"\n{d['title']}")
        panels = [p for top in d["panels"] for p in [top] + top.get("panels", [])]
        for p in panels:
            for t in p.get("targets", []):
                if "$trace_id" in json.dumps(t) and not variables["$trace_id"]:
                    continue  # kräver att användaren valt en trace
                if t.get("queryType") == "serviceMap":
                    continue  # service map byggs delvis i Grafanas frontend och går inte att köra via /api/ds/query
                total += 1
                status, info = ds_query(substitute(t, variables))
                if status == "ok":
                    continue
                mark = "FEL " if status == "error" else "tom "
                errors += status == "error"
                empties += status == "empty"
                q = t.get("expr") or t.get("query") or t.get("queryType")
                print(f"  {mark} {p['title']} [{t['refId']}]  {str(info)[:160] if status == 'error' else ''}\n        {q[:150]}")
    print(f"\n{total} queries · {errors} fel · {empties} tomma")
    sys.exit(1 if errors else 0)


if __name__ == "__main__":
    main()
