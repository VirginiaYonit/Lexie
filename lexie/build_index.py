import os
import json
from .loaders import load_file_text

def build_policy_chunks(pdf_path, output_path):
    chunks = load_file_text(pdf_path)
    with open(output_path, "w", encoding="utf-8") as f:
        for i, chunk in enumerate(chunks):
            record = {
                "id": f"{os.path.basename(pdf_path)}::p{i+1}",
                "text": chunk["text"],
                "page": chunk["page"]
            }
            f.write(json.dumps(record) + "\n")
    print(f"✅ Wrote {len(chunks)} chunks to {output_path}")

if __name__ == "__main__":
    build_policy_chunks("lexie/policies/gdpr/gdpr.pdf", "lexie/policies/gdpr/chunks.jsonl")
    build_policy_chunks("lexie/policies/ai_act/ai_act.pdf", "lexie/policies/ai_act/chunks.jsonl")