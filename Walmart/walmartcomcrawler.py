                
from common import *

redis_conn = Redis()
q = Queue(connection=redis_conn, default_timeout=3600000)


MONGO_URI = getenv('MONGODB_URI')
PROXY_VENDOR = getenv('PROXY_VENDOR')

client = MongoClient(MONGO_URI)
db = client['walmart']
product_collection = db['product']
category_collection = db['category']
cache_collection = db['cache']
error_collection = db['error']

def check_cache_for(data):
    return cache_collection.find_one(data)



def crawl_hierarchical():
    key = randint(0, 1)
    req = send_req_syphoon(key,'get','https://www.walmart.com/all-departments',headers=headers)

    base_soup = BeautifulSoup(req.text, 'html.parser')

    base_categories = {}
    for cat in base_soup.select('div.flex.justify-between.shadow-1.br2.pa4.h-100'):
        cat_name = cat.find('h2').text
        if 'Savings & Featured Shops' in cat_name:continue

        cat_url = cat.select('ul li a')
        if 'all' in cat_url[0].text.lower():
            base_categories[cat_name] = [cat_url[0]['href'] if cat_url[0]['href'].startswith('https') else f'https://www.walmart.com{cat_url[0]["href"]}']
        else:
            base_categories[cat_name] = [cat['href'] if cat['href'].startswith('https') else f'https://www.walmart.com{cat["href"]}' for cat in cat_url  ]

    q.enqueue_many([
        Queue.prepare_data(
            crawl_child_categories,
            (name,url),
            job_id=f'crawling {name} from {url}',
            retry=Retry(max=5, interval=10),
        )
        for name,urls in base_categories.items() for url in urls
    ])



def get_categories_from_content(category_container):
    category_urls_dict = {}
    for cat in category_container.contents:
        cat_name = cat.find('button').text.strip()
        if 'brand' in cat_name.lower() or 'featured'  in cat_name.lower() or 'savings' in cat_name.lower() or 'deal' in cat_name.lower() or 'trending' in cat_name.lower():continue
        
        cat_urls = cat.find('ul').find_all('a')
        
        if 'shop all' in cat_urls[0].text.lower():
            cat_urls = {cat_urls[0].text.strip() :cat_urls[0]['href'] if cat_urls[0]['href'].startswith('https') else f'https://www.walmart.com{cat_urls[0]["href"]}' }
        else:
            cat_urls ={
                        cat.text.strip():cat['href']
                        if cat['href'].startswith('https') else f'https://www.walmart.com{cat["href"]}' 
                        for cat in cat_urls  }

        category_urls_dict[cat_name] = cat_urls

    return category_urls_dict


def crawl_child_categories(category_name,category_url):
    try:
        cache_data = cache_collection.find_one({'url': category_url})

        if cache_data:
            html = cache_data['data']
        else:
            key = randint(0, 1)
            cat_req = send_req_syphoon(key,'get',category_url,headers=headers)

            cat_req.raise_for_status()

            html = cat_req.text
            cache_collection.insert_one(
                    {
                        'url': category_url,
                        'data': html,
                        'updated_at': datetime.now(),
                        'data_format': 'html',
                        'info_type': 'crawl',
                        'info_subtype': 'category_crawl',
                    }
                )
        
        cat_soup = BeautifulSoup(html, 'html.parser')
        category_urls_dict = {}
        for cat in ['Categories','Shop by *|[^ ] category','Category']:
            category_container = cat_soup.find('h2',string=re.compile(cat,re.IGNORECASE))
            if category_container:
                if category_container.find_next_sibling('ul'):
                    category_urls_dict = get_categories_from_content(category_container.find_next_sibling('ul'))
                else:
                    cat_urls={
                                a.text.strip(): a["href"] if a['href'].startswith('https') else f'https://www.walmart.com{a["href"]}'
                                for a in cat_soup.find('h2',string=re.compile(cat,re.IGNORECASE)).find_parent('section').find_all('a')
                                if a.text.strip() not in ['Featured Brands','Savings','Trending','New arrivals'] and 'Trending ' not in a.text 
                                }

                    category_urls_dict[category_name] = cat_urls

                category_collection.insert_one({
                    'category_name': category_name,
                    'category_urls': category_url,
                    'child_category' :category_urls_dict
                })
                q.enqueue_many(
                    [Queue.prepare_data(
                        crawl_child_categories,
                        (f'{cat_name} - {cat}',cat_urls[cat]),
                        result_ttl=5, retry=Retry(1)

                        )
                    for cat_name,cat_urls in category_urls_dict.items() for cat in cat_urls]
                )
                break

        else:
            category_product_json = json.loads(cat_soup.find('script',id="__NEXT_DATA__").text)['props']['pageProps']['initialData']
            total_products = category_product_json['searchResult']['itemStacks'][0]['count']

            departments = []

            for item in category_product_json['moduleDataByZone']['topZone3']['configs']['allSortAndFilterFacets']:
                if item['name'] == 'Departments':
                    departments = item['values'] or []
                    break
                
            if len(departments) > 1 and total_products > 1000:
                category_collection.insert_one({
                    'category_name': category_name,
                    'category_urls': category_url,
                    'child_category' :{
                        d['name']:f'https://www.walmart.com/{d["baseSeoURL"]}'
                         for d in departments}
                })
                q.enqueue_many(
                    [Queue.prepare_data(
                        crawl_departments,
                        (d['name'],'https://www.walmart.com/'+d['baseSeoURL']),
                        retry=Retry(5), job_id=f'Crawling {d["name"]} {d["id"]}'
                    )
                    for d in departments]
                )

            else:
                category_id = category_product_json['searchResult']['catInfo']['catId']
                product_urls = [
                    {
                        'url'  : 'https://www.walmart.com' + item['canonicalUrl'],
                        'name': item['name'],
                        'category_url': category_url,
                        'category_name': category_name,
                        'page':1
                    }
                    for item in category_product_json['searchResult']['itemStacks'][0]['items']

                    if item['__typename'] == 'Product' and product_collection.find_one({'url': 'https://www.walmart.com' + item['canonicalUrl']}) is None
                ]

                if len(product_urls) > 0:
                    product_collection.insert_many(product_urls)

                ####
                #### We can travel upto 25 pages
                ####

                q.enqueue_many(
                    [Queue.prepare_data(
                        crawl_product_urls,
                        (category_name,category_url,category_id,i),
                        retry=Retry(5), job_id=f'Crawling {i} {category_name} {category_id}'
                    )
                    for i in range(2,min((total_products//50) +1,26))]
                )
    except Exception as e:
        error_collection.insert_one({
            'category_name': category_name,
            'category_url': category_url,
            'error': str(e)
            , 'traceback': traceback.format_exc()
        })


def crawl_departments(category_name,category_url):

    try:
        
        cached_data = cache_collection.find_one({'url': category_url})
        if cached_data:
            html = cached_data['data']
        else:
            key = randint(0, 1)
            req = send_req_syphoon(key,'get',category_url,headers=headers)
            req.raise_for_status()
            html = req.text
            cache_collection.insert_one(
                {
                    'url': category_url,
                    'data': req.text,
                    'updated_at': datetime.now(),
                    'data_format': 'html',
                    'info_type': 'crawl',
                    'info_subtype': 'department_crawl',
                }
                
            )
        
        dep_soup = BeautifulSoup(html, 'html.parser')

        page_json = json.loads(dep_soup.find('script',id="__NEXT_DATA__").text)['props']['pageProps']['initialData']
        total_products = page_json['searchResult']['itemStacks'][0]['count']

        departments = []

        for item in page_json['moduleDataByZone']['topZone3']['configs']['allSortAndFilterFacets']:
            if item['name'] == 'Departments':
                departments = item['values'] or []
                break
            
        if len(departments) > 1 and total_products > 1000:
            category_collection.insert_one({
                'category_name': category_name,
                'category_urls': category_url,
                'child_category' :{
                    d['name']:f'https://www.walmart.com/{d["baseSeoURL"]}'
                        for d in departments}
            })
            q.enqueue_many(
                [Queue.prepare_data(
                    crawl_departments,
                    (d['name'],'https://www.walmart.com/'+d['baseSeoURL']),
                    retry=Retry(5), job_id=f'Crawling {d["name"]} {d["id"]}'
                )
                for d in departments]
            )

        else:
            
            category_id = page_json['searchResult']['catInfo']['catId']
            product_urls = [
                {
                    'url'  : 'https://www.walmart.com' + item['canonicalUrl'],
                    'name': item['name'],
                    'category_url': category_url,
                    'category_name': category_name,
                    'page':1
                }
                for item in page_json['searchResult']['itemStacks'][0]['items']

                if item['__typename'] == 'Product' and product_collection.find_one({'url': 'https://www.walmart.com' + item['canonicalUrl']}) is None
            ]

            if len(product_urls) > 0:
                product_collection.insert_many(product_urls)

            ####
            #### We can travel upto 25 pages
            ####

            q.enqueue_many(
                [Queue.prepare_data(
                    crawl_product_urls,
                    (category_name,category_url,i),
                    retry=Retry(5), job_id=f'Crawling {i} {category_name} {category_id}'
                )
                for i in range(2,min((total_products//50) +1,26))]
            )
    except Exception as e:
        error_collection.insert_one({
            'category_name': category_name,
            'category_url': category_url,
            'error': str(e)
            , 'traceback': traceback.format_exc()
        })


def crawl_product_urls(category_name,category_url,page=1):
    req_url= f'{category_url}?page={page}' if '?' not in category_url else f'{category_url}&page={page}'
    
    try:
        cached_data = cache_collection.find_one({'url': category_url,'page':page})
        if cached_data:
            html = cached_data['data']
        else:
            key = randint(0, 1)
            req = send_req_syphoon(key,'get',req_url,headers=headers)
            req.raise_for_status()
            html = req.text
            cache_collection.insert_one(
                    {
                        'url': category_url,
                        'page':page,
                        'data': product_json,
                        'updated_at': datetime.now(),
                        'data_format': 'html',
                        'info_type': 'crawl',
                        'info_subtype': 'product_crawl',
                    }
                )
        
        product_json = json.loads(BeautifulSoup(html, 'html.parser').find('script',id="__NEXT_DATA__").text)['props']['pageProps']['initialData']['searchResult']['itemStacks'][0]['items']
        product_urls = [
            {
                'url'  : 'https://www.walmart.com' + item['canonicalUrl'],
                'name': item['name'],
                'category_url': category_url,
                'category_name': category_name,
                'page':page
            }
            for item in product_json
            if item['__typename'] == 'Product' and product_collection.find_one({'url': 'https://www.walmart.com' + item['canonicalUrl']}) is None
        ]

        if len(product_urls) > 0:
            product_collection.insert_many(product_urls)

    except Exception as e:
        error_collection.insert_one({'error': e, 'category_name': category_name,'category_url':category_url,'page':page,'traceback':traceback.format_exc()})
