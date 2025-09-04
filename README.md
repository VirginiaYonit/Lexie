# Lexie — MVP Compliance Copilot

An Agentic AI assistant to assess GDPR and AI Act compliance

Lexie analyzes policy documents (PDF) or free text and compares them to key articles in the GDPR and EU AI Act. It returns a downloadable human-readable PDF report with risk score, violations, citations, and recommendations.

---

## 🚀 Try it out

You can try Lexie directly on Hugging Face Spaces:

👉 [Lexie — Compliance Copilot (Demo)](https://huggingface.co/spaces/virginialevy/Lexie)

Upload a policy or paste free text. Lexie returns:
- Risk score (0–100)
- Violations table
- PDF report

---

## Requirements

- Python 3.10+
- Valid OPENAI_API_KEY

---

## Installation

python -m venv .venv
source .venv/bin/activate    # Windows: .venv\Scripts\activate
pip install -r requirements.txt

## Environment variable

(macOS/Linux)
export OPENAI_API_KEY="sk-..."
(Windows PowerShell)
setx OPENAI_API_KEY "sk-..."

## ▶️ Run locally

python app.py

On startup Lexie will create:
runtime/
  logs/
  outputs/

## 💻 Usage

- Upload a PDF (≤ 10 MB) or paste free text.
- Policies are pre-selected: ["gdpr", "ai_act"].
- Click Analyze.
- The UI displays a risk badge, a violations table, and a download link for the generated PDF.
 
Lexie performs retrieval + analysis + PDF generation.

---

## 🤖 Deploy on Hugging Face Spaces

To deploy your own Lexie instance:

- Create a Gradio Space
- Push: app.py, lexie/, requirements.txt
- Add OPENAI_API_KEY under Settings → Secrets
- Use CPU Basic — no torch required.

---

## 📂 Project structure

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

---

## 🧠 Design Principles

Lexie is built using agentic, modular design:

🔹 Context-first prompting like briefing a junior dev
🔹 Rule-based logic via config.py and postprocess modules
🔹 Validation-driven output: predictable, auditable results
🔹 Model mixing: MiniLM for chunking, GPT-4 for reasoning
🔹 Human-in-the-loop: tested and refined with real feedback

Lexie isn’t just a wrapper,  it's a working assistant designed for clarity, traceability, and real compliance use cases.

---

## 👥 Collaborative Development

Lexie was co-developed with ChatGPT (GPT-4 & GPT-5) as a design partner, not just a coding assistant.
From architecture to debugging, AI served as a thought companion. Every step was:

- Reviewed manually
- Integrated intentionally
- Documented clearly

This is human-in-the-loop AI applied seriously.

---

## 🧪 Testing

Lexie includes a full test suite to ensure:

- Functional stability
- Snapshot consistency
- Clear regression detection

Install test dependencies:

pip install -r requirements-dev.txt

Run all tests:

pytest tests/ -q

---

## Test Types

| Type           | Purpose                                      |
| -------------- | -------------------------------------------- |
| Snapshot tests | Compare new PDF output to golden reference   | 
| Smoke tests    | Ensure basic structure (risk, sections, etc) | 
| Unit tests     | Validate rule enforcement and structure      | 

Lexie includes fixtures, golden snapshots, and CLI test helpers.

📎 Lexie Pipeline Overview:

route → retrieve → analyze → postprocess → pdf_reporter
            │                        │
       (document)              (free text)

---

## 🧭 Acceptance Criteria

- PDF reports in runtime/outputs/*.pdf
- Matching violations ↔ citations
- Graceful handling of:
  - Corrupted PDFs
  - Empty input
  - Slow performance with long docs

---

## 📜 AI Responsible Use Policy

System: Lexie – Compliance Copilot
Version: 1.0
Date: September 4, 2025
Next review: September 2026
AI System Owner: Virginia Levy Abulafia

---

## 🎯 Purpose

Lexie is an Agentic AI system designed to support the analysis of policy documents and free text related to AI governance.
It compares input against key articles of the GDPR and the EU AI Act, returning:

- a human-readable PDF report (risk score, violations, citations, recommendations)

- 🛑 No machine-readable log is stored: JSON outputs have been removed to avoid retaining sensitive information.

Lexie does not make autonomous decisions. It requires textual input and assumes human oversight for all interpretations and uses of its outputs.

---

## 🌱 Guiding Principles

### Transparency
All compliance logic is defined in human-readable Markdown files. Outputs follow a strict, verifiable JSON schema. Users are clearly informed about scope and limitations.

### Mandatory Human Oversight
Lexie does not replace compliance officers. Reports must be reviewed and validated by authorized staff. No decisions are applied automatically.

### Data Minimization
It does not retain, log, or store any JSON output. Reports are returned as downloadable PDFs only.

### Content Neutrality
Lexie analyzes technical and organizational compliance. It never generates discriminatory, sensitive, or legally binding content.
It is not suitable for medical, legal, or other critical data contexts.

### Proportionate Responsibility
The system guarantees technical operation within declared limits. The owner is not liable for misuse or misinterpretation of reports.

### Continuous Improvement
Lexie is periodically reviewed. All updates to compliance logic or system features will be documented transparently.

---

## 📌 Organizational Commitments

The system owner commits to:

- Operate in alignment with ISO/IEC 42001:2023, the EU AI Act, and the GDPR
- Document risk and impact assessments
- Release only tested, traceable versions
- Inform users about system scope and limitations
- Integrate user feedback into continuous improvement

---

## ✍️ Approval

This Responsible Use Policy was approved on September 4, 2025
It will be reviewed within 12 months.

AI System Owner: Virginia Levy Abulafia
Signature: Digital or equivalent

---


💡 **Ready to explore AI compliance you can trust and see how micro-AI agents could support your business?**

🚀 Try Lexie now:
👉 [Live Demo on Hugging Face](https://huggingface.co/spaces/virginialevy/Lexie)
