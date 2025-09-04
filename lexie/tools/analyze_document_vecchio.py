# tools/analyze_document.py
from __future__ import annotations
from typing import Dict, Any, List
from pathlib import Path
from ..loaders import load_file_text
from ..retriever import retrieve_law_chunks
from ..legal_analyzer_gpt import legal_analyze_with_gpt, build_prompt
from .postprocess import normalize_contract
from ..config import POLICIES as DEFAULT_POLICIES, TOP_K as TOP_K_DEFAULT
try:
    from ..config import MAX_EVIDENCE_CHARS
except Exception:
    MAX_EVIDENCE_CHARS = 1000

# --- token-aware chunking ---
def _approx_tokens(s: str) -> int:
    return max(1, len(s) // 4)  # ≈ 4 char/token

def _chunk_by_tokens(text: str, max_tokens=350, overlap_tokens=60, min_tokens=200):
    if not text:
        return []
    max_c = max_tokens * 4
    ovl_c = overlap_tokens * 4

    out, i, N = [], 0, len(text)
    while i < N:
        j = min(N, i + max_c)
        k = j
        # prova a chiudere su fine frase
        while k > i + int(0.6 * max_c) and k < N and text[k - 1] not in ".!?":
            k -= 1
        if k <= i + int(0.6 * max_c):
            k = j
        chunk = text[i:k].strip()
        if chunk:
            out.append(chunk)
        # avanzamento con overlap
        adv = max(1, (len(chunk) * 4 - ovl_c) // 4)
        i += adv

    # merge pezzi troppo piccoli
    merged, buf = [], ""
    for ch in out:
        if _approx_tokens(ch) < min_tokens:
            buf = (buf + "\n" + ch).strip()
        else:
            if buf:
                merged.append(buf); buf = ""
            merged.append(ch)
    if buf:
        merged.append(buf)
    return merged


def _dedup_list(xs: List[str]) -> List[str]:
    seen = set(); out = []
    for x in xs:
        k = (x or "").strip()
        if k and k not in seen:
            out.append(k); seen.add(k)
    return out


def handle(payload: Dict[str, Any]) -> Dict[str, Any]:
    assert payload.get("mode") == "document", "DocAnalyzer expects mode=document"
    doc_path = payload.get("document_path")
    assert doc_path and Path(doc_path).exists(), f"Document not found: {doc_path}"

    # 1) Carica testo (cap a 12k per prompt safety)
    pages = load_file_text(doc_path)  # list[{"page":int,"text":str}]
    full_text = "\n\n".join((p.get("text") or "") for p in pages)
    _chunks = _chunk_by_tokens(full_text, max_tokens=350, overlap_tokens=60, min_tokens=200)
    user_text = full_text[:12000]

    # 2) Retrieval separato e bilanciato
    top_k = int(payload.get("top_k", 12))
    k_ai = max(1, top_k // 2)
    k_gdpr = top_k - k_ai

    chunks_ai   = retrieve_law_chunks(user_text, ["ai_act"], top_k=k_ai)
    chunks_gdpr = retrieve_law_chunks(user_text, ["gdpr"],   top_k=k_gdpr)

    # 3) Normalizza source evidences (gdpr | ai_act)
    def _norm_source(x: str) -> str:
        s = (x or "").strip().lower().replace(" ", "_")
        if "gdpr" in s: return "gdpr"
        if "ai" in s and "act" in s: return "ai_act"
        return s or "gdpr"
    for ch in chunks_ai + chunks_gdpr:
        ch["source"] = _norm_source(ch.get("source", "gdpr"))

    # 4) Prompt duale: una run focalizzata GDPR, una AI Act
    prompt_gdpr = build_prompt("FOCUS: Evaluate GDPR only.\n\n" + user_text, chunks_gdpr)
    prompt_ai   = build_prompt("FOCUS: Evaluate AI Act only.\n\n" + user_text, chunks_ai)

    raw_gdpr = legal_analyze_with_gpt(prompt_gdpr, chunks_gdpr, temperature=0.0, seed=42)
    raw_ai   = legal_analyze_with_gpt(prompt_ai,   chunks_ai,   temperature=0.0, seed=43)

    # 5) Merge deterministico
    violations: List[Dict[str, Any]] = []
    for v in (raw_gdpr.get("violations") or []):
        vv = dict(v); vv["law"] = "GDPR"; violations.append(vv)
    for v in (raw_ai.get("violations") or []):
        vv = dict(v); vv["law"] = "AI Act"; violations.append(vv)

    # recommendations: unione de-duplicata
    recs = _dedup_list((raw_gdpr.get("recommendations") or []) + (raw_ai.get("recommendations") or []))

    # citations: concatena (il postprocess ridurrà e riallineerà)
    cites = (raw_gdpr.get("citations") or []) + (raw_ai.get("citations") or [])

    # risk: prendi il massimo (conservativo)
    try:
        rg = int(raw_gdpr.get("risk_score", 0))
    except Exception:
        rg = 0
    try:
        ra = int(raw_ai.get("risk_score", 0))
    except Exception:
        ra = 0
    risk_score = max(rg, ra)

    # coverage semplice: found se c'è almeno una violazione
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
        "meta": {
            "top_k": top_k,
            "policies": ["gdpr", "ai_act"],
            "pages": len(pages),
        },
    }

    # 6) Post-process finale: correzioni articoli/titoli, citations coerenti, eventuale placeholder AI
    evidences = chunks_gdpr + chunks_ai
    return normalize_contract(merged, evidences=evidences)

