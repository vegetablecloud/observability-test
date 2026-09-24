"""
loadgen – simulerar användare som chattar med agenten. Medvetet UTAN OpenTelemetry:
det är "användaren", så första spanen i varje trace skapas i frontend.

Frågorna är valda så att agenten tar olika vägar genom grafen:
  bara search_documents · search_documents + get_project_insight · okänt projekt (verktygsfel)
"""
import os
import random
import time

import requests

TARGET = os.getenv("TARGET_URL", "http://frontend:8080")
RPS = float(os.getenv("RPS", "2"))

QUESTIONS = [
    # observability -> search_documents
    "Varför ska jag använda traces och inte bara logs?",
    "Hur hittar jag vilken tjänst som gör p95 långsam?",
    "Vad är cardinality i Prometheus metrics?",
    "Hur kopplar jag loggar i Loki till en trace_id?",
    "Vad gör OTel Collector med batch och sampling?",
    "Hur ser jag GPU och minne på DGX Spark?",
    "Hur ser jag vilken LangGraph-nod som felar?",
    "Vad händer när en agent når recursion limit?",
    # projekt -> search_documents + get_project_insight
    "Hur ser prognosen ut för projekt P-101?",
    "Vilka risker finns i projekt P-102?",
    "Vad är status för projekt P-103 och är leveransen försenad?",
    "Håller budgeten i projekt P-105 enligt prognos?",
    "Vad är den största risken i projekt P-107?",
]
RARE = ["Vad är status för projekt P-999?"]  # okänt projekt -> verktyget ger 404, agenten hanterar det

USERS = [(f"u{n:04d}", f"user{n}@kund.se") for n in range(1, 60)]

print(f"loadgen -> {TARGET} @ {RPS} req/s", flush=True)
while True:
    uid, email = random.choice(USERS)
    q = random.choice(RARE) if random.random() < 0.03 else random.choice(QUESTIONS)
    try:
        r = requests.post(f"{TARGET}/ask", json={"question": q, "userId": uid, "userEmail": email},
                          headers={"x-test-run-id": "loadgen"}, timeout=20)
        print(r.status_code, r.headers.get("x-trace-id", "-"), flush=True)
    except Exception as e:  # noqa: BLE001
        print("error", type(e).__name__, flush=True)
    time.sleep(random.expovariate(RPS))
