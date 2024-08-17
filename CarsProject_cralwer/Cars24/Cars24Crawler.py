
import json
import logging
from datetime import datetime
import traceback
import requests
from redis import Redis
from rq import Queue

logger = logging.getLogger('Cars24Crawler')
logger.setLevel(logging.ERROR)
log_file_name = "Cars24Crawler.log"
file_handler = logging.FileHandler(f'./{log_file_name}')
formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
file_handler.setFormatter(formatter)
logger.addHandler(file_handler)

redis_conn = Redis()
queue = Queue('Cars24',connection=redis_conn)


def crawl_urls(page=0,current_item=0):
    parent_category_code = 'buy-used-cars-uae'
    headers= {
            'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36',
            'x_country': 'AE',
            'x_platform': 'desktop',
            'x_vehicle_type': 'CAR',
        } 
    try:
    
        req_url = f'https://listing-service.c24.tech/v2/vehicle?isSeoFilter=true&size=25&spath={parent_category_code}&page={page}'
        
        res = requests.get(
            url=req_url,
            headers=headers
        )
        data = res.json()
            
        total_item = data.get('total')
        products = [
            {'url' : f'https://www.cars24.ae/buy-used-{i["make"]}-{i["model"]}-{i["year"]}-cars-{i["city"]}-{i["appointmentId"]}'.lower().replace(' ', '-'),
                'name' : f'{i["make"]} {i["model"]} {i["year"]} {i["variant"]}',
                'make': i["make"],
                'model': i["model"],
                'odometer': i["odometerReading"],
                'year': i["year"],
                'color': i["carExteriorColor"],
                'location': i["city"],
                'engine_size': None,
                'trim': i["trim"],
                'price': i["price"],
                'image': 'https://media-ae.cars24.com/'+i["mainImage"]['path'],
                'post_datetime': None,
                'extra':{
                'variant': i["variant"],
                'specs': i["specs"],
                'finance': i["emiDetails"],
                'transmission': i["transmissionType"],
                'fuel_type': i["fuelType"]
                },
                'scraped':0,
                'scraped_at': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                }
            for i in data.get('results') 
        ]
        current_item += len( data.get('results') )

        if current_item < total_item:
            page += 1
            queue.enqueue(crawl_urls, page, current_item)
        
        if len(products) > 0:
            json.dump(products, open(f'cars24.json', 'a', encoding='utf-8'), indent=4)
            
    except Exception as ex:
        logger.error(f'{page} - {str(traceback.format_exc())}')