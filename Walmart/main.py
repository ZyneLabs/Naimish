from fastapi import FastAPI, Query, Response, HTTPException
from WalmartScraper import walmart_scraper
from Walmart_Parser_v2 import walmert_parser
from common import get_domain_name
from pydantic import BaseModel
from pymongo.mongo_client import MongoClient
from datetime import datetime
mongo = MongoClient()
collection = mongo["Walmart"]["urls"]

whitelist = ['walmart.com', 'walmart.ca']
class ScrapeModel(BaseModel):
    url: str
    token: str

app = FastAPI()

@app.get("/")
async def root():
    return {"message": "Hello World"}

@app.post("/walmart/")
async def walmart(body: ScrapeModel, response: Response):
    """
    Parse Walmart product data.

    This endpoint accepts a URL to a Walmart product page and a token for authorization.
    Only URLs from 'walmart.com' and 'walmart.ca' are accepted.

    - **url**: URL to the Walmart product page.
    - **token**: Authorization token.

    Returns parsed product data if the URL is valid and token is correct.
    
    Raises 401 Unauthorized if the token is invalid.
    Raises 400 Bad Request if the URL is not from 'walmart.com' or 'walmart.ca'.
    Raises 4xx and 5xx errors if the URL is invalid or the request fails.
    """
    url = body.url
    token = body.token

    if token != "Testing Naimish Walmart... :)":
        raise HTTPException(status_code=401, detail="Unauthorized")

    if get_domain_name(url) not in whitelist:
        raise HTTPException(status_code=400, detail=f"Invalid URL: {url}. Only 'walmart.com' and 'walmart.ca' URLs are accepted.")
    
    page_response  = walmart_scraper(url)
    
    collection.insert_one({"url": url, "timestamp": datetime.now()})

    if page_response.status_code == 200:
        return walmert_parser(url,page_response.text)
    else:
        raise HTTPException(status_code=page_response.status_code, detail=page_response.text)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="127.0.0.1", port=8000, reload=True)
