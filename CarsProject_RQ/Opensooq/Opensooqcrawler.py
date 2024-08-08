from common.utils import *
from .Opensooqscraper import opensooq_scraper

queue = Queue('Opensooq',connection=redis_conn)


db = client['opensooq']
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

def crawl_opensooq(page=1):
    try:
        url = 'https://ae.opensooq.com/en/cars/cars-for-sale'
        if page != 1:
            url = url+'?page='+str(page)

        cache_data = check_cache_for({'url': url, 'page': page})
        if cache_data is not None:
            html = cache_data['data']
            status = 200
        else:
            req = opensooq_scraper(url)
            html = req.text
            status = req.status_code
            save_cache_for(url,html,page)

        soup = BeautifulSoup(html, 'html.parser')
        
        page_json =json.loads(soup.find('script',id="__NEXT_DATA__").text)['props']['pageProps']['serpApiResponse']['listings']

        products = []
        for item in page_json['items']:
            product_url = 'https://ae.opensooq.com/en'+item['post_url']
            if product_collection.find_one({'url': product_url}) is not None: continue

            product_info = {
                'url': product_url,
                'id': item['id'],
                'title': item['title'],
                'price': item['price_amount'].split(' ')[0],
                'currency': item['price_currency_iso'],
                'location': item['city_reporting'],
                'images' : ['https://opensooq-images.os-cdn.com'+image.replace('{size}','2048x0') for image in item['images']],
                'highlights' : item['highlights'].replace('»',','),
                'keywords': item['cps'],
                'listing_status': item['listing_status'],
                'publish_date':item['inserted_date'],
                'expired_at':item['expired_at'],
                'scraped': 0
            }

            products.append(product_info)

        if len(products) != 0:
            product_collection.insert_many(products)
        
        if page == 1:
           total_pages=page_json['meta']['pages']+1
           
           for i in range(2,10):
                queue.enqueue(crawl_opensooq, i)

    except Exception as ex:
        error_collection.insert_one(
            {
                'url': 'https://ae.opensooq.com/en/cars/cars-for-sale',
                'page': page,
                'status': status,
                'date_time': datetime.now(),
                'error': str(ex),
                'traceback': traceback.format_exc(),
            }
        )