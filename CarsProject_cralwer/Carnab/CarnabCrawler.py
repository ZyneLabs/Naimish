import json
import logging
from datetime import datetime
import traceback
import requests
from redis import Redis
from rq import Queue

redis_conn = Redis()
queue = Queue('Carnab',connection=redis_conn)

logger = logging.getLogger('CarnabCrawler')
logger.setLevel(logging.ERROR)
log_file_name = "CarnabCrawler.log"
file_handler = logging.FileHandler(f'./{log_file_name}')
formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
file_handler.setFormatter(formatter)
logger.addHandler(file_handler)

def crawl_urls(page=0):
    url = 'https://zc2yl0jdgy-dsn.algolia.net/1/indexes/*/queries?x-algolia-agent=Algolia%20for%20JavaScript%20(4.13.1)%3B%20Browser%20(lite)%3B%20JS%20Helper%20(3.8.2)%3B%20react%20(17.0.2)%3B%20react-instantsearch%20(6.26.0)&x-algolia-api-key=7686cb7c0c84e002e9f57028f5b8d647&x-algolia-application-id=ZC2YL0JDGY'

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
        
        req = requests.post(
            url,
            headers=headers,
            data=data,
        )
        page_json = req.json()

        products_list = page_json['results'][0]['hits']
        if len(products_list) != 0:
            page += 1
            queue.enqueue(crawl_urls, page)
        

        products = []
        for item in products_list:
            product_url = 'https://carnab.com/uae-en/details/'+item['slug']
        
            product_info = {
                'url': product_url,
                'name': item['name'],
                'make': item['make'],
                'model': item['model'],
                'odometer': item['km'],
                'year': item['year'],
                'color': item['color'],
                'location': None,
                'engine_size': item['engine_size'],
                'trim':None,
                'price': item['price'],
                'image' : ' | '.join([media['image'] for media in item['media'] if media.get('image')]),
                'post_datetime':None,
                'extra':{
                    'specs': item['specs'],
                    'transmission': item['gear'],
                    'body_type': item['body_type']
                    },  
                'scraped':0,
                'scraped_at':datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            }
            if item['emiOptions']['optionDownPayment']:
                product_info['extra']={
                'finance' : {'price':item['emiPerMonth'],
                            'downpayment':item['emiOptions']['optionDownPayment']['min_perc'],
                            'duration':item['emiOptions']['optionLoanTenure']['preselected']
                            }}
                
            products.append(product_info)

        if len(products)>0:
            json.dump(products, open('carnab.json', 'a', encoding='utf-8'), indent=4)
       
        
    except Exception as ex:
        logger.error(f'{page} - {str(ex)} - {str(traceback.format_exc())}')
    
   