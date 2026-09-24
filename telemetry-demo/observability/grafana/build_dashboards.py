#!/usr/bin/env python3
"""
Genererar alla Grafana-dashboards (JSON) för telemetry-demot.

    python3 observability/grafana/build_dashboards.py          # bygg + validera + skriv JSON
    python3 observability/grafana/build_dashboards.py --check  # bara kontrollera (t.ex. i CI)
    python3 observability/grafana/build_dashboards.py --draft  # länkar till ej byggda dashboards = varning

Varför en generator i stället för handskriven JSON?
  * Dashboard-JSON är mångordig och omöjlig att granska i en PR. Här syns FRÅGORNA.
  * Stil, färger och layout finns på ETT ställe (dashlib/). Alla dashboards ser likadana ut.
  * Generatorn validerar sig själv (dashlib/validate.py): titel, beskrivning, enhet, layout,
    datakällor och länkar mellan dashboards. Bygget stoppar om en regel bryts.

Struktur:
  dashlib/theme.py      färgspråket (en accentfärg, samma färg per tjänst överallt)
  dashlib/panels.py     byggstenar: prom(), loki(), traceql(), stat(), timeseries(), table(), …
  dashlib/board.py      Board: automatisk layout (ingen x/y för hand), variabler, länkar, annoteringar
  dashlib/queries.py    queries som används på flera dashboards (RED, status per komponent)
  dashlib/diagram.py    klickbara arkitekturkartor som SVG
  boards/bNN_*.py       en fil per dashboard, var och en en build()-funktion

Grafana läser JSON-filerna från dashboards/ (provisioning) och laddar om inom 30 s.
"""

import importlib
import json
import pkgutil
import sys
from pathlib import Path

HERE = Path(__file__).parent
sys.path.insert(0, str(HERE))

import boards  # noqa: E402
from dashlib import validate  # noqa: E402

OUT = HERE / "dashboards"


def build_all():
    result = []
    for mod in sorted(m.name for m in pkgutil.iter_modules(boards.__path__)):
        board = importlib.import_module(f"boards.{mod}").build()
        result.append((f"{mod[1:3]}-{board.uid}.json", board.to_json()))
    return result


def main():
    check = "--check" in sys.argv
    built = build_all()
    errors = validate([d for _, d in built])
    if "--draft" in sys.argv:
        for e in [e for e in errors if "okänd dashboard" in e]:
            print("varning:", e)
        errors = [e for e in errors if "okänd dashboard" not in e]
    if errors:
        print("Dashboards bryter mot reglerna:\n  " + "\n  ".join(errors))
        sys.exit(1)
    OUT.mkdir(exist_ok=True)
    stale = []
    for name, dash in built:
        path = OUT / name
        content = json.dumps(dash, indent=2, ensure_ascii=False) + "\n"
        if check:
            if not path.exists() or path.read_text() != content:
                stale.append(name)
        else:
            path.write_text(content)
            print(f"wrote {path.relative_to(HERE)}  ({len(dash['panels'])} paneler)")
    if not check:
        for old in OUT.glob("*.json"):
            if old.name not in {n for n, _ in built}:
                old.unlink()
                print(f"removed {old.name}")
    if stale:
        print("Inaktuella JSON-filer (kör build_dashboards.py): " + ", ".join(stale))
        sys.exit(1)


if __name__ == "__main__":
    main()
