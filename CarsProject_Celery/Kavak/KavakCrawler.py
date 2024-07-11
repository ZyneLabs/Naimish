from celery_worker import celery_app
from common import *

db = client['kavak']
product_collection = db['urls']
cache_collection = db['cache']
error_collection = db['error']


def check_cache_for(data):
    return cache_collection.find_one(data)


def save_cache_for(req_url, page, data):
    
    cache_collection.insert_one(
            {
                'input': {
                    'url': req_url,
                    'page': page
                },
                'data': data,
                'updated_at': datetime.now(),
                'data_format': 'html',
                'info_type': 'crawl',
                'info_subtype': 'url_crawl',
            }
        )
    
def save_urls_from_html(html,page):
    soup = BeautifulSoup(html, 'lxml')
    products = [
        {'url' : i.get('href'),'name':i.text,'page':page,'scraped':0}
        
        for i in soup.find_all('a',  class_="sr-only",attrs={"rel":"noopener"})
        
        if product_collection.find_one({'url':i.get('href')}) is None
    ]

    if len(products) != 0:
        product_collection.insert_many(products)


@celery_app.task(queue = 'kavak')
def crawl_main_page():
    try:
       
        res = send_req_syphoon(PROXY_VENDOR, 'GET', 'https://www.kavak.com/ae/preowned')
        res.raise_for_status()
        soup = BeautifulSoup(res.text, 'lxml') 
        
        save_cache_for('https://www.kavak.com/ae/preowned', 0, res.text)
        save_urls_from_html(res.text,0)

        total_page = int(soup.select_one('div.results span.total').text)

        for page in range(2, total_page+1):
            crawl_urls.delay(page)

    except Exception as ex:
        error_collection.insert_one(
            {
                'url': 'https://www.kavak.com/ae/preowned',
                'page': 0,
                'error': str(ex),
                'traceback': traceback.format_exc(),
            }
        )

@celery_app.task(queue = 'kavak')    
def crawl_urls(page):
    try:
        req_url = f'https://www.kavak.com/ae/preowned?page={page}'

        cache_data = check_cache_for({'input.url': req_url, 'input.page': page})
        
        if cache_data is not None:
            data = cache_data['data']

        else:
            res = send_req_syphoon(
                PROXY_VENDOR,
                method="GET",
                url=req_url,
            )

            res.raise_for_status()

            data = res.text
            save_cache_for(req_url, page, data)

        save_urls_from_html(data,page)

    except Exception as ex:
        error_collection.insert_one(
            {
                'url': req_url,
                'page': page,
                'error': str(ex),
                'traceback': traceback.format_exc(),
            }
        )
