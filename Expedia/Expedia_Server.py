from expedia_car_scraper import expedia_search_crawler , expedia_internal_search_crawler
from fastapi import FastAPI, HTTPException, BackgroundTasks, Request
import motor.motor_asyncio
from datetime import datetime

MONGO_URI = "mongodb://localhost:27017"
DB_NAME = "expedia"
COLLECTION_NAME = "car_searches"

db_client = motor.motor_asyncio.AsyncIOMotorClient(MONGO_URI)
db = db_client[DB_NAME]
collection = db[COLLECTION_NAME]

app = FastAPI()


async def crawl_and_save(url,max_results):
    try:
        data = await expedia_internal_search_crawler(url,5)
        await collection.insert_one({"search_url": url, "data": data, "created_at": datetime.now()})

    except Exception as e:
        print(e)


REQUIRED_PARAMS = ('https://www.expedia.co.uk/carsearch','locn', 'dpln', 'date1', 'date2', 'time1', 'time2')

@app.get("/internal_search")
async def search_cars(search_url: str, max_results: int,background_tasks: BackgroundTasks ):
    if not search_url:
        raise HTTPException(status_code=400, detail="Invalid URL")
    
    for param in REQUIRED_PARAMS:
        if param not in search_url:
            raise HTTPException(status_code=400, detail=f"Invalid URL : {param} is missing")
    
    
    background_tasks.add_task(crawl_and_save, search_url,max_results)
    
    return {'message': 'Task created'}

@app.get("/search")
async def search_cars(search_url: str, max_results: int):
    if not search_url:
        raise HTTPException(status_code=400, detail="Invalid URL")
    
    for param in REQUIRED_PARAMS:
        if param not in search_url:
            raise HTTPException(status_code=400, detail=f"Invalid URL : {param} is missing")
    
    data = await expedia_search_crawler(search_url,max_results)
    return data