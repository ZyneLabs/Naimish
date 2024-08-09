from common.utils import *
from .Albacarsscraper import albacars_scraper

queue = Queue('Albacars',connection=redis_conn)


db = client['albacars']
product_collection = db['urls']
cache_collection = db['cache']
error_collection = db['error']

def check_cache_for(data):
    return cache_collection.find_one(data)

def save_cache_for(url,data, page=1):
    
    cache_collection.insert_one(
            {
               
                'url': url,
                'page': page,
                'data': data,
                'updated_at': datetime.now(),
                'data_format': 'html',
                'info_type': 'crawl',
                'info_subtype': 'url_crawl',
            }
        )

def crawl_albacars():
    page=0
    while True:
        try:
            url = f'https://www.albacars.ae/all-cars-ajax?id={page}&_token=v1igI8bUlgnUzd9iwhrScZxJpXaSIMH4AlhOYPcB'
            cache_data = check_cache_for({'url': url, 'page': page})
            if cache_data is not None:
                html = cache_data['data']
                status = 200
            else:
                req = albacars_scraper(url)
                html = req.text
                status = req.status_code
                save_cache_for(url,html,page)

            soup = BeautifulSoup(html, 'html.parser')
            
            product_soup = soup.select('.listviews a')
            if not product_soup:
                break

            products = []
            for item in product_soup:
                product_url = item.get('href')
                price_list = item.select_one('span.titlenm:not(:has(del))').text.split(' ')
                if product_collection.find_one({'url': product_url}) is not None: continue

                product_info = {
                    'url': product_url,
                    'id': product_url.split('/')[-1].split('-')[0],
                    'title': item.find('h3').text,
                    'price': price_list[1].strip(),
                    'currency': price_list[0].strip(),
                    'image' : item.find('img').get('src'),
                    'odometer': item.select_one('.kms').text,
                    'finance':{'price':item.select_one('.aedprice').text.strip(),
                               'downpayment':item.select_one('.downpayment').text.split('Downpayment')[0].strip(),
                               'duration':item.select_one('.downpayment').text.split('Downpayment')[1].strip()
                               },
                    'scraped': 0
                }

                products.append(product_info)

            if len(products) != 0:
                product_collection.insert_many(products)
            
            page += 9
            
        except Exception as ex:
            error_collection.insert_one(
                {
                    'url': url,
                    'page': page,
                    'status': status,
                    'date_time': datetime.now(),
                    'error': str(ex),
                    'traceback': traceback.format_exc(),
                }
            )