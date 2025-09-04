import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent

# Modello LLM
MODEL_ID = os.getenv("LEXIE_GPT_MODEL", "gpt-4o-mini")

# Retrieval
TOP_K = int(os.getenv("LEXIE_TOP_K", "10"))
MAX_EVIDENCE_CHARS = int(os.getenv("LEXIE_MAX_EVIDENCE_CHARS", "1000"))
POLICIES = ["gdpr", "ai_act"]

CHUNK_MAX_TOKENS = 350
CHUNK_OVERLAP_TOKENS = 60
CHUNK_MIN_TOKENS = 200
USER_TEXT_CAP = 16000
RETRIEVAL_BALANCE = {"gdpr": 0.5, "ai_act": 0.5}
STRICT_GDPR_PROMPT = True

# Runtime
OUTPUT_DIR = BASE_DIR / "runtime" / "outputs"
LOG_DIR = BASE_DIR / "runtime" / "logs"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
LOG_DIR.mkdir(parents=True, exist_ok=True)

def level_from_score(x: int) -> str:
    try:
        x = int(x)
    except Exception:
        x = 0
    if x < 33: return "low"
    if x < 66: return "medium"
    return "high"
    


