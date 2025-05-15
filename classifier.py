import re, requests, io
from pdfminer.high_level import extract_text

KEYWORDS = {
    "Case study":  r"(case\s*study|success\s*story)",
    "Datasheet":   r"(data\s*sheet|spec\s*sheet)",
    "White paper": r"(white\s*paper)",
    "Brochure":    r"(brochure|leaflet|flyer)",
    "E-book":      r"(ebook|e-book)"
}

def _guess(label_map, text):
    for label, pattern in label_map.items():
        if re.search(pattern, text, re.I):
            return label, 0.85
    return "Other", 0.3

def classify_pdf(url, byte_limit=2_000_000):
    # 1) filename guess
    kind, conf = _guess(KEYWORDS, url.split("/")[-1])
    if kind != "Other":
        return kind, conf

    # 2) peek at first page
    try:
        raw = requests.get(url, timeout=10).content[:byte_limit]
        text = extract_text(io.BytesIO(raw), maxpages=1)
        return _guess(KEYWORDS, text or "")
    except Exception:
        return "Unknown", 0.0
