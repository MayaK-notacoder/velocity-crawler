"""
Content-Velocity crawler for Foleon.

Visits up to `max_pages` pages within `depth` link levels and returns:
    • pdf_count              – how many .pdf links found
    • html5_like_count       – flipbook/HTML5 asset hints
    • tools_detected         – ['ceros', 'turtl', ...] in URLs
    • partner_portal         – True if /partners|/resellers|/channel path found
    • sample_pdfs            – first 5 PDF links
    • sample_html5           – first 5 HTML5 links
"""

import asyncio, re, aiohttp
from urllib.parse import urljoin, urlparse
from bs4 import BeautifulSoup

TOOL_PATTERNS = re.compile(r"(ceros|turtl|uberflip|issuu|storyblok)", re.I)
HTML5_HINTS   = re.compile(r"(/story/|/flipbook/|pubhtml5|/view/)", re.I)
PDF_REGEX     = re.compile(r"\.pdf($|\?)", re.I)     # case-insensitive, allows query

async def _fetch(session, url, timeout=10):
    try:
        async with session.get(url, timeout=timeout) as r:
            if "text/html" in r.headers.get("content-type", ""):
                return await r.text()
    except Exception:
        pass
    return ""

async def crawl(root: str, max_pages:int = 150, depth:int = 3):
    root   = root.rstrip("/")
    domain = urlparse(root).netloc
    seen   = {root}
    queue  = [root]

    pdfs, html5, tools = [], [], set()
    partner_portal = False
    current_depth  = 0

    async with aiohttp.ClientSession() as session:
        while queue and len(seen) < max_pages and current_depth <= depth:
            next_queue = []

            # fetch all URLs in this level concurrently
            html_pages = await asyncio.gather(*[_fetch(session, u) for u in queue])

            for url, html in zip(queue, html_pages):
                if not html: continue
                soup = BeautifulSoup(html, "html.parser")

                for a in soup.find_all("a", href=True):
                    href = a["href"].split("#")[0]

                    # normalise relative/ scheme-less URLs
                    if href.startswith("//"):
                        href = "https:" + href
                    if href.startswith("/"):
                        href = urljoin(root, href)

                    if domain not in urlparse(href).netloc:
                        continue
                    if href in seen:
                        continue

                    # classify link
                    if PDF_REGEX.search(href):
                        pdfs.append(href)
                    elif HTML5_HINTS.search(href):
                        html5.append(href)

                    match = TOOL_PATTERNS.search(href)
                    if match:
                        tools.add(match.group(1).lower())

                    if re.search(r"/partners|/resellers|/channel", href, re.I):
                        partner_portal = True

                    # queue for next depth if HTML-ish link
                    if (not href.lower().endswith((".pdf", ".zip", ".doc", ".docx"))
                            and len(seen) < max_pages):
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
