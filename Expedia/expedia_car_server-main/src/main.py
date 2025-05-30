from fastapi import FastAPI, Response

app = FastAPI()

@app.get("/search")
async def trigger_search_cars(res: Response, search_url: str, max_results: int = 0):
    required_params = ('locn', 'dpln', 'date1', 'date2', 'time1', 'time2')    
    
    if "expedia.co.uk/search" not in search_url or not all(x in search_url for x in required_params):
        res.status_code = 400
        return "Invalid URL"
    
    start_search_cars(search_url)