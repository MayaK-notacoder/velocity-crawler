import io, requests, pdfminer.high_level as ph

def extract_first_page_text(url, byte_limit=2_000_000):
    """
    Downloads the first ~2 MB of a PDF and returns the text of page 1.
    If the PDF is image-only, returns an empty string.
    """
    try:
        raw = requests.get(url, timeout=10).content[:byte_limit]
        text = ph.extract_text(io.BytesIO(raw), maxpages=1) or ""
        return text.strip()
    except Exception:
        return ""   # any error → blank text
