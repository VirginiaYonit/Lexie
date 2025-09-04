#from __future__ import annotations
from typing import Dict, Any, List
from ..retriever import retrieve_law_chunks
from ..legal_analyzer_gpt import legal_analyze_with_gpt, build_prompt
from .postprocess import normalize_contract
from ..config import POLICIES as DEFAULT_POLICIES, TOP_K as TOP_K_DEFAULT
try:
    from ..config import MAX_EVIDENCE_CHARS
except Exception:
    MAX_EVIDENCE_CHARS = 1000




def handle(payload: Dict[str, Any]) -> Dict[str, Any]:
    assert payload.get("mode") == "free_text", "expects mode=free_text"
    user_text = (payload.get("user_text") or "").strip()
    top_k = int(payload.get("top_k", 12))

    k_ai = max(1, top_k // 2)
    k_gdpr = top_k - k_ai
    law_chunks: List[Dict[str, Any]] = (
        retrieve_law_chunks(user_text, ["ai_act"], top_k=k_ai)
        + retrieve_law_chunks(user_text, ["gdpr"],   top_k=k_gdpr)
    )

    # normalizza source
    def _norm_source(x: str) -> str:
        s = (x or "").strip().lower().replace(" ", "_")
        if "gdpr" in s: return "gdpr"
        if "ai" in s and "act" in s: return "ai_act"
        return s or "gdpr"
    for ch in law_chunks:
        ch["source"] = _norm_source(ch.get("source","gdpr"))

    prompt = build_prompt(user_text, law_chunks)
    raw = legal_analyze_with_gpt(prompt, law_chunks, temperature=0.0, seed=42)

    return normalize_contract(raw, evidences=law_chunks)

