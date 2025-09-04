# test_pdf_snapshot.py
from pathlib import Path
from helpers.run_cli import run_main_and_get_pdf
from helpers.pdf_extract import extract_text_from_pdf, normalize_text

ROOT = Path(__file__).resolve().parents[1]

def test_iubenda_snapshot(tmp_path):
    fixtures = ROOT / "tests" / "fixtures"
    src = fixtures / "iubenda.pdf"

    # esegue: python main.py document "<file>"
    pdf_path = run_main_and_get_pdf("document", str(src), cwd=ROOT)

    got = normalize_text(extract_text_from_pdf(pdf_path))
    golden = fixtures / "iubenda_snapshot.normalized.txt"
    if not golden.exists():
        golden.write_text(got, encoding="utf-8")  # prima run: crea golden
    exp = golden.read_text(encoding="utf-8")
    assert got == exp, "PDF snapshot mismatch. Aggiorna il golden solo se il cambiamento è voluto."

def test_smoke_pdf_has_sections():
    fixtures = ROOT / "tests" / "fixtures"
    src = fixtures / "info_breve.pdf"
    pdf_path = run_main_and_get_pdf("document", str(src), cwd=ROOT)
    t = normalize_text(extract_text_from_pdf(pdf_path))

    # intestazione rischio/punteggio
    assert "risk:" in t and "score:" in t, "Manca intestazione rischio/punteggio"

    # sezioni chiave effettive
    for must in ["violations", "recommendations", "citations"]:
        assert must in t, f"Sezione mancante: {must}"
