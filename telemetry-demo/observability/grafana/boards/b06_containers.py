"""
06 · Containrar – hälsan för varje container på DGX Spark (cAdvisor, pull).
Svarar på: "Lever alla containrar, och vem äter maskinen?"

  ① Översikt       antal, omstarter, OOM, total CPU och minne
  ② Topp 5         CPU, minne, nätverk, disk – vem belastar mest just nu?
  ③ Över tid       upp/nere per container, CPU och minne per container
  ④ Alla           en tabell med allt, sorterbar
"""

from dashlib import (ACCENT, G300, G500, G700, SERVICE_COLORS, WHITE, Board, bargauge, cell, color_override, field_override,
                     join, organize, prom, stat, state_timeline, table, thresholds, timeseries)

SVC = "container_label_com_docker_compose_service"
SEL = f'{SVC}!=""'


def by(expr):
    return f"sum by ({SVC}) ({expr})"


def top5(expr):
    return f"topk(5, {by(expr)})"


CPU = f"rate(container_cpu_usage_seconds_total{{{SEL}}}[1m])"
MEM = f"container_memory_working_set_bytes{{{SEL}}}"
NET = f"rate(container_network_receive_bytes_total{{{SEL}}}[1m]) + rate(container_network_transmit_bytes_total{{{SEL}}}[1m])"
DISK = f"rate(container_fs_reads_bytes_total{{{SEL}}}[1m]) + rate(container_fs_writes_bytes_total{{{SEL}}}[1m])"
UP = f"max by ({SVC}) (time() - container_last_seen{{{SEL}}} < bool 30)"
RESTARTS = f"{by(f'changes(container_start_time_seconds{{{SEL}}}[1h])')}"


# Appens containrar i sina vanliga färger, allt annat (observability-stacken, exporters) i mörkgrått
APP_COLORS = [color_override(n, c, width=3 if n == "ai-chat" else None) for n, c in SERVICE_COLORS.items()]


def build():
    b = Board("containers", "06 · Containrar", "Lever alla containrar, och vem äter maskinen?", tags=["drift"])
    b.add(stat("Containrar som kör", [prom(f"sum({UP})")], decimals=0,
               desc="Containrar som cAdvisor sett de senaste 30 s (med compose-label)."), w=4, h=4)
    b.add(stat("Omstarter · 1 h", [prom(f"sum({RESTARTS}) or vector(0)")], decimals=0, th=thresholds((None, WHITE), (1, ACCENT)),
               desc="Hur många gånger någon container startats om senaste timmen. Över 0: kolla tabellen i ④ och tjänstens loggar."),
          w=4, h=4)
    b.add(stat("OOM-kills · 1 h", [prom(f"sum(increase(container_oom_events_total{{{SEL}}}[1h])) or vector(0)")], decimals=0,
               th=thresholds((None, WHITE), (1, ACCENT)),
               desc="Containrar som dödats för att de slog i minnesgränsen. Ska alltid vara 0."), w=4, h=4)
    b.add(stat("CPU · alla containrar", [prom(f"sum({CPU})")], unit="short", decimals=2,
               desc="Summa CPU-kärnor som containrarna använder just nu (1,0 = en hel kärna)."), w=4, h=4)
    b.add(stat("Minne · alla containrar", [prom(f"sum({MEM})")], unit="bytes", decimals=1,
               desc="Working set för alla containrar. På DGX Spark delar de 128 GB med GPU:n."), w=4, h=4)
    b.add(stat("CPU-strypning", [prom(f"sum(rate(container_cpu_cfs_throttled_periods_total{{{SEL}}}[5m])) / sum(rate(container_cpu_cfs_periods_total{{{SEL}}}[5m]))")],
               unit="percentunit", decimals=1, th=thresholds((None, WHITE), (0.1, ACCENT)),
               desc="Andel CPU-perioder där en container ville mer än sin gräns. Över 10 %: höj gränsen eller optimera."), w=4, h=4)

    b.row("② Topp 5 · vem belastar mest just nu?")
    common = dict(mode="gradient", color=None, names="left")
    b.add(bargauge("CPU", [prom(top5(CPU), "{{" + SVC + "}}", instant=True)], unit="short", decimals=2,
                   th=thresholds((None, G500), (1, ACCENT)), desc="CPU-kärnor per container. Gul över en hel kärna.", **common), w=6, h=8)
    b.add(bargauge("Minne", [prom(top5(MEM), "{{" + SVC + "}}", instant=True)], unit="bytes", decimals=0,
                   th=thresholds((None, G500), (4 * 1024 ** 3, ACCENT)), desc="Working set per container. Gul över 4 GB.", **common),
          w=6, h=8)
    b.add(bargauge("Nätverk · in + ut", [prom(top5(NET), "{{" + SVC + "}}", instant=True)], unit="Bps", decimals=0,
                   th=thresholds((None, G500)), desc="Bytes per sekund in och ut per container.", **common), w=6, h=8)
    b.add(bargauge("Disk · läs + skriv", [prom(top5(DISK), "{{" + SVC + "}}", instant=True)], unit="Bps", decimals=0,
                   th=thresholds((None, G500)), desc="Disk-I/O per container. Databaserna och Loki/Tempo brukar toppa.", **common),
          w=6, h=8)

    b.row("③ Över tid")
    b.add(state_timeline("Upp / nere per container", [prom(UP, "{{" + SVC + "}}")],
                         mappings=[{"type": "value", "options": {"1": {"text": "upp", "color": G700, "index": 0},
                                                                 "0": {"text": "NERE", "color": ACCENT, "index": 1}}}],
                         desc="Grått = containern kör. Gult = cAdvisor har inte sett den på 30 s (stoppad, kraschad, startar om)."),
          w=24, h=9)
    b.add(timeseries("CPU per container", [prom(by(CPU), "{{" + SVC + "}}")], unit="short", color=G700,
                     overrides=APP_COLORS,
                     desc="1,0 = en hel CPU-kärna. Ingen data? cAdvisor behöver cgroup v2 och Docker-socket (se docs/)."), w=12, h=9)
    b.add(timeseries("Minne per container", [prom(by(MEM), "{{" + SVC + "}}")], unit="bytes", color=G700,
                     overrides=APP_COLORS,
                     desc="Working set. En linje som bara växer och aldrig går ned = minnesläcka."), w=12, h=9)

    b.row("④ Alla containrar")
    t = lambda e, ref: prom(e, ref=ref, instant=True, fmt="table")  # noqa: E731
    b.add(table("Alla containrar · sortera på valfri kolumn", [
        t(by(CPU), "A"), t(by(MEM), "B"),
        t(f"{by(MEM)} / {by(f'container_spec_memory_limit_bytes{{{SEL}}} > 0')}", "C"),
        t(RESTARTS, "D"), t(f"time() - max by ({SVC}) (container_start_time_seconds{{{SEL}}})", "E")],
        transformations=[join(SVC), organize(exclude=["Time", "Time 1", "Time 2", "Time 3", "Time 4", "Time 5"],
                                             rename={SVC: "Container", "Value #A": "CPU (kärnor)", "Value #B": "Minne",
                                                     "Value #C": "Minne av gräns", "Value #D": "Omstarter 1 h", "Value #E": "Uptime"})],
        overrides=[field_override("CPU (kärnor)", decimals=2, display=cell("gauge", "basic"), color={"mode": "fixed", "fixedColor": G300}),
                   field_override("Minne", unit="bytes", decimals=0),
                   field_override("Minne av gräns", unit="percentunit", decimals=0, display=cell("color-text"),
                                  thresholds={"mode": "absolute", "steps": [{"value": None, "color": WHITE}, {"value": 0.8, "color": ACCENT}]},
                                  color={"mode": "thresholds"}),
                   field_override("Omstarter 1 h", decimals=0, display=cell("color-text"),
                                  thresholds={"mode": "absolute", "steps": [{"value": None, "color": WHITE}, {"value": 1, "color": ACCENT}]},
                                  color={"mode": "thresholds"}),
                   field_override("Uptime", unit="s", decimals=0)],
        sort="CPU (kärnor)", desc="En rad per container. 'Minne av gräns' är tom om containern saknar minnesgräns. Gult = över 80 % "
                                  "av gränsen eller omstartad senaste timmen."), w=24, h=16)
    return b
