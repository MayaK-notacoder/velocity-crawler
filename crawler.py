"""
Asynchronous crawler that:
– visits up to `max_pages` pages within the same domain
– counts PDFs and HTML-style flipbooks
– detects tool names (Ceros, Turtl, Uberflip, Issuu, Storyblok) in URLs
– flags whether a partner / reseller portal exists
– returns sample links (first 5 of each list)
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

async def crawl(root: str, max_pages: int = 200, depth: int = 2):
    root   = root.rstrip("/")
    domain = urlparse(root).netloc
    seen   = set([root])
    queue  = [root]

    pdfs, html5, tools = [], [], set()
    partner_portal = False

    async with aiohttp.ClientSession() as session:
        while queue and len(seen) < max_pages:
            url = queue.pop(0)
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

                # stay on domain
                if urlparse(href).netloc.endswith(domain) is False:
                    continue
                if href in seen:
                    continue

                # classify link
                if href.endswith(".pdf"):
                    pdfs.append(href)
                elif HTML5_HINTS.search(href):
                    html5.append(href)

                tool_match = TOOL_PATTERNS.search(href)
                if tool_match:
                    tools.add(tool_match.group(1).lower())

                if re.search(r"/partners|/resellers|/channel", href, re.I):
                    partner_portal = True

                # breadth-first crawl (skip binary docs)
                if depth > 0 and href.endswith((".pdf", ".zip", ".doc", ".docx")) is False:
                    queue.append(href)

                seen.add(href)

            depth -= 1  # one level finished

    return {
        "pdf_count":        len(pdfs),
        "html5_like_count": len(html5),
        "tools_detected":   sorted(tools),
        "partner_portal":   partner_portal,
        "sample_pdfs":      pdfs[:5],
        "sample_html5":     html5[:5]
    }
