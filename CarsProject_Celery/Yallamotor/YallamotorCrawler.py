from common import *
from celery_worker import celery_app


db = client['yallamotor']
product_collection = db['urls']
cache_collection = db['cache']
error_collection = db['error']


def check_cache_for(data):
    return cache_collection.find_one(data)

@celery_app.task(queue = 'yallamotor')
def crawl_from_brands():    
    try:
        check_data = check_cache_for({'url': 'https://uae.yallamotor.com/used-cars', 'page': 'brands'})
        if check_data is not None:
            html = check_data['data']
            status = 200
        else:
            req = send_req_syphoon(PROXY_VENDOR, 'GET', 'https://uae.yallamotor.com/used-cars')
            html,status = req.text,req.status_code

            req.raise_for_status()
            cache_collection.insert_one({'url': 'https://uae.yallamotor.com/used-cars', 'data': html, 'page': 'brands'})

        soup = BeautifulSoup(html, 'html.parser')
        brand_urls = [a.get('href') for a in soup.select('div#makesListing a')]
        for brand_url in brand_urls:
            crawl_page.delay(brand_url)
            
    except Exception as ex:
        error_collection.insert_one(
            {
                'url': 'https://uae.yallamotor.com/used-cars',
                'page': 'brands',
                'status': status,
                'error': str(ex),
                'traceback': traceback.format_exc(),
            }
        )

@celery_app.task()
def crawl_page(brand_url,page=1):
    try:
        check_data = check_cache_for({'url': brand_url, 'page': page})
        if check_data is not None:
            html = check_data['data']
            status = 200
        else:
            req = send_req_syphoon(PROXY_VENDOR, 'GET', brand_url+f'?page={page}&sort=updated_desc')
            html,status = req.text,req.status_code

            req.raise_for_status()
            cache_collection.insert_one({'url': brand_url, 'data': html, 'page': page})

        soup = BeautifulSoup(html, 'html.parser')
        
        products = [
            {'url': 'https://uae.yallamotor.com'+i.get('href'), 'name': i.text,'brand': brand_url, 'page': page, 'scraped': 0}
            for i in soup.select('div.singleSearchGrid h2 a')
            if product_collection.find_one({'url': 'https://uae.yallamotor.com'+i.get('href')}) is None
        ]

        if len(products) != 0:
            product_collection.insert_many(products)

        if page==1:
            if soup.find('a',attrs={"aria-label":"next page"}):
                try:total_pages = int(soup.find('a',attrs={"aria-label":"next page"}).find_previous_sibling('a').text)
                except: total_pages = int(soup.select_one('div.m20t.m12b.color-gray.text-center b:last-child').text) // 16 + 1
                for page in range(2,total_pages+1):
                    crawl_page.delay(brand_url,page)

    except Exception as ex:
        error_collection.insert_one(
            {
                'url': brand_url,
                'page': page,
                'status': status,
                'date_time': datetime.now(),
                'error': str(ex),
                'traceback': traceback.format_exc(),
            })