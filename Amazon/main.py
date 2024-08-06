from fastapi import FastAPI, Query, Response, HTTPException,Body
from typing import Annotated

from Amazon import amazon_parser,get_domain_name,amazon_scraper,amazon_review_parser
from Walmart import walmert_parser,walmart_scraper
from BestBuy import bestbuy_parser,bestbuy_scraper
from pydantic import BaseModel
from pymongo.mongo_client import MongoClient
from datetime import datetime

import examples as ex

mongo = MongoClient()
amazon_collection = mongo["Amazon"]["urls"]
walmart_collection = mongo["Walmart"]["urls"]
bestbuy_collection = mongo["BestBuy"]["urls"]

amazon_whitelist = ['amazon.com', 'amazon.ca', 'amazon.co.uk']
walmart_whitelist = ['walmart.com', 'walmart.ca']

class ScrapeModel(BaseModel):
    url: str
    token: str


class AmazonReviewModel(BaseModel):
    domain : str
    asin : str
    token : str
    page : int = 1

tags_metadata = [
    {
        "name": "Amazon",
        "description": "Scrape details from Amazon",
    },
    {
        "name": "Walmart",
        "description": "Scrape details from Walmart",
    },
    {
        "name": "Best Buy",
        "description": "Scrape details from Best Buy",
    },
]

app_description = """
E-commerce scraper API. helps you to scrape data from e-commerce websites.
"""

app = FastAPI(
    title="E-Commerce Scraper API",
    description=app_description,
    version="0.0.1",
    openapi_tags=tags_metadata
    )

# @app.get("/")
# async def root():
#     return {"message": "Hello World"}

@app.post("/walmart/product",tags=["Walmart"])
async def walmart(body: Annotated[ScrapeModel,Body(openapi_examples=ex.walmart_product_examples)], response: Response):
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
    
    walmart_collection.insert_one({"url": url, "timestamp": datetime.now(), "token": token})

    if page_response.status_code == 200:
        return walmert_parser(url,page_response.text)
    else:
        raise HTTPException(status_code=page_response.status_code, detail=page_response.text)


@app.post("/amazon/product",tags=["Amazon"])
async def amazon(body: Annotated[ScrapeModel,Body(openapi_examples=ex.amazon_prodcut_examples)], response: Response):
    url = body.url
    token = body.token

    if token != "Testing Naimish Amazon... :)":
        response.status_code = 401
        return 
    domain = get_domain_name(url)
    amazon_collection.insert_one({"url": url, "timestamp": datetime.now(), "token": token})
    if domain not in amazon_whitelist:
        return HTTPException(status_code=400, detail=f"Invalid URL: {url}. Only {', '.join(amazon_whitelist[:-1])} and {amazon_whitelist[-1]} URLs are accepted.")
    
    if '?th' in url:
        url +='&psc=1'
    elif '?' in url:
        url += '&th=1&psc=1'
    else:
        url += '?th=1&psc=1'
        
    asin = url.split('/dp/')[1].split('/')[0].split('?')[0]

    page_html  = amazon_scraper(url,asin,domain)
    try:
        if page_html.get('message',''):
            raise HTTPException(status_code=401, detail=page_html['message'])
    except:
        ...
            
    return amazon_parser(url,domain,page_html,asin)
    
    
@app.post("/amazon/review",tags=["Amazon"])
async def amazon_review(body: Annotated[AmazonReviewModel, Body(openapi_examples=ex.amazon_review_examples)],response: Response):
    
    asin = body.asin
    token = body.token
    domain = body.domain
    page = body.page

    if token != "Testing Naimish Amazon... :)":
        response.status_code = 401
        return None
    
    if domain not in amazon_whitelist:
        return HTTPException(status_code=400, detail=f"Invalid Domain for :{asin}. Only {', '.join(amazon_whitelist[:-1])} and {amazon_whitelist[-1]} URLs are accepted.")
    
    review_url  = f'https://www.{domain}/product-reviews/{asin}'
    
    if page<1:
        return HTTPException(status_code=400, detail="Invalid page number")
    else:
        review_url = f'{review_url}?pageNumber={page}'

    domain = body.domain

    filename  = f'{asin}_{page}'
    page_html = amazon_scraper(review_url,filename,domain)
    try:
        if page_html.get('message',''):
            raise HTTPException(status_code=401, detail=page_html['message'])
    except:
        ...
        
    request_info = {
        "request_info":
        {
            "asin": asin,
            "domain": domain,
            "page": page,
        }
    } 
    return request_info|amazon_review_parser(page_html,domain)

@app.post("/bestbuy/product",tags=["Best Buy"])
async def bestbuy(body: Annotated[ScrapeModel,Body(openapi_examples=ex.bestbuy_product_examples)], response: Response):
    url = body.url
    token = body.token

    if token != "Testing Naimish Best Buy... :)":
        response.status_code = 401
        return

    if get_domain_name(url) !='bestbuy.com':
        response.status_code = 400
        return HTTPException(status_code=400, detail=f"Invalid URL: {url}. Only 'bestbuy.com' URLs are accepted.")

    page_response  = bestbuy_scraper(url)
    bestbuy_collection.insert_one({"url": url, "timestamp": datetime.now(), "token": token})
    
    if page_response.status_code != 200:
        raise HTTPException(status_code=page_response.status_code, detail=page_response.text)
    
    return bestbuy_parser(url,page_response.text)
   


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="127.0.0.1", port=8000, reload=True)
