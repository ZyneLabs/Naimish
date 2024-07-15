from common import *

redis_conn = Redis()
q = Queue(connection=redis_conn, default_timeout=3600000)


MONGO_URI = getenv('MONGODB_URI')
PROXY_VENDOR = getenv('PROXY_VENDOR')

client = MongoClient(MONGO_URI)
db = client['amazon']
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

def crawl_category():
    req = send_req_syphoon(0,'get','https://www.amazon.in/')
    soup = BeautifulSoup(req.text,'lxml')
    categories = {}
    for i in soup.find('select',id="searchDropdownBox").find_all('option')[1:]:
        if i.text in ['Deals',"Subscribe & Save"] or 'Under ' in i.text or 'Amazon' in i.text:continue
        search = i['value'].replace('search-alias=','')
        params = {
            'limit': '11',
            'prefix': '',
            'suggestion-type': [
                'WIDGET',
                'KEYWORD',
            ],
            'page-type': 'Gateway',
            'alias':search,
            'site-variant': 'desktop',
            'version': '3',
            'event': 'onfocus',
            'wc': '',
            'lop': 'en_IN',
            'last-prefix': '\x00',
            'avg-ks-time': '0',
            'fb': '1',
            'session-id': '261-1839024-5051426',
            'request-id': 'B5B5F6CJ76DG184BAKJS',
            'mid': 'A21TJRUUN4KGV',
            'plain-mid': '44571',
            'client-info': 'search-ui',
        }
        response = requests.get('https://completion.amazon.in/api/2017/suggestions', params=params, headers=headers)

        params = {
            'url': f'search-alias={search}',
            'field-keywords': '',
            'crid': response.json()['responseId'],
            'sprefix': f',{search},243',
        }

        response = requests.get('https://www.amazon.in/s/ref=nb_sb_noss', params=params,  headers=headers)
        url = search_text_between(response.text,'<script>window.location.replace("\\','");</script>')
        if url:
            categories[i.text] = 'https://www.amazon.in' + url
        else:
            categories[i.text] = response.url


    category_collection.insert_many(categories.items())

    q.enqueue_many(
        [
        Queue.prepare_data(
            crawl_leaf_category, 
            (cat_name,cat_url),
            retry=Retry(max=3)
            )
        for cat_name,cat_url in categories.items() if cat_name not in ['Deal','Subscribe & Save'] and 'Under ' not in cat_name and 'Amazon' not in cat_name
        ]
    )


def crawl_leaf_category(category_name,category_url):
    
    key  = randint(0,1)
    req = send_req_syphoon(key, 'GET', category_url)
    req.raise_for_status()

    soup = BeautifulSoup(req.text, 'lxml')  

    if soup.select_one('div[data-a-card-type="basic"] span.a-size-base.a-color-base.a-text-normal'):
        total_products = int(soup.select_one('div[data-a-card-type="basic"] span.a-size-base.a-color-base.a-text-normal').text.split('over')[1].split('results')[0].replace(',',''))
    else:
        total_products = 0

    if total_products > 5000:
        for sub_cat_path in ['li.a-spacing-micro.apb-browse-refinements-indent-2 a','li.a-spacing-micro.s-navigation-indent-2 a','div.left_nav.browseBox li a']:
            if soup.select(sub_cat_path):
                cat_urls = {
                    a.text.strip() : 'https://www.amazon.in'+a['href']
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
            crawl_leaf_category(category_name,'https://www.amazon.in'+soup.find('a',id="apb-desktop-browse-search-see-all")['href'])

        elif soup.select('div[data-component-type="s-search-result"] h2 a'):

            products = [
                {
                    "name" : item.text.strip(),
                    "url" : 'https://www.amazon.in'+item['href'],
                    "category" : category_name,
                }
                for item in soup.select('div[data-component-type="s-search-result"] h2 a')
            ]

            product_collection.insert_many(products)

            if soup.find('a',attrs={'aria-label':re.compile('Go to next')}):
                next_page = soup.find('a',attrs={'aria-label':re.compile('Go to next')})
                max_page = int(next_page.previous_element)
                page_url = 'https://www.amazon.in'+next_page['href']

                q.enqueue_many(
                    [
                    Queue.prepare_data(
                        crawl_products, 
                        (category_name,page_url,page),
                        retry=Retry(max=5)
                        )
                        for page in range(2,max_page+1)
                    ]
                )


def crawl_products(category_name,category_url,page):
    key = randint(0,1)
    req_url = re.sub(r'(ref=sr_pg_\d+)',f'ref=sr_pg_{page}',re.sub(r'(&amp;page=)\d+', f'&amp;page={page}', category_url))

    req = send_req_syphoon(key, 'GET', req_url)

    req.raise_for_status()

    soup = BeautifulSoup(req.text, 'lxml')

    if soup.select('div[data-component-type="s-search-result"] h2 a'):
        products = [
            {
                "name" : item.text.strip(),
                "url" : 'https://www.amazon.in'+item['href'],
                "category" : category_name,
                "category_url":req_url,
            }
            for item in soup.select('div[data-component-type="s-search-result"] h2 a')

            if product_collection.find_one({'url': 'https://www.amazon.in'+item['href']}) is None
        ]

        product_collection.insert_many(products)
