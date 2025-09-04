import os
import json
import numpy as np
from sentence_transformers import SentenceTransformer, util
from pathlib import Path
POLICY_DIR = Path(__file__).parent / "policies"

# Carica il modello solo una volta
embedding_model = SentenceTransformer('all-MiniLM-L6-v2')

def cosine_similarity(a, b):
    return np.dot(a, b) / (np.linalg.norm(a) * np.linalg.norm(b))

def load_chunks(policy_name):
    path = POLICY_DIR / policy_name / "chunks.jsonl"  # <-- usa path corretto
    if not path.exists():
        print(f"❌ File not found: {path}")
        return []
    out = []
    with open(path, "r", encoding="utf-8") as f:
        for line in f:
            if not line.strip():
                continue
            raw = json.loads(line)
            # normalizzazione pagina
            page = raw.get("page") or raw.get("page_num") or raw.get("p")
            try:
                page = int(page) if page is not None else None
            except Exception:
                page = None
            out.append({
                "id": raw.get("id") or f"{policy_name}:{page if page is not None else '?'}",
                "text": raw.get("text") or raw.get("chunk") or "",
                "page": page,
                "source": policy_name,
            })
    return out

def retrieve_law_chunks(query_text, policy_list, top_k=5):
    results = []
    query_vec = embedding_model.encode(query_text)

    for policy in policy_list:
        chunks = load_chunks(policy)
        for chunk in chunks:
            chunk_vec = embedding_model.encode(chunk["text"])
            score = cosine_similarity(query_vec, chunk_vec)
            results.append({
                "id": chunk["id"],
                "text": chunk["text"],
                "page": chunk["page"],
                "score": score,
                "source": policy
            })

    results.sort(key=lambda x: x["score"], reverse=True)
    return results[:top_k]