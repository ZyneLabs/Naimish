from common import * 
from redis import Redis
from rq import Queue,Retry
from pymongo.mongo_client import MongoClient

redis_conn = Redis()
q = Queue(connection=redis_conn, default_timeout=3600000)


MONGO_URI = getenv('MONGODB_URI')
PROXY_VENDOR = getenv('PROXY_VENDOR')

client = MongoClient(MONGO_URI)
db = client['amazon_keyword']
product_collection = db['product']
category_collection = db['category']
cache_collection = db['cache']
error_collection = db['error']

def check_cache_for(data):
    return cache_collection.find_one(data)


headers = {
    'sec-ch-ua': '"Not/A)Brand";v="8", "Chromium";v="126", "Google Chrome";v="126"',
    'sec-ch-device-memory': '8',
    'sec-ch-viewport-width': '1850',
    'sec-ch-ua-platform-version': '"6.5.0"',
    'X-Requested-With': 'XMLHttpRequest',
    'dpr': '1',
    'downlink': '10',
    'sec-ch-ua-platform': '"Linux"',
    'device-memory': '8',
    'rtt': '100',
    'sec-ch-ua-mobile': '?0',
    'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36',
    'viewport-width': '1850',
    'Accept': 'text/html, */*; q=0.01',
    'sec-ch-dpr': '1',
    'ect': '4g',
}


def crawl_leaf_category(category_name,category_url):
  
    chache_data = check_cache_for({'url':category_url})
    
    if chache_data:
            html = chache_data['html']
    
    else:
        req = send_req_syphoon(1, 'GET', category_url)
        req.raise_for_status()
        html = req.text
        cache_collection.insert_one({'url':category_url,'html':html,'time':datetime.now()})

    soup = BeautifulSoup(html, 'lxml')  

    maybe_counts_soup = soup.select_one('div[data-a-card-type="basic"] span.a-size-base.a-color-base.a-text-normal')
    if maybe_counts_soup:
        total_products = int(maybe_counts_soup.text.split('over')[1].split('results')[0].replace(',',''))
    elif soup.select_one('span[data-component-type="s-result-info-bar"] div.s-breadcrumb span'):
        total_count_text = soup.select_one('span[data-component-type="s-result-info-bar"] div.s-breadcrumb span').text
        if 'of' in total_count_text:
            total_count_text = total_count_text.split('of')[1]
        if 'over' in total_count_text:
            total_count_text = total_count_text.split('over')[1]
        total_products = int(total_count_text.split('results')[0].replace(',',''))
    else:
        total_products = 0

    for sub_cat_path in ['#s-refinements li.a-spacing-micro.apb-browse-refinements-indent-2 a','li.a-spacing-micro.s-navigation-indent-2 a','#departments li.a-spacing-micro.s-navigation-indent-1 a','div.left_nav.browseBox li a']:
        if soup.select(sub_cat_path) and total_products > 300:
            cat_urls = {
                a.text.strip() : 'https://www.amazon.com'+a['href']
                for a in soup.select(sub_cat_path)
            }

            category_collection.insert_one({
                "name" : category_name,
                "url" : category_url,
                "child_categories" : cat_urls
            })
            
            q.enqueue_many(
                [
                Queue.prepare_data(
                    crawl_leaf_category, 
                    (cat_name,cat_url),
                    retry=Retry(max=3)
                    )
                    for cat_name,cat_url in cat_urls.items()
                ]
            )
            break

    else:
        if soup.find('a',id="apb-desktop-browse-search-see-all"):
            crawl_leaf_category(category_name,'https://www.amazon.com'+soup.find('a',id="apb-desktop-browse-search-see-all")['href'])

        elif soup.select('div[data-component-type="s-search-result"] h2 a'):
            exclude_links = soup.select('div[data-component-type="s-search-result"] div[data-component-type="s-impression-logger"] h2 a')
            products = [
                {
                    "name" : item.text.strip(),
                    "url" : 'https://www.amazon.com'+item['href'],
                    "category" : category_name,
                }
                for item in soup.select('div[data-component-type="s-search-result"] h2 a')
                if item not in exclude_links
                and product_collection.find_one({'url': 'https://www.amazon.com'+item['href']}) is None
            ]
            if products:
                product_collection.insert_many(products)

            if soup.find('a',attrs={'aria-label':re.compile('Go to next')}):
                next_page = soup.find('a',attrs={'aria-label':re.compile('Go to next')})
                max_page = int(next_page.previous_element)
                page_url = 'https://www.amazon.com'+next_page['href']

                q.enqueue_many(
                    [
                    Queue.prepare_data(
                        crawl_products, 
                        (category_name,page_url,page),
                        retry=Retry(max=5)
                        )
                        for page in range(2,min(max_page+1,6))
                    ]
                )


def crawl_products(category_name,category_url,page):

    req_url = re.sub(r'(ref=sr_pg_\d+)',f'ref=sr_pg_{page}',re.sub(r'(&amp;page=)\d+', f'&amp;page={page}', category_url))

    cache_data = check_cache_for({'url':req_url,'page':page})

    if cache_data:
        html = cache_data['html']

    else:
        req = send_req_syphoon(1, 'GET', req_url)
        req.raise_for_status()
        html = req.text
        cache_collection.insert_one({'url':req_url,'html':html,'time':datetime.now(),'page':page})

    soup = BeautifulSoup(html, 'lxml')
    products_soup = soup.select('div[data-component-type="s-search-result"] h2 a')
    if products_soup:
        exclude_links = soup.select('div[data-component-type="s-search-result"] div[data-component-type="s-impression-logger"] h2 a')

        products = [
            {
                "name" : item.text.strip(),
                "url" : 'https://www.amazon.com'+item['href'],
                "category" : category_name,
                "category_url":req_url,
            }
            for item in products_soup 
            if product_collection.find_one({'url': 'https://www.amazon.com'+item['href']}) is None
            and item not in exclude_links
        ]
        if products:
            product_collection.insert_many(products)

