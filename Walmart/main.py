from fastapi import FastAPI, Query, Response
from WalmartScraper import walmart_scraper
from Walmart_Parser_v2 import walmert_parser
from pydantic import BaseModel
from pymongo.mongo_client import MongoClient
from datetime import datetime
# mongo = MongoClient()
# collection = mongo["Walmart"]["urls"]

class ScrapeModel(BaseModel):
    url: str
    token: str

app = FastAPI()

@app.get("/")
async def root():
    return {"message": "Hello World"}

@app.post("/walmart/")
async def walmart(body: ScrapeModel, response: Response):
    url = body.url
    token = body.token

    if token != "Testing Naimish Walmart... :)":
        response.status_code = 401
        return None
    # collection.insert_one({"url": url, "timestamp": datetime.now()})
    if 'walmart.com' in url or 'walmart.ca' in url:
       
        pid = url.split('/')[-1].split('?')[0]
        return walmert_parser(url,walmart_scraper(url,pid))
    else:
        return {"message": f"Invalid url {url}"}
    

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="127.0.0.1", port=8000, reload=True)