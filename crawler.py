"""
Given a root URL, crawl up to max_pages pages
– Count PDFs and HTML5 flipbooks
– Flag partner / reseller portals
– Detect tool names inside URLs (Ceros, Turtl, Uberflip, Issuu, etc.)
Return a JSON summary.
"""
import asyncio, re, aiohttp
from urllib.parse import urljoin, urlparse
from bs4 import BeautifulSoup

TOOL_PATTERNS = re.compile(r"(ceros|turtl|uberflip|issuu|storyblok)", re.I)
HTML5_HINTS   = re.compile(r"(/story/|/flipbook/|pubhtml5|/view/)", re.I)

async def fetch(session, url, timeout=10):
    try:
        async with session.get(url, timeout=timeout) as r:
            if "text/html" in r.headers.get("content-type",""):
                return await r.text()
    except Exception:
        pass
    return ""

async def crawl(root:str, max_pages:int=200, depth:int=2):
    root = root.rstrip("/")
    domain = urlparse(root).netloc
    seen, queue = set([root]), [root]
    pdfs, html5, tools, partner_portal = [], [], set(), False

    async with aiohttp.ClientSession() as session:
        while queue and len(seen) < max_pages:
            url = queue.pop(0)
            html = await fetch(session, url)
            if not html: continue
            soup = BeautifulSoup(html, "html.parser")

            # collect links
            for a in soup.find_all("a", href=True):
                href = a["href"].split("#")[0]
                if href.startswith("//"): href = "https:" + href
                if href.startswith("/"):  href = urljoin(root, href)

                if not urlparse(href).netloc.endswith(domain): continue
                if href in seen: continue

                # classify
                if href.endswith(".pdf"):
                    pdfs.append(href)
                elif HTML5_HINTS.search(href):
                    html5.append(href)
                if TOOL_PATTERNS.search(href):
                    tools.add( TOOL_PATTERNS.search(href).group(1).lower() )
                if re.search(r"/partners|/resellers|/channel", href, re.I):
                    partner_portal = True

                # BFS queue
                if depth and len(seen) < max_pages and href.endswith((".pdf",".zip",".docx")) is False:
                    queue.append(href)
                seen.add(href)

    return {
        "pdf_count": len(pdfs),
        "html5_like_count": len(html5),
        "sample_pdfs": pdfs[:5],
        "sample_html5": html5[:5],
        "tools_detected": sorted(tools),
        "partner_portal": partner_portal
    }

# Example (async entry point)
# asyncio.run(crawl("https://example.com"))
