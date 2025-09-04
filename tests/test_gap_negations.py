from pathlib import Path
from helpers.run_cli import run_main_and_get_pdf
from helpers.pdf_extract import extract_text_from_pdf, normalize_text

ROOT = Path(__file__).resolve().parents[1]

def test_free_text_negation_biometric():
    pdf_path = run_main_and_get_pdf(
        "free-text",
        "We do not collect biometric data from our users.",
        cwd=ROOT
    )
    t = normalize_text(extract_text_from_pdf(pdf_path))

    # non deve comparire violazione biometric/AI
    assert "biometric" not in t, "Biometric violation should not appear due to negation"
    assert "no explicit violations detected" in t or "violations (0)" in t.lower()

def test_free_text_biometric_positive():
    pdf_path = run_main_and_get_pdf(
        "free-text",
        "We collect biometric data from our users for identification purposes.",
        cwd=ROOT
    )
    t = normalize_text(extract_text_from_pdf(pdf_path))

    # deve comparire almeno una violazione con riferimento a biometric/AI
    assert "biometric" in t or "ai act" in t or "gdpr" in t, \
        "Expected a biometric violation to appear in the PDF"
    assert "violations" in t and "no explicit violations" not in t, \
        "Violations section should not be empty"
