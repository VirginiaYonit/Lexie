# call_agent.py
import json, time, uuid
from .config import TOP_K, POLICIES, LOG_DIR, OUTPUT_DIR, level_from_score
from .tools.analyze_document import handle as analyze_document
from .tools.analyze_free_text import handle as analyze_free_text
from .pdf_reporter import generate_report

def route(payload: dict, generate_pdf: bool = False) -> dict:
    mode = (payload.get("mode") or "").lower()
    if mode not in {"document", "free_text"}:
        raise ValueError("payload.mode must be 'document' or 'free_text'")

    policies = payload.get("policies") or POLICIES
    top_k = int(payload.get("top_k") or TOP_K)

    if mode == "document":
        if not payload.get("document_path"):
            raise ValueError("document mode requires payload.document_path")
        result = analyze_document(payload)
        if not isinstance(result, dict):
            raise RuntimeError("analyze_document returned non-dict/None")
    else:
        if not payload.get("user_text"):
            raise ValueError("free_text mode requires payload.user_text")
        result = analyze_free_text(payload)
        if not isinstance(result, dict):
            raise RuntimeError("analyze_free_text returned non-dict/None")

    score = int(result.get("risk_score", 0))
    result["risk_level"] = level_from_score(score)

    ts = time.strftime("%Y%m%d-%H%M%S")
    result.setdefault("_meta", {"timestamp": ts, "mode": mode, "policies": policies, "top_k": top_k})

    log_path = LOG_DIR / f"lexie_{ts}_{uuid.uuid4().hex[:6]}.json"
    with open(log_path, "w", encoding="utf-8") as f:
        json.dump(result, f, ensure_ascii=False, indent=2)

    if generate_pdf:
        out_path = OUTPUT_DIR / f"report_{ts}.pdf"
        generate_report(result, str(out_path))
        result["_meta"]["pdf"] = str(out_path)

    return result
