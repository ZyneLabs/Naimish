from fastapi import FastAPI, Query, Response, HTTPException
from AmazonScraper import amazon_scraper
from AmazonParser_v2 import amazon_parser,get_domain_name
from WalmartScraper import walmart_scraper
from Walmart_Parser_v2 import walmert_parser
from pydantic import BaseModel
from pymongo.mongo_client import MongoClient
from datetime import datetime
mongo = MongoClient()
amazon_collection = mongo["Amazon"]["urls"]
walmart_collection = mongo["Walmart"]["urls"]

amazon_whitelist = ['amazon.com', 'amazon.ca', 'amazon.co.uk']
walmart_whitelist = ['walmart.com', 'walmart.ca']

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

    if get_domain_name(url) not in walmart_whitelist:
        raise HTTPException(status_code=400, detail=f"Invalid URL: {url}. Only 'walmart.com' and 'walmart.ca' URLs are accepted.")
    
    page_response  = walmart_scraper(url)
    
    walmart_collection.insert_one({"url": url, "timestamp": datetime.now()})

    if page_response.status_code == 200:
        return walmert_parser(url,page_response.text)
    else:
        raise HTTPException(status_code=page_response.status_code, detail=page_response.text)


@app.post("/amazon/")
async def amazon(body: ScrapeModel, response: Response):
    url = body.url
    token = body.token

    if token != "Testing Naimish Amazon... :)":
        response.status_code = 401
        return None
    domain = get_domain_name(url)
    amazon_collection.insert_one({"url": url, "timestamp": datetime.now()})
    if domain in amazon_whitelist:
        if '?th' in url:
            url +='&psc=1'
        elif '?' in url:
            url += '&th=1&psc=1'
        else:
            url += '?th=1&psc=1'
         
        asin = url.split('/dp/')[1].split('/')[0].split('?')[0]
        return amazon_parser(url,domain,amazon_scraper(url,asin,domain),asin)
    else:
        return {"message": f"Invalid url {url}"}
    

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="127.0.0.1", port=8000, reload=True)
