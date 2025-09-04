# tools/analyze_document.py
from __future__ import annotations
from typing import Dict, Any, List
from pathlib import Path
from ..loaders import load_file_text
from ..retriever import retrieve_law_chunks
from ..legal_analyzer_gpt import legal_analyze_with_gpt, build_prompt
from .postprocess import normalize_contract
from ..config import TOP_K as TOP_K_DEFAULT
# in cima al file, con gli altri import
try:
    from ..config import (
        CHUNK_MAX_TOKENS,
        CHUNK_OVERLAP_TOKENS,
        CHUNK_MIN_TOKENS,
        USER_TEXT_CAP,
    )
except Exception:
    CHUNK_MAX_TOKENS = 350
    CHUNK_OVERLAP_TOKENS = 60
    CHUNK_MIN_TOKENS = 200
    USER_TEXT_CAP = 16000
import re

_GDPR_KWS = (
    r"(consent|lawful|legal\s+basis|art\.?\s*5|art\.?\s*6|art\.?\s*9|art\.?\s*13|art\.?\s*14|art\.?\s*22|dpia|data\s+minimi[sz]ation|personal\s+data|data\s+subject|profiling|automated\s+decision)"
)

def _extract_gdpr_signals(text: str, max_lines: int = 20) -> str:
    # prendi righe/sentenze che contengono keyword GDPR
    lines = re.split(r'(?<=[\.\?!])\s+|\n+', text)
    hits = [ln.strip() for ln in lines if re.search(_GDPR_KWS, ln, flags=re.I)]
    # dedup semplice preservando ordine
    seen, out = set(), []
    for h in hits:
        k = h.lower()
        if k not in seen:
            out.append(h)
            seen.add(k)
        if len(out) >= max_lines:
            break
    return "\n".join(out)


# --- token-aware chunking ---
def _approx_tokens(s: str) -> int:
    return max(1, len(s) // 4)

def _chunk_by_tokens(text: str, max_tokens=350, overlap_tokens=60, min_tokens=200):
    if not text: return []
    max_c, ovl_c = max_tokens * 4, overlap_tokens * 4
    out, i, N = [], 0, len(text)
    while i < N:
        j = min(N, i + max_c)
        k = j
        while k > i + int(0.6 * max_c) and k < N and text[k-1] not in ".!?":
            k -= 1
        if k <= i + int(0.6 * max_c): k = j
        chunk = text[i:k].strip()
        if chunk: out.append(chunk)
        i += max(1, (len(chunk) * 4 - ovl_c) // 4)
    merged, buf = [], ""
    for ch in out:
        if _approx_tokens(ch) < min_tokens: buf = (buf + "\n" + ch).strip()
        else:
            if buf: merged.append(buf); buf = ""
            merged.append(ch)
    if buf: merged.append(buf)
    return merged

def _dedup_list(xs: List[str]) -> List[str]:
    seen, out = set(), []
    for x in xs:
        k = (x or "").strip()
        if k and k not in seen: out.append(k); seen.add(k)
    return out

def _norm_source(x: str) -> str:
    s = (x or "").strip().lower().replace(" ", "_")
    if "gdpr" in s: return "gdpr"
    if "ai" in s and "act" in s: return "ai_act"
    return "gdpr"

def handle(payload: Dict[str, Any]) -> Dict[str, Any]:
    assert payload.get("mode") == "document", "DocAnalyzer expects mode=document"
    doc_path = payload.get("document_path")
    assert doc_path and Path(doc_path).exists(), f"Document not found: {doc_path}"

    # 1) Carica + chunking token-aware (cap ~16k)
    pages = load_file_text(doc_path)
    full_text = "\n\n".join((p.get("text") or "") for p in pages)
    chunks = _chunk_by_tokens(full_text, CHUNK_MAX_TOKENS, CHUNK_OVERLAP_TOKENS, CHUNK_MIN_TOKENS)
    signals_gdpr = _extract_gdpr_signals(full_text, max_lines=20)

    # precedence ai segnali GDPR, poi il resto
    user_text = (signals_gdpr + "\n\n" + "\n\n".join(chunks))[:USER_TEXT_CAP]

    # 2) Retrieval separato con query-expansion e quota 50/50
    top_k = int(payload.get("top_k", TOP_K_DEFAULT or 12))
    k_gdpr = max(1, top_k // 2)
    k_ai   = top_k - k_gdpr

    gdpr_query = (
        signals_gdpr + "\n\n" +
        "[GDPR focus: Arts 5,6,9,13,14,22,35; consent; lawful basis; transparency; minimization; profiling; automated decision; DPIA]"
    )
    ai_query = (
        user_text + "\n\n" +
        "[AI Act focus: Art.5 prohibited; Art.10 data & governance; Art.13 transparency; Art.14 oversight; Art.15 robustness; Annex III]"
    )

    chunks_gdpr = retrieve_law_chunks(gdpr_query, ["gdpr"],   top_k=k_gdpr)
    chunks_ai   = retrieve_law_chunks(ai_query,   ["ai_act"], top_k=k_ai)
    lawchunks = chunks_gdpr + chunks_ai

    # 3) Prompt duale con obbligo GDPR
    prompt_gdpr = build_prompt(
        "MANDATORY: Evaluate GDPR applicability to this corporate AI policy. "
        "Identify gaps vs Arts 5,6,9,13,14,22,35 even if 'personal data' is not explicitly mentioned. "
        "Cite only GDPR. Do not discuss the AI Act.\n\n" + user_text,
        chunks_gdpr
    )
    prompt_ai = build_prompt(
        "MANDATORY: Evaluate ONLY the EU AI Act requirements for this policy. Cite only the AI Act.\n\n" + user_text,
        chunks_ai
    )


    # 3) Prompt duale
    prompt_gdpr = build_prompt("FOCUS: Evaluate GDPR only.\n\n" + user_text, chunks_gdpr)
    prompt_ai   = build_prompt("FOCUS: Evaluate AI Act only.\n\n" + user_text, chunks_ai)

    raw_gdpr = legal_analyze_with_gpt(prompt_gdpr, chunks_gdpr, temperature=0.0, seed=42)
    raw_ai   = legal_analyze_with_gpt(prompt_ai,   chunks_ai,   temperature=0.0, seed=43)

    # 4) Merge deterministico
    violations: List[Dict[str, Any]] = []
    for v in (raw_gdpr.get("violations") or []):
        vv = dict(v); vv["law"] = "GDPR"; violations.append(vv)
    for v in (raw_ai.get("violations") or []):
        vv = dict(v); vv["law"] = "AI Act"; violations.append(vv)

    recs  = _dedup_list((raw_gdpr.get("recommendations") or []) + (raw_ai.get("recommendations") or []))
    cites = (raw_gdpr.get("citations") or []) + (raw_ai.get("citations") or [])
    risk_score = max(int(raw_gdpr.get("risk_score", 0) or 0), int(raw_ai.get("risk_score", 0) or 0))

    cov = [
        {"law": "GDPR",   "status": "found" if any(v.get("law")=="GDPR"   for v in violations) else "not_found", "notes": ""},
        {"law": "AI Act", "status": "found" if any(v.get("law")=="AI Act" for v in violations) else "not_found", "notes": ""},
    ]

    merged = {
        "risk_score": risk_score,
        "violations": violations,
        "recommendations": recs,
        "citations": cites,
        "law_coverage": cov,
        "meta": {"top_k": top_k, "policies": ["gdpr","ai_act"], "pages": len(pages)},
    }

    # 5) Post-process finale
    return normalize_contract(merged, evidences=lawchunks)
