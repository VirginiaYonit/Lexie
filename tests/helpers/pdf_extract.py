from pathlib import Path
import re

def extract_text_from_pdf(pdf_path: Path) -> str:
    # Usa pdfminer.six (dipendenza test)
    from pdfminer.high_level import extract_text
    return extract_text(str(pdf_path))

def normalize_text(s: str) -> str:
    import re
    s = s.lower()
    s = re.sub(r"\s+", " ", s)

    # rimuovi timestamp/versioni
    s = re.sub(r"(generated at|timestamp).*?", "", s)
    s = re.sub(r"version[:\s]\S+", "version x", s)

    # normalizza quotes (contenuto molto variabile)
    s = re.sub(r'quote:\s*".*?"', 'quote:"<q>"', s)

    # normalizza header rischio/punteggio (numeri fluttuano poco)
    s = re.sub(r"risk:\s*(low|medium|high)", r"risk:\1", s)
    s = re.sub(r"score:\s*\d+\/100", "score:xx/100", s)

    # tollera conteggio tra parentesi (violations (N))
    s = re.sub(r"(violations\s*)\(\d+\)", r"\1(x)", s)
    s = re.sub(r"(recommendations\s*)\(\d+\)", r"\1(x)", s)
    s = re.sub(r"(citations\s*)\(\d+\)", r"\1(x)", s)

    return s.strip()
