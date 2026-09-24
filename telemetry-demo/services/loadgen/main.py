"""
loadgen – simulerar användare som chattar. Medvetet UTAN OpenTelemetry:
det är "användaren", så första spanen i varje trace skapas i frontend.
"""
import os
import random
import time

import requests

TARGET = os.getenv("TARGET_URL", "http://frontend:8080")
RPS = float(os.getenv("RPS", "2"))

QUESTIONS = [
    "Varför ska jag använda traces och inte bara logs?",
    "Hur hittar jag vilken tjänst som gör p95 långsam?",
    "Vad är cardinality i Prometheus metrics?",
    "Hur kopplar jag loggar i Loki till en trace_id?",
    "Vad gör OTel Collector med batch och sampling?",
    "Hur ser jag GPU och minne på DGX Spark?",
    "Vad är skillnaden mellan counter, gauge och histogram?",
    "Hur fungerar trace propagation mellan containers?",
    "Vad är exemplars och hur hoppar jag till en trace?",
    "Vad betyder push och pull för telemetry?",
]
USERS = [(f"u{n:04d}", f"user{n}@kund.se") for n in range(1, 60)]

print(f"loadgen -> {TARGET} @ {RPS} req/s", flush=True)
while True:
    uid, email = random.choice(USERS)
    try:
        r = requests.post(f"{TARGET}/ask", json={"question": random.choice(QUESTIONS), "userId": uid, "userEmail": email}, timeout=15)
        print(r.status_code, r.headers.get("x-trace-id", "-"), flush=True)
    except Exception as e:  # noqa: BLE001
        print("error", type(e).__name__, flush=True)
    time.sleep(random.expovariate(RPS))
