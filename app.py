from fastapi import FastAPI, HTTPException, Query
from crawler import crawl
import validators
import asyncio
from classifier import classify_pdf

app = FastAPI()

@app.get("/crawl", summary="Crawl a site for PDF/HTML5 counts")
async def crawl_endpoint(
    url: str = Query(..., description="Root website URL"),
):
    # simple URL check
    if not validators.url(url):
        raise HTTPException(status_code=400, detail="Invalid URL")

    try:
        # run crawl with smaller limits (150 pages, 3 levels) and 60-second timeout
        result = await asyncio.wait_for(
            crawl(url, max_pages=150, depth=3),
            timeout=60
        )
        return result

    except asyncio.TimeoutError:
        raise HTTPException(status_code=504, detail="Crawl timed out")

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/classify", summary="Classify a single PDF link")
async def classify_endpoint(
    url: str = Query(..., description="Direct PDF URL")
):
    # Runs the simple keyword classifier
    kind, conf = classify_pdf(url)
    return {"content_type": kind, "confidence": round(conf, 2)}
