from common.utils import *

queue = Queue('Carnab',connection=redis_conn)


db = client['carnab']
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
                'data_format': 'json',
                'info_type': 'crawl',
                'info_subtype': 'url_crawl',
            }
        )

def crawl_carnab():
    page=0
    url = 'https://zc2yl0jdgy-dsn.algolia.net/1/indexes/*/queries?x-algolia-agent=Algolia%20for%20JavaScript%20(4.13.1)%3B%20Browser%20(lite)%3B%20JS%20Helper%20(3.8.2)%3B%20react%20(17.0.2)%3B%20react-instantsearch%20(6.26.0)&x-algolia-api-key=7686cb7c0c84e002e9f57028f5b8d647&x-algolia-application-id=ZC2YL0JDGY'
    while True:
        try:
            headers = {
                'Accept': '*/*',
                'Accept-Language': 'en-GB,en-US;q=0.9,en;q=0.8',
                'Connection': 'keep-alive',
                'Origin': 'https://carnab.com',
                'Referer': 'https://carnab.com/',
                'Sec-Fetch-Dest': 'empty',
                'Sec-Fetch-Mode': 'cors',
                'Sec-Fetch-Site': 'cross-site',
                'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36',
                'content-type': 'application/x-www-form-urlencoded',
                'sec-ch-ua': '"Not/A)Brand";v="8", "Chromium";v="126", "Google Chrome";v="126"',
                'sec-ch-ua-mobile': '?0',
                'sec-ch-ua-platform': '"Linux"',
            }

            data = '{"requests":[{"indexName":"stg-cars","params":"highlightPreTag=%3Cais-highlight-0000000000%3E&highlightPostTag=%3C%2Fais-highlight-0000000000%3E&query=&hitsPerPage=50&filters=country_id%3A1&page='+str(page)+'&facets=%5B%5D&tagFilters="}]}'
            
            cache_data = check_cache_for({'url': url, 'page': page})
            if cache_data is not None:
                page_json = cache_data['data']
                status = 200
            else:
                req = requests.post(
                    url,
                    headers=headers,
                    data=data,
                )
                page_json = req.json()
                status = req.status_code
                save_cache_for(url,page_json,page)

            products_list = page_json['results'][0]['hits']
            if len(products_list) == 0: break
            

            products = []
            for item in products_list:
                product_url = 'https://carnab.com/uae-en/details/'+item['slug']
                if product_collection.find_one({'url': product_url}) is not None: continue

                product_info = {
                    'url': product_url,
                    'id': item['id'],
                    'name': item['name'],
                    'make': item['make'],
                    'model': item['model'],
                    'body_type': item['body_type'],
                    'price': item['price'],
                    'currency': item['currency'],
                    'images' : [media['image'] for media in item['media'] if media.get('image')],
                    'odometer': item['km'],
                    'specs': item['specs'],
                    'year': item['year'],
                    'color': item['color'],
                    'transmission': item['gear'],
                    'engine_size': item['engine_size'],
                    
                   
                }
                if item['emiOptions']['optionDownPayment']:
                    product_info['finance']={'price':item['emiPerMonth'],
                                'downpayment':item['emiOptions']['optionDownPayment']['min_perc'],
                               'duration':item['emiOptions']['optionLoanTenure']['preselected']
                               }
                product_info['scraped'] = 0
                products.append(product_info)

            if len(products) != 0:
                product_collection.insert_many(products)
            
            page += 1
            
        except Exception as ex:
            print(traceback.format_exc())
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