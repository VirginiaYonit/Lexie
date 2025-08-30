# Lexie — MVP Compliance Copilot
An Agentic AI to verify compliance with GDPR and AI Act.

Lexie is an MVP AI assistant for compliance checks.
It analyzes free text or policy documents (PDF), compares them against GDPR and the AI Act, and outputs both a JSON log and a human-readable PDF report.

## 🚀 Try it out

You can try Lexie directly on Hugging Face Spaces:
👉 [Lexie — Compliance Copilot (Demo)](indirizzo)

Upload a PDF or paste free text, and Lexie will return a risk score, violations, and a downloadable PDF report.

## Requirements

- Python 3.10+
- Valid OPENAI_API_KEY

## Installation

python -m venv .venv
source .venv/bin/activate    # Windows: .venv\Scripts\activate
pip install -r requirements.txt

## Environment variable

(macOS/Linux)
export OPENAI_API_KEY="sk-..."
(Windows PowerShell)
setx OPENAI_API_KEY "sk-..."

## Run locally

python app.py

On startup Lexie will create:
runtime/
  logs/
  outputs/

## Usage

- Upload a PDF (≤ 10 MB) or paste free text.
- Policies are pre-selected: ["gdpr", "ai_act"].
- Click Analyze.
- The UI displays a risk badge, a violations table, and a download link for the generated PDF.
- 
Both JSON logs and PDFs are stored under runtime/.

## Deploy on Hugging Face Spaces
If you want to deploy your own instance on Hugging Face Spaces:

1. Create a Gradio Space.
2. Push this repo (app.py, lexie/, requirements.txt).
3. In Settings → Secrets, add OPENAI_API_KEY.
4. Hardware: CPU Basic is enough.
5. No torch required for the MVP.

## Project structure

lexie/
  main.py
  config.py
  loaders.py
  build_index.py
  retriever.py
  legal_analyzer_gpt.py
  pdf_reporter.py
  call_agent.py
  tools/
    analyze_document.py
    analyze_free_text.py
  policies/
    gdpr/ {gdpr.pdf, index.yml, chunks.jsonl}
    ai_act/ {ai_act.pdf, index.yml, chunks.jsonl}
runtime/
  logs/
  outputs/
app.py
requirements.txt
README.md

## Common errors

- **Missing OPENAI_API_KEY** → warning in UI.
- **Unreadable/corrupted PDF** → clear error message, no crash.
- **Empty input** → requires either text or PDF.
- **Slow performance with >100 pages** → reduce Top-K or run summary-only.

## Acceptance criteria

- JSON saved under runtime/logs/…json.
- PDF saved under runtime/outputs/…pdf.
- len(violations) == len(citations) in JSON.
- UI does not crash with corrupted PDFs or empty input.






