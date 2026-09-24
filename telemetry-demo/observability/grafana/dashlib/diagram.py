"""
Arkitekturkartor som SVG i en text-panel (HTML-läge). Rutorna är länkar till rätt dashboard,
och request-vägen är animerad så att man ser åt vilket håll trafiken går.

    boxes = [Box("frontend", 200, 150, "frontend", "C# · UI", link="/d/platform-overview"), ...]
    edges = [Edge("frontend", "backend"), Edge("ai-chat", "vllm-gemma", kind="request", label="chat")]
    html = svg_map(boxes, edges, columns=[(20, "① ANVÄNDARE"), ...])

Kräver GF_PANELS_DISABLE_SANITIZE_HTML=true i Grafana (annars rensas SVG och länkar bort).
"""

from dataclasses import dataclass

from .theme import ACCENT, G300, G500, G700, WHITE

FONT = "Roboto Mono, ui-monospace, monospace"


@dataclass
class Box:
    id: str
    x: int
    y: int
    title: str
    sub: str = ""
    link: str = ""
    w: int = 180
    h: int = 56
    accent: bool = False
    dashed: bool = False   # streckad kant = något du inte äger (pull)


@dataclass
class Edge:
    src: str
    dst: str
    label: str = ""
    kind: str = "request"  # request (animerad, gul) · pull (streckad grå) · telemetry (tunn grå)


def _anchor(a: Box, b: Box):
    """Punkt på a:s kant i riktning mot b."""
    ax, ay, bx, by = a.x + a.w / 2, a.y + a.h / 2, b.x + b.w / 2, b.y + b.h / 2
    dx, dy = bx - ax, by - ay
    if abs(dx) * a.h > abs(dy) * a.w:
        return (a.x + a.w if dx > 0 else a.x), ay
    return ax, (a.y + a.h if dy > 0 else a.y)


def svg_map(boxes, edges, columns=(), width=1600, height=460, legend=True):
    by_id = {b.id: b for b in boxes}
    out = [f'<svg viewBox="0 0 {width} {height}" width="100%" style="max-height:{height}px" xmlns="http://www.w3.org/2000/svg" '
           f'font-family="{FONT}">',
           f'''<style>
  .bx rect {{ fill:#0D0D0D; stroke:{G700}; stroke-width:1.5; transition:stroke .15s; }}
  .bx.acc rect {{ stroke:{ACCENT}; stroke-width:2; }}
  .bx.ext rect {{ stroke-dasharray:5 4; }}
  a:hover .bx rect {{ stroke:{ACCENT}; fill:#141414; }}
  .t {{ fill:{WHITE}; font-size:15px; }} .s {{ fill:{G500}; font-size:12px; }}
  .col {{ fill:{G500}; font-size:12px; letter-spacing:1.5px; }}
  .lbl {{ fill:{G500}; font-size:11px; }} .lbl.hot {{ fill:{ACCENT}; }}
  path.req {{ stroke:{ACCENT}; stroke-width:2.2; fill:none; stroke-dasharray:7 6; animation:flow 1.2s linear infinite; }}
  path.pull {{ stroke:{G500}; stroke-width:1.5; fill:none; stroke-dasharray:3 5; }}
  path.tel {{ stroke:{G700}; stroke-width:1.2; fill:none; }}
  @keyframes flow {{ to {{ stroke-dashoffset:-26; }} }}
</style>''',
           f'<defs><marker id="ah" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="6" markerHeight="6" orient="auto">'
           f'<path d="M0 0L10 5L0 10z" fill="{ACCENT}"/></marker>'
           f'<marker id="ag" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="6" markerHeight="6" orient="auto">'
           f'<path d="M0 0L10 5L0 10z" fill="{G500}"/></marker></defs>']
    for x, label in columns:
        out.append(f'<text class="col" x="{x}" y="20">{label}</text>')
    for e in edges:
        a, b = by_id[e.src], by_id[e.dst]
        (x1, y1), (x2, y2) = _anchor(a, b), _anchor(b, a)
        cls = {"request": "req", "pull": "pull", "telemetry": "tel"}[e.kind]
        marker = "ah" if e.kind == "request" else "ag"
        out.append(f'<path class="{cls}" d="M{x1:.0f} {y1:.0f} L{x2:.0f} {y2:.0f}" marker-end="url(#{marker})"/>')
        if e.label:
            mx, my = (x1 + x2) / 2, (y1 + y2) / 2
            out.append(f'<text class="lbl {"hot" if e.kind == "request" else ""}" x="{mx + 6:.0f}" y="{my - 6:.0f}">{e.label}</text>')
    for b in boxes:
        cls = "bx" + (" acc" if b.accent else "") + (" ext" if b.dashed else "")
        g = (f'<g class="{cls}"><rect x="{b.x}" y="{b.y}" width="{b.w}" height="{b.h}" rx="2"/>'
             f'<text class="t" x="{b.x + 12}" y="{b.y + 24}">{b.title}</text>'
             f'<text class="s" x="{b.x + 12}" y="{b.y + 43}">{b.sub}</text></g>')
        out.append(f'<a href="{b.link}">{g}</a>' if b.link else g)
    if legend:
        y = height - 8
        out.append(f'<path class="req" d="M20 {y - 4} L60 {y - 4}"/><text class="lbl" x="68" y="{y}">en fråga genom stacken</text>'
                   f'<path class="pull" d="M260 {y - 4} L300 {y - 4}"/><text class="lbl" x="308" y="{y}">pull · du äger inte koden</text>'
                   f'<path class="tel" d="M520 {y - 4} L560 {y - 4}"/><text class="lbl" x="568" y="{y}">telemetri</text>'
                   f'<text class="lbl" x="720" y="{y}" style="fill:{G300}">klicka på en ruta för dess dashboard</text>')
    out.append("</svg>")
    return "\n".join(out)
