# tools/postprocess.py
from __future__ import annotations
from typing import Dict, Any, List
import re

# -----------------------------
# Switch di comportamento
# -----------------------------
ENABLE_AI_PLACEHOLDER = False  # lasciamo disattivo

# -----------------------------
# Utilità base
# -----------------------------
def _level(x: int) -> str:
    return "low" if x < 33 else ("medium" if x < 66 else "high")

_ART_NUM = re.compile(r"art\.?\s*(\d+)", re.I)

def _norm_src(s: str) -> str:
    s = (s or "").lower().replace(" ", "_")
    if "gdpr" in s: return "gdpr"
    if "ai" in s and "act" in s: return "ai_act"
    return s or "gdpr"

# -----------------------------
# Mappe GDPR ufficiali
# -----------------------------
GDPR_TITLES = {
    "Art. 5":  "Principles relating to processing",
    "Art. 6":  "Lawfulness of processing",
    "Art. 8":  "Conditions applicable to child's consent",
    "Art. 9":  "Processing of special categories of personal data",
    "Art. 13": "Information to be provided where personal data are collected",
    "Art. 14": "Information to be provided where personal data have not been obtained",
    "Art. 15": "Right of access by the data subject",
    "Art. 24": "Responsibility of the controller",
    "Art. 25": "Data protection by design and by default",
    "Art. 30": "Records of processing activities",
    "Art. 32": "Security of processing",
    "Art. 35": "Data protection impact assessment",
    "Art. 44": "General principle for transfers",
    "Art. 45": "Transfers on the basis of an adequacy decision",
    "Art. 46": "Transfers subject to appropriate safeguards",
    "Art. 49": "Derogations for specific situations",
}
def _norm_title(t: str) -> str:
    return (t or "").strip().lower().replace("’","'")

GDPR_TITLE2ART = { _norm_title(v): k for k, v in GDPR_TITLES.items() }

# -----------------------------
# Heuristics AI Act (keyphrase → articolo/titolo)
# -----------------------------
AI_KEYMAP = [
    ("risk management",  "Art. 9",  "Risk management system"),
    ("data governance",  "Art. 10", "Data and data governance"),
    ("human oversight",  "Art. 14", "Human oversight"),
    ("transparency",     "Art. 13", "Transparency and information to users"),
    ("conformity",       "Art. 43", "Conformity assessment"),
]

def _is_ai_act(law: str) -> bool:
    return (law or "").lower().replace(" ", "_") in ("ai_act", "aiact")

def _mk_cite(e: Dict[str, Any]) -> Dict[str, Any]:
    return {"source": _norm_src(e.get("source","gdpr")), "page": e.get("page","?"), "id": e.get("id","")}

# =============================================================================
# Postprocess principale
# =============================================================================
def normalize_contract(data: Dict[str, Any], evidences: List[Dict] = None) -> Dict[str, Any]:
    """
    Finalizza l'output:
      - Mantiene le violations come fonte primaria.
      - Corregge coerenza articoli/titoli (GDPR) e 'unknown' (AI Act) con euristiche.
      - Costruisce CITATIONS 1:1 con le violations (1 ref per violazione).
      - Nessuna deduplicazione: il conteggio coincide sempre con le violazioni.
    """
    data = dict(data or {})

    # --- Risk ---
    try:
        rs = int(data.get("risk_score", 0))
    except Exception:
        rs = 0
    data["risk_score"] = rs
    data["risk_level"] = _level(rs)

    # --- Violations / Recommendations ---
    viols: List[Dict[str, Any]] = list(data.get("violations") or [])
    data["violations"] = viols
    recos: List[str] = list(data.get("recommendations") or [])
    data["recommendations"] = recos

    evs = list(evidences or [])

    # (1) Correzioni strutturali minime
    for v in viols:
        law = (v.get("law") or "").strip()
        art_raw = str(v.get("article","")).strip()
        title   = str(v.get("title","")).strip()

        # GDPR: normalizza "Art. X" e titolo ufficiale, se possibile
        if law.upper() == "GDPR":
            m = _ART_NUM.search(art_raw)
            std_from_num = f"Art. {m.group(1)}" if m else None
            std_from_title = GDPR_TITLE2ART.get(_norm_title(title))
            if std_from_title:
                v["article"] = std_from_title
                v["title"]   = GDPR_TITLES.get(std_from_title, title)
            elif std_from_num:
                v["article"] = std_from_num
                v["title"]   = GDPR_TITLES.get(std_from_num, title)

        # AI Act: se 'unknown', prova a dedurre
        elif _is_ai_act(law):
            if art_raw.lower() in {"", "unknown", "art. ?", "?"}:
                blob = (v.get("reason","") + " " + title).lower()
                picked = None
                for key, art, t in AI_KEYMAP:
                    if key in blob:
                        picked = (art, t); break
                if not picked and evs:
                    ai_blob = " ".join(str(e.get("text","")).lower() for e in evs if _norm_src(e.get("source"))=="ai_act")
                    for key, art, t in AI_KEYMAP:
                        if key in ai_blob:
                            picked = (art, t); break
                if picked:
                    v["article"], v["title"] = picked

    # (2) Citations 1:1 con le violations
    pool = [_mk_cite(e) for e in evs] or [{"source":"gdpr","page":"?","id":""}]
    idx_all = 0
    idx_gdpr = 0
    idx_aia  = 0
    pool_gdpr = [p for p in pool if p["source"]=="gdpr"] or [{"source":"gdpr","page":"?","id":""}]
    pool_aia  = [p for p in pool if p["source"]=="ai_act"] or [{"source":"ai_act","page":"?","id":""}]

    def take(prefer: str|None):
        nonlocal idx_all, idx_gdpr, idx_aia
        if prefer == "gdpr":
            ref = pool_gdpr[idx_gdpr % len(pool_gdpr)]; idx_gdpr += 1; return dict(ref)
        if prefer == "ai_act":
            ref = pool_aia[idx_aia % len(pool_aia)];   idx_aia  += 1; return dict(ref)
        ref = pool[idx_all % len(pool)]; idx_all += 1; return dict(ref)

    per_violation: List[Dict[str, Any]] = []
    for v in viols:
        vc = (v.get("citations") or [])
        if vc:
            ct = {"source": _norm_src(vc[0].get("source","gdpr")),
                  "page":   vc[0].get("page","?"),
                  "id":     vc[0].get("id","")}
            per_violation.append(ct)
        else:
            law = (v.get("law") or "")
            prefer = "ai_act" if "ai" in law.lower() else ("gdpr" if "gdpr" in law.upper() else None)
            per_violation.append(take(prefer))

    for v, ct in zip(viols, per_violation):
        if not v.get("citations"):
            v["citations"] = [dict(ct)]

    data["citations"] = per_violation

    # (3) Placeholder AI Act (disattivo per default)
    if ENABLE_AI_PLACEHOLDER:
        has_ai_viol = any(_is_ai_act(v.get("law")) for v in viols)
        has_ai_cite = any(c.get("source")=="ai_act" for c in data.get("citations", []))
        has_ai_reco = any(("ai act" in r.lower() or "high-risk ai" in r.lower()) for r in recos)
        if (has_ai_cite or has_ai_reco) and not has_ai_viol:
            data["violations"].append({
                "law": "AI Act",
                "article": "Art. 9",
                "title": "Risk management system",
                "reason": (
                    "Placeholder added: citations/recommendations indicate AI Act relevance, "
                    "but the model did not return an explicit AI Act violation. "
                    "Review required to confirm applicability."
                )
            })
            data["citations"].append(take("ai_act"))

    return data

# -----------------------------
# Helper per coerenza GDPR
# -----------------------------
def _norm_art_key(x) -> str:
    s = str(x or "").lower()
    s = s.replace("art.", "").replace("art", "")
    s = re.sub(r"[^0-9]+", "", s)
    return s

def _gdpr_expected_title(art: str) -> str | None:
    if not isinstance(GDPR_TITLES, dict):
        return None
    want = _norm_art_key(art)
    for k, v in GDPR_TITLES.items():
        if _norm_art_key(k) == want:
            return v
    return None

# -----------------------------
# Negation detector (EN/IT)
# -----------------------------
NEGATION_WINDOW = 12  # ± parole di contesto
NEG_TOKENS = [
    r"\bno\b", r"\bnot\b", r"\bnever\b", r"\bwithout\b", r"\bdoes?\s+not\b",
    r"\bnon\b", r"\bmai\b", r"\bsenza\b", r"\bnon\s+viene(?:\s+mai)?\b",
]
THEME_KEYWORDS = {
    "biometric": [r"\bbiometric", r"\bface", r"\bfacial", r"\bimpronte", r"\bbiometr", r"\bvolto"],
    "profiling": [r"\bprofil", r"\bprofiling", r"\bprofilazione"],
    "retention": [r"\bretain", r"\bretention", r"\bconserva", r"\bconservazione"],
    "sharing_transfer": [r"\bshare", r"\btransfer", r"\btrasfer", r"\bcondivis"],
    "emotion": [r"\bemotion", r"\bemotional", r"\bemozion"],
}
def _tokenize_words(text: str) -> list[str]:
    return re.findall(r"\w+", text.lower(), flags=re.UNICODE)

def _has_negation_near(text: str, keywords: list[str], window: int = NEGATION_WINDOW) -> bool:
    neg_idxs = set()
    for m in re.finditer("|".join(NEG_TOKENS), text.lower()):
        neg_idxs.add(len(_tokenize_words(text[:m.start()])))

    key_idxs = set()
    for kw in keywords:
        for m in re.finditer(kw, text.lower()):
            key_idxs.add(len(_tokenize_words(text[:m.start()])))

    for ki in key_idxs:
        for ni in neg_idxs:
            if abs(ki - ni) <= window:
                return True
    return False

def _infer_theme(v: dict) -> str | None:
    t = (v.get("title") or "" + " " + v.get("reason", "") or "").lower()
    if any(re.search(p, t) for p in THEME_KEYWORDS["biometric"]): return "biometric"
    if any(re.search(p, t) for p in THEME_KEYWORDS["emotion"]): return "emotion"
    if any(re.search(p, t) for p in THEME_KEYWORDS["profiling"]): return "profiling"
    if any(re.search(p, t) for p in THEME_KEYWORDS["retention"]): return "retention"
    if any(re.search(p, t) for p in THEME_KEYWORDS["sharing_transfer"]): return "sharing_transfer"
    return None

def _covered_by_negation_in_evidence(user_evidence: str, theme: str) -> bool:
    if not user_evidence or theme not in THEME_KEYWORDS:
        return False
    return _has_negation_near(user_evidence, THEME_KEYWORDS[theme])

# -----------------------------
# Article guard-rails (auto-correct)
# -----------------------------
ARTICLE_MAP = {
    ("GDPR", "transfer"): "46",
    ("GDPR", "minors"): "8",
    ("GDPR", "security"): "32",
    ("GDPR", "records"): "30",
    ("GDPR", "design"): "25",
    ("GDPR", "access"): "15",
    ("AI ACT", "conformity"): "43",
    ("AI ACT", "transparency"): "13",
}
THEME_ALIASES = {
    "transfer": [
        "transfer","transfers","transfer outside eu","outside eu",
        "third country","third countries","extra-ue","extra ue",
        "trasfer","trasferimento","trasferimenti","paesi terzi","paese terzo"
    ],
    "minors": ["minor","minors","child","children","minori","under 16","under 13"],
    "security": ["security","sicurezza","integrity","breach"],
    "records": ["records","registro","registri","art.30","record of processing"],
    "design": ["by design","by default","art.25","default settings","privacy by design"],
    "access": ["access","right of access","art.15","accesso","diritto di accesso"],
    "conformity": ["conformity","assessment","valutazione conformità"],
    "transparency": ["transparency","inform","ai info","art.13","trasparenza","informazioni agli utenti"],
}
def _infer_theme_from_text(s: str) -> str | None:
    s = (s or "").lower()
    for theme, keys in THEME_ALIASES.items():
        if any(k in s for k in keys):
            return theme
    return None

# -----------------------------
# Adapter: regole extra + avvisi
# -----------------------------
def enforce_rules(data: Dict[str, Any], max_citations: int | None = None, warn_coherence: bool = True):
    """
    Applica normalize_contract e aggiunge:
      - flag negazioni (restano nel JSON, verranno esclusi dal PDF)
      - auto-correct articolo (transfer→46, conformity→43, transparency→13, …)
      - warnings non bloccanti su incoerenza titolo/articolo (GDPR)
      - cap opzionale sulle citations
    Ritorna: (data_out, warnings_list)
    """
    out = normalize_contract(data, evidences=data.get("evidences") or [])
    warnings: List[str] = []

    # A0) Negazioni (flag)
    ue = (data.get("user_text") or data.get("document_text") or "")
    for v in out.get("violations", []) or []:
        theme = _infer_theme(v)
        if theme and _covered_by_negation_in_evidence(ue, theme):
            v["covered_by_negation"] = True

    # A1) Article guard-rails (auto-correct) — deterministico, senza inferenza tema
    TRANSFER_PAT = re.compile(
        r"\btransfer(s)?\b|outside\s+eu|third\s+countr|extra[-\s]?ue|trasfer|trasferiment|paesi\s+terzi|paese\s+terzo",
        re.I,
    )

    for v in out.get("violations", []) or []:
        law = (v.get("law") or "").strip().upper()
        art_raw = str(v.get("article") or "").strip()
        blob = f"{v.get('title','')} {v.get('reason','')}".lower()

        # GDPR — Transfers → Art. 46
        if law == "GDPR" and TRANSFER_PAT.search(blob):
            if _norm_art_key(art_raw) != _norm_art_key("46"):
                v["autocorrected_from"] = art_raw
                v["article"] = "Art. 46"

        # AI Act — Conformity → Art. 43 (facoltativo, ma utile)
        if law == "AI ACT" and re.search(r"\bconformity\b|\bassessment\b|valutazione\s+conformit", blob):
            if _norm_art_key(art_raw) != _norm_art_key("43"):
                v["autocorrected_from"] = art_raw
                v["article"] = "Art. 43"


    # A2) Warning su incoerenza titolo/articolo GDPR (non blocca)
    if warn_coherence:
        for v in out.get("violations", []) or []:
            law = (v.get("law") or "").upper()
            art = v.get("article")
            tit = v.get("title") or ""
            if law == "GDPR" and art:
                expected = _gdpr_expected_title(art)
                if expected and _norm_title(tit) != _norm_title(expected):
                    warnings.append(
                        f"GDPR coherence warning: {art} expected '{expected}', got '{tit}'."
                    )

    # B) Cap opzionale sulle citations (non distruttivo)
    if isinstance(max_citations, int) and max_citations > 0:
        cits = out.get("citations") or []
        if len(cits) > max_citations:
            out["citations"] = cits[:max_citations]
            warnings.append(f"Citations capped to {max_citations} for stability.")

    return out, warnings
