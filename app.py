from fastapi import FastAPI, HTTPException
from crawler import crawl   # your async crawl(root, max_pages=200)

app = FastAPI()

@app.get("/crawl")
async def crawl_endpoint(url: str):
    try:
        return await crawl(url)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
