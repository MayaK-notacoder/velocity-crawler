from fastapi import FastAPI, HTTPException, Query
from crawler import crawl
import validators
import asyncio

app = FastAPI()

@app.get("/crawl", summary="Crawl a site for PDF/HTML5 counts")
async def crawl_endpoint(url: str = Query(..., description="Root website URL")):
    if not validators.url(url):
        raise HTTPException(status_code=400, detail="Invalid URL")
    try:
        # 90-second overall timeout
        # smaller crawl for faster completion
return await asyncio.wait_for(crawl(url, max_pages=150, depth=3), timeout=60)
    except asyncio.TimeoutError:
        raise HTTPException(status_code=504, detail="Crawl timed out")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
