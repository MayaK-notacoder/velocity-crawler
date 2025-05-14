"""
Async crawler for “content-velocity” signals.

• Visits up to 400 pages within the same domain (root + 3 levels deep)
• Counts PDFs and HTML5-style flipbooks
• Detects tool strings (Ceros, Turtl, Uberflip, Issuu, Storyblok) in URLs
• Flags a partner / reseller portal if link path matches /partners, /resellers, /channel
• Returns sample links (first 5 of each list)
"""

import asyncio, re, aiohttp
from urllib.parse import urljoin, urlparse
from bs4 import BeautifulSoup

TOOL_PATTERNS = re.compile(r"(ceros|turtl|uberflip|issuu|storyblok)", re.I)
HTML5_HINTS   = re.compile(r"(/story/|/flipbook/|pubhtml5|/view/)", re.I)

async def _fetch(session, url, timeout=10):
    try:
        async with session.get(url, timeout=timeout) as r:
            if "text/html" in r.headers.get("content-type", ""):
                return await r.text()
    except Exception:
        pass
    return ""

async def crawl(root: str, max_pages: int = 400, depth: int = 4):
    root   = root.rstrip("/")
    domain = urlparse(root).netloc
    seen   = set([root])
    queue  = [root]

    pdfs, html5, tools = [], [], set()
    partner_portal = False
    current_depth = 0

    async with aiohttp.ClientSession() as session:
        while queue and len(seen) < max_pages and current_depth <= depth:
            next_queue = []
            for url in queue:
                html = await _fetch(session, url)
                if not html:
                    continue

                soup = BeautifulSoup(html, "html.parser")
                for a in soup.find_all("a", href=True):
                    href = a["href"].split("#")[0]

                    # normalise
                    if href.startswith("//"):
                        href = "https:" + href
                    if href.startswith("/"):
                        href = urljoin(root, href)

                    # stay within root domain or its sub-domains
                    if domain not in urlparse(href).netloc:
                        continue
                    if href in seen:
                        continue

                    # classify
                    if href.endswith(".pdf"):
                        pdfs.append(href)
                    elif HTML5_HINTS.search(href):
                        html5.append(href)

                    tool_match = TOOL_PATTERNS.search(href)
                    if tool_match:
                        tools.add(tool_match.group(1).lower())

                    if re.search(r"/partners|/resellers|/channel", href, re.I):
                        partner_portal = True

                    # queue internal HTML links
                    if not href.endswith((".pdf", ".zip", ".doc", ".docx")):
                        next_queue.append(href)

                    seen.add(href)

            queue = next_queue
            current_depth += 1

    return {
        "pdf_count":        len(pdfs),
        "html5_like_count": len(html5),
        "tools_detected":   sorted(tools),
        "partner_portal":   partner_portal,
        "sample_pdfs":      pdfs[:5],
        "sample_html5":     html5[:5]
    }
