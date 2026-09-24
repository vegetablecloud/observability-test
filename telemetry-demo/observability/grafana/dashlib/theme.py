"""
Färgspråk. ETT ställe att byta palett på.

Regeln: svart/vitt/grått för allt normalt. GULT bara för det som kräver uppmärksamhet just nu:
huvudserien i en graf, ett passerat tröskelvärde, något som är nere. Då betyder gult alltid
"titta här", och ingen behöver lära sig vad åtta olika färger betyder.
"""

ACCENT = "#FFB400"        # Imperial Yellow – uppmärksamhet
ACCENT_DIM = "#7A5600"    # samma nyans, mörkare: "störd" (bakgrund på statusrutor)
WHITE = "#FFFFFF"
G200 = "#EDEDED"
G300 = "#D6D6D6"
G500 = "#707070"
G700 = "#4D4D4D"
TILE = "#161616"          # bakgrund för en statusruta som är OK
TRANSPARENT = "transparent"

# Samma tjänst har samma färg på ALLA dashboards. Huvudaktören (agenten) är accentfärgad.
SERVICE_COLORS = {
    "frontend": WHITE,
    "backend": G300,
    "ai-chat": ACCENT,
    "rag-api": G200,
    "algorithm": G500,
    "vllm-gemma": WHITE,
    "vllm-embed": G500,
    "postgres": G700,
    "paradedb": G300,
    "user": G500,
    "partner-service": G700,
}

# LangGraph-noderna, i grafens ordning (används för färger och sortering)
NODE_COLORS = {"guard_input": G500, "agent": ACCENT, "tools": WHITE, "respond": G300}
TOOL_COLORS = {"search_documents": WHITE, "get_project_insight": G300}

# Statusrutor: 0 = OK, 1 = störd, 2 = nere
STATUS_MAP = [{"type": "value", "options": {
    "0": {"text": "OK", "color": TILE, "index": 0},
    "1": {"text": "STÖRD", "color": ACCENT_DIM, "index": 1},
    "2": {"text": "NERE", "color": ACCENT, "index": 2},
}}]
UP_MAP = [{"type": "value", "options": {
    "1": {"text": "UP", "color": TILE, "index": 0},
    "0": {"text": "DOWN", "color": ACCENT, "index": 1},
}}]
