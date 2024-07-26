from fastapi import FastAPI, Query
from AmazonScraper import amazon_scraper
from AmazonParser_v2 import *

app = FastAPI()

@app.get("/")
async def root():
    return {"message": "Hello World"}

@app.get("/amazon/")
async def amazon(url: str):

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
