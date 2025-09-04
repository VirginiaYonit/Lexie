import os
import json
from typing import List, Dict

try:
    from openai import OpenAI
except Exception:
    OpenAI = None

DEFAULT_MODEL = os.getenv("LEXIE_GPT_MODEL", "gpt-4o-mini")

SYSTEM_MSG = """
You are Lexie, a precise legal compliance assistant.
You MUST evaluate the USER_EVIDENCE against BOTH the EU GDPR AND the EU AI Act.
Use ONLY LAW_SNIPPETS as legal basis. If an article is not present in LAW_SNIPPETS, say "unknown".
Identify up to 3 distinct violations per law (GDPR and AI Act). Do not collapse them.
If fewer than 3 exist for a law, return only what is supported by LAW_SNIPPETS.
Every identified risk MUST be justified with a concrete 15–30 word QUOTE from the policy text and at least one citation referencing LAW_SNIPPETS.
Be concise, professional, explicit. Return ONLY valid JSON.
Ensure risk_score and risk_level are consistent (0–100 → low<33, medium<66, else high).
If minors are involved, explicitly assess GDPR Art. 8 conditions.
You MUST also report coverage for each law (found/not_found) with a one-line reason.
"""

def _format_evidence(evidences: List[Dict]) -> str:
    items = []
    for ev in evidences:
        cid = ev.get("id","")
        page = ev.get("page","")
        src = ev.get("source","")
        txt = ev.get("text","").replace("\n", " ").strip()
        items.append({"id": cid, "page": page, "source": src, "excerpt": txt[:1200]})
    return json.dumps(items, ensure_ascii=False)

def build_prompt(user_text: str, evidences: List[Dict]) -> str:
    return f'''
Evaluate the following POLICY TEXT against BOTH GDPR and AI Act using the LAW_SNIPPETS provided.

Return STRICT JSON with this schema:

{{
  "risk_score": int,
  "risk_level": "low"|"medium"|"high",
  "violations": [
    {{
      "law": "GDPR"|"AI Act",
      "article": "Art. X(…)"|"unknown",
      "title": "short title",
      "reason": "why this is a violation, grounded in LAW_SNIPPETS. Include QUOTE: \"...15–30 words from POLICY TEXT...\""
    }}
  ],
  "recommendations": ["short, actionable"],
  "citations": [
    {{
      "source": "gdpr"|"ai_act",
      "page": int,
      "id": "chunk id from LAW_SNIPPETS"
    }}
  ],
  "law_coverage": [
    {{"law":"GDPR","status":"found"|"not_found","notes":"one line justification"}},
    {{"law":"AI Act","status":"found"|"not_found","notes":"one line justification"}}
  ]
}}

CONSTRAINTS:
- Evaluate GDPR and AI Act separately.
- Return up to 3 violations for GDPR and up to 3 for AI Act (max 6 total).
- Each violation MUST include a 15–30 word QUOTE from POLICY TEXT and ≥1 citation from LAW_SNIPPETS.
- If a law has <3 supported violations, return only the supported ones and explain in law_coverage.
- Do NOT cite articles absent from LAW_SNIPPETS; use "unknown" instead.

POLICY TEXT:
{user_text}

LAW_SNIPPETS (JSON array of objects: id, page, source, excerpt):
{_format_evidence(evidences)}
'''

def legal_analyze_with_gpt(prompt: str, evidences: List[Dict], model: str = None, temperature: float = 0.0, seed: int = 42) -> Dict:
    model = model or DEFAULT_MODEL
    if OpenAI is None:
        raise RuntimeError("OpenAI library not available. Run: pip install openai")

    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        raise RuntimeError("Missing OPENAI_API_KEY in environment. Set it before running.")

    client = OpenAI(api_key=api_key)

    # prompt è già stato costruito prima, non serve rebuild
    resp = client.chat.completions.create(
        model=model,
        messages=[
            {"role": "system", "content": SYSTEM_MSG},
            {"role": "user", "content": prompt},
        ],
        temperature=temperature,
        seed=seed,
    )
    content = resp.choices[0].message.content.strip()

    try:
        data = json.loads(content)
    except Exception as e:
        start = content.find("{")
        end = content.rfind("}")
        if start != -1 and end != -1 and end > start:
            data = json.loads(content[start:end+1])
        else:
            raise RuntimeError(f"Model did not return JSON. Raw:\n{content}") from e

    data.setdefault("risk_score", 0)
    data.setdefault("risk_level", "low")
    data.setdefault("violations", [])
    data.setdefault("recommendations", [])
    data.setdefault("citations", [])
    
    s = int(data.get("risk_score", 0))
    def level(x): 
        return "low" if x < 33 else ("medium" if x < 66 else "high")
    data["risk_level"] = level(s)

    return data
