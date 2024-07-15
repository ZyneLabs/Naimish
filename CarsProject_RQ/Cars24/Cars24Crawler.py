
from common.utils import *

db = client['cars24']
product_collection = db['urls']
cache_collection = db['cache']
error_collection = db['error']

def crawl_urls():
    parent_category_code = 'buy-used-cars-uae'
    page = 0
    current_item = 0
    headers= {
            'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36',
            'x_country': 'AE',
            'x_platform': 'desktop',
            'x_vehicle_type': 'CAR',
        } 
    try:
        while True:
            req_url = f'https://listing-service.c24.tech/v2/vehicle?isSeoFilter=true&size=25&spath={parent_category_code}&page={page}'
            
            cached_data =cache_collection.find_one({'url': req_url, 'page': page})
            
            if cached_data is not None:
                data = cached_data['data']
                status = 200
            else:
                res = requests.get(
                    url=req_url,
                    headers=headers
                )
                status = res.status_code
                data = res.json()
                cache_collection.insert_one(
                    {
                        'url': req_url,
                        'page': page,
                        'data': data,
                        'updated_at': datetime.now(),
                        'data_format': 'json',
                        'info_type': 'crawl',
                        'info_subtype': 'url_crawl',
                    }
                )
            total_item = data.get('total')
            products = [
                {'url' : f'https://www.cars24.ae/buy-used-{i["make"]}-{i["model"]}-{i["year"]}-cars-{i["city"]}-{i["appointmentId"]}'.lower().replace(' ', '-'),
                 'name' : f'{i["make"]} {i["model"]} {i["year"]} {i["variant"]}',
                 'scraped':0}
                for i in data.get('results') 
                if product_collection.find_one({'url': f'https://www.cars24.ae/buy-used-{i["make"]}-{i["model"]}-{i["year"]}-cars-{i["city"]}-{i["appointmentId"]}'.lower().replace(' ', '-')}) is None
            ]
            current_item += len( data.get('results') )
            
            if len(products) != 0:
                product_collection.insert_many(products)

            if current_item >= total_item:
                break

            page += 1

    except Exception as ex:
        error_collection.insert_one({'parent_category_code': parent_category_code,'status':status,'date_time': datetime.now(), 'page': page,'error': ex, 'traceback': traceback.format_exc()})
