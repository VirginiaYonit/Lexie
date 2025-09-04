# lexie/retriever.py — fallback first (no torch)
import json
from pathlib import Path
import numpy as np

# opzionale: embeddings se disponibili, altrimenti fallback
try:
    from sentence_transformers import SentenceTransformer
    _ST = SentenceTransformer("all-MiniLM-L6-v2")
except Exception:
    _ST = None

POLICY_DIR = Path(__file__).parent / "policies"

def load_chunks(policy_name: str):
    path = POLICY_DIR / policy_name / "chunks.jsonl"
    if not path.exists():
        print(f"❌ File not found: {path}")
        return []
    out = []
    with path.open("r", encoding="utf-8") as f:
        for line in f:
            if not line.strip():
                continue
            raw = json.loads(line)
            page = raw.get("page") or raw.get("page_num") or raw.get("p")
            try:
                page = int(page) if page is not None else None
            except Exception:
                page = None
            out.append({
                "id":   raw.get("id") or f"{policy_name}:{page if page is not None else '?'}",
                "text": raw.get("text") or raw.get("chunk") or "",
                "page": page,
                "source": policy_name,
            })
    return out
    
def retrieve_law_chunks(query_text: str, policy_list, top_k=8):
    scored_by_policy = {}
    for policy in policy_list:
        items = []
        for ch in load_chunks(policy):
            s = _score(query_text, ch["text"])
            items.append({**ch, "score": s})
        items.sort(key=lambda x: x["score"], reverse=True)
        scored_by_policy[policy] = items

    # quota per policy
    n_per = max(1, top_k // max(1, len(policy_list)))
    selected = []
    for p in policy_list:
        selected.extend(scored_by_policy.get(p, [])[:n_per])

    # fill remaining from global pool
    remaining = top_k - len(selected)
    if remaining > 0:
        pool = []
        for p in policy_list:
            pool.extend(scored_by_policy.get(p, [])[n_per:])
        pool.sort(key=lambda x: x["score"], reverse=True)
        selected.extend(pool[:remaining])

    return selected[:top_k]


def _score(a: str, b: str) -> float:
    if _ST is not None:
        va = _ST.encode(a)
        vb = _ST.encode(b)
        return float(np.dot(va, vb) / (np.linalg.norm(va) * np.linalg.norm(vb) + 1e-9))
    # fallback leggero: Jaccard su token
    A, B = set(a.lower().split()), set(b.lower().split())
    den = len(A | B) or 1
    return len(A & B) / den

