from pdfminer.high_level import extract_text
import re

_SPACES = re.compile(r"[ \t]+")
_NEWLINES = re.compile(r"\s*\n\s*")

def _clean_text(s: str) -> str:
    if not s:
        return ""
    s = s.replace("\u00ad","").replace("\u200b","").replace("\u200c","") \
         .replace("\u200d","").replace("\ufeff","").replace("\xa0"," ")
    s = re.sub(r"(\w)-\n(\w)", r"\1\2", s)      # mini-\nmization -> minimization
    s = _SPACES.sub(" ", s)
    s = _NEWLINES.sub("\n", s)
    return s.strip()

def load_file_text(file_path):
    try:
        text = extract_text(file_path)
        pages = text.split("\f")
        out = []
        for i, pg in enumerate(pages):
            pg = _clean_text(pg)
            if pg:
                out.append({"page": i+1, "text": pg})
        return out
    except Exception as e:
        print(f"❌ Failed to load PDF: {e}")
        return []
