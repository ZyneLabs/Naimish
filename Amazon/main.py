from fastapi import FastAPI, Query, Response
from AmazonScraper import amazon_scraper
from AmazonParser_v2 import *
from pydantic import BaseModel
from pymongo.mongo_client import MongoClient
from datetime import datetime
mongo = MongoClient()
collection = mongo["Amazon"]["urls"]

class ScrapeModel(BaseModel):
    url: str
    token: str

app = FastAPI()

@app.get("/")
async def root():
    return {"message": "Hello World"}

@app.post("/amazon/")
async def amazon(body: ScrapeModel, response: Response):
    url = body.url
    token = body.token

    if token != "Testing Naimish Amazon... :)":
        response.status_code = 401
        return None
    collection.insert_one({"url": url, "timestamp": datetime.now()}}
    if 'amazon.com' in url or 'amazon.ca' in url:
        if '?th' in url:
            url +='&psc=1'
        elif '?' in url:
            url += '&th=1&psc=1'
        else:
            url += '?th=1&psc=1'
         
        asin = url.split('/dp/')[1].split('/')[0].split('?')[0]
        domain = get_domain_name(url)
        return amazon_parser(url,domain,amazon_scraper(url,asin),asin)
    else:
        return {"message": f"Invalid url {url}"}
    

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="127.0.0.1", port=8000, reload=True)
