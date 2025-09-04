from pathlib import Path
from helpers.run_cli import run_main_and_get_pdf
from helpers.pdf_extract import extract_text_from_pdf, normalize_text

ROOT = Path(__file__).resolve().parents[1]

def test_free_text_smoke():
    pdf_path = run_main_and_get_pdf(
        "free-text",
        "We collect facial images without consent.",
        cwd=ROOT
    )
    t = normalize_text(extract_text_from_pdf(pdf_path))

    # intestazione rischio/punteggio
    assert "risk:" in t and "score:" in t

    # sezioni chiave effettive
    for must in ["violations", "recommendations", "citations"]:
        assert must in t, f"Sezione mancante: {must}"
