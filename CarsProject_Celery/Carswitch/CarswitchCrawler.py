from common import *
from celery_worker import celery_app

db = client['carswitch']
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
                    'page': page,
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
        {'url' : 'https://carswitch.com/'+i.get('href'),
         'name':i.text,
         'scraped':0,
         'page':page}
        
        for i in soup.select('section#main-listing-div div.pro-item div.title a')
        
        if product_collection.find_one({'url': 'https://carswitch.com'+i.get('href')}) is None
    ]

    if len(products) != 0:
        product_collection.insert_many(products)

@celery_app.task(queue='carswitch')
def crawl_category():
    res = send_req_syphoon(PROXY_VENDOR, 'GET', 'https://carswitch.com/uae/used-cars/search')
    soup = BeautifulSoup(res.text, 'html.parser')
   
    total_page = int(soup.select_one('div.page-number_holder a:last-child').text)
    save_urls_from_html(res.text,1)

    for page in range(2, total_page+1):
        crawl_urls.delay('https://carswitch.com/uae/used-cars/search',page)

@celery_app.task(queue='carswitch')
def crawl_urls(category_url,page ):
    try:
        cache_data = check_cache_for({'input.url': category_url, 'input.page': page})

        if cache_data is not None:
            data = cache_data['data']
            status = 200
        else:
            res = send_req_syphoon(PROXY_VENDOR, 'GET', category_url+f'?page={page}')   
            status = res.status_code
            res.raise_for_status()
            data = res.text
            save_cache_for(category_url,page,data)

        save_urls_from_html(data,page)

    except Exception as ex:
        error_collection.insert_one(
            {
                'url': category_url,
                'page': page,
                'status': status,
                'error': str(ex),
                'traceback': traceback.format_exc(),
            }
        )

def crawl_sitemap():
    try:
        req  = send_req_syphoon(PROXY_VENDOR, 'GET', 'https://www.carswitch.com/sitemap.xml')
        req.raise_for_status()
        soup = BeautifulSoup(req.content, 'xml')

        products = [
            {'url': i.text, 'page': 'sitemap'}
            for i in soup.find_all('loc')

            if product_collection.find_one({'url': i.text}) is None
        ]

        if len(products) != 0:
            product_collection.insert_many(products)
    except Exception as ex:
        error_collection.insert_one(
            {
                'url': 'https://www.carswitch.com/sitemap.xml',
                'page': 'sitemap',
                'error': str(ex),
                'traceback': traceback.format_exc(),
            }
        )
