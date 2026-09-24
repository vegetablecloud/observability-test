"""
07 · DGX Spark – maskinen allt kör på (node-exporter + dcgm-exporter, pull).
Svarar på: "Har maskinen resurser kvar, och är GPU:n frisk?"

  ① Nu          CPU, minne, disk, GPU, temperatur, effekt
  ② GPU         utnyttjande, minne, temperatur/effekt, klockfrekvens (strypning)
  ③ Värden      CPU per läge, minne, nätverk, disk
  ④ Runtimes    .NET (frontend, backend) – GC och minne ur OTel-SDK:t
"""

from dashlib import (ACCENT, G300, G500, G700, WHITE, Board, color_override, prom, service_overrides, stat, thresholds, timeseries)

CPU = '100 * (1 - avg(rate(node_cpu_seconds_total{mode="idle"}[1m])))'
MEM = "100 * (1 - sum(node_memory_MemAvailable_bytes) / sum(node_memory_MemTotal_bytes))"
DISK = '100 * (1 - max(node_filesystem_avail_bytes{mountpoint="/"}) / max(node_filesystem_size_bytes{mountpoint="/"}))'
NIC = 'device!~"lo|veth.*|docker.*|br-.*"'


def build():
    b = Board("infra-dgx", "07 · DGX Spark", "Har maskinen resurser kvar, och är GPU:n frisk?", tags=["drift"])
    b.add(stat("CPU", [prom(CPU)], unit="percent", decimals=0, th=thresholds((None, WHITE), (85, ACCENT)),
               desc="Hela maskinens CPU (alla kärnor). Gul över 85 %."), w=4, h=4)
    b.add(stat("Minne", [prom(MEM)], unit="percent", decimals=0, th=thresholds((None, WHITE), (90, ACCENT)),
               desc="Använt minne. På DGX Spark är det samma 128 GB som GPU:n använder (unified memory)."), w=4, h=4)
    b.add(stat("Disk /", [prom(DISK)], unit="percent", decimals=0, th=thresholds((None, WHITE), (85, ACCENT)),
               desc="Rotfilsystemet. Modellvikter, Loki och Tempo fyller disken över tid."), w=4, h=4)
    b.add(stat("GPU", [prom("avg(DCGM_FI_DEV_GPU_UTIL)")], unit="percent", decimals=0, th=thresholds((None, WHITE), (90, ACCENT)),
               desc="GPU-utnyttjande. Konstant över 90 %: modellerna köar."), w=4, h=4)
    b.add(stat("GPU-temp", [prom("max(DCGM_FI_DEV_GPU_TEMP)")], unit="celsius", decimals=0, th=thresholds((None, WHITE), (80, ACCENT)),
               desc="Över 80 °C börjar GPU:n strypa klockan (se ②)."), w=4, h=4)
    b.add(stat("GPU-effekt", [prom("sum(DCGM_FI_DEV_POWER_USAGE)")], unit="watt", decimals=0,
               desc="Strömförbrukning. Följer utnyttjandet."), w=4, h=4)

    b.row("② GPU · dcgm-exporter")
    b.add(timeseries("GPU-utnyttjande", [prom("avg by (gpu) (DCGM_FI_DEV_GPU_UTIL)", "gpu {{gpu}}")], unit="percent", max_=100,
                     color=ACCENT, fill=15, th=thresholds((None, "transparent"), (90, ACCENT)), th_style="dashed",
                     desc="Streckad linje = 90 %. Kurvan ska följa trafiken, inte ligga i taket."), w=6, h=8)
    b.add(timeseries("GPU-minne (unified)", [
        prom("sum(DCGM_FI_DEV_FB_USED) * 1024 * 1024", "använt"),
        prom("(sum(DCGM_FI_DEV_FB_USED) + sum(DCGM_FI_DEV_FB_FREE)) * 1024 * 1024", "totalt")],
        unit="bytes", overrides=[color_override("använt", WHITE), color_override("totalt", G700, dash=True)],
        desc="vLLM reserverar en fast andel (gpu-memory-utilization) vid start, så 'använt' är mest platt."), w=6, h=8)
    b.add(timeseries("Temperatur & effekt", [prom("max(DCGM_FI_DEV_GPU_TEMP)", "°C"), prom("sum(DCGM_FI_DEV_POWER_USAGE)", "W")],
                     overrides=[color_override("°C", WHITE), color_override("W", G500, dash=True, axis_right=True)],
                     desc="Temperatur (vänster axel) och effekt (höger axel)."), w=6, h=8)
    b.add(timeseries("SM-klocka", [prom("avg(DCGM_FI_DEV_SM_CLOCK)", "MHz")], unit="short", color=G300,
                     desc="Klockfrekvensen sjunker när GPU:n är varm eller slår i effektgränsen (strypning). Då blir allt långsammare."),
          w=6, h=8)

    b.row("③ Värden · node-exporter")
    b.add(timeseries("CPU per läge", [
        prom('100 * sum by (mode) (rate(node_cpu_seconds_total{mode=~"user|system|iowait"}[1m])) / scalar(count(count by (cpu) (node_cpu_seconds_total)))',
             "{{mode}}")], unit="percent", stack=True, fill=40,
        overrides=[color_override("user", WHITE), color_override("system", G500), color_override("iowait", ACCENT)],
        desc="iowait (gul) = CPU:n väntar på disk. Hög iowait + långsamma frågor = disken är flaskhalsen."), w=6, h=8)
    b.add(timeseries("Minne", [
        prom("sum(node_memory_MemTotal_bytes) - sum(node_memory_MemAvailable_bytes)", "använt"),
        prom("sum(node_memory_MemTotal_bytes)", "totalt")], unit="bytes",
        overrides=[color_override("använt", WHITE), color_override("totalt", G700, dash=True)], desc="Använt mot totalt."), w=6, h=8)
    b.add(timeseries("Nätverk", [
        prom(f"sum(rate(node_network_receive_bytes_total{{{NIC}}}[1m]))", "in"),
        prom(f"-sum(rate(node_network_transmit_bytes_total{{{NIC}}}[1m]))", "ut")], unit="Bps",
        overrides=[color_override("in", WHITE), color_override("ut", G500)], desc="In uppåt, ut nedåt."), w=6, h=8)
    b.add(timeseries("Disk-I/O", [
        prom("sum(rate(node_disk_read_bytes_total[1m]))", "läs"), prom("-sum(rate(node_disk_written_bytes_total[1m]))", "skriv")],
        unit="Bps", overrides=[color_override("läs", WHITE), color_override("skriv", G500)], desc="Läs uppåt, skriv nedåt."), w=6, h=8)

    b.row("④ Runtimes · ur OTel-SDK:t (push)")
    b.add(timeseries(".NET · working set", [prom("sum by (service_name) (dotnet_process_memory_working_set_bytes)", "{{service_name}}")],
                     unit="bytes", overrides=service_overrides(), desc="Minnet .NET-processen använder, per tjänst."), w=8, h=8)
    b.add(timeseries(".NET · GC-paus", [prom("sum by (service_name) (rate(dotnet_gc_pause_time_seconds_total[1m]))", "{{service_name}}")],
                     unit="percentunit", overrides=service_overrides(),
                     desc="Andel av tiden processen står still för garbage collection. Över några procent syns det i latensen."), w=8, h=8)
    b.add(timeseries(".NET · trådpoolskö", [prom("sum by (service_name) (dotnet_thread_pool_queue_length_total)", "{{service_name}}")],
                     overrides=service_overrides(),
                     desc="Arbete som väntar på en tråd. Växer den: synkrona anrop blockerar trådpoolen."), w=8, h=8)
    return b
