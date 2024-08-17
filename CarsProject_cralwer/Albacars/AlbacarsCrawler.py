from .Albacarsscraper import albacars_scraper
import json
import logging
from datetime import datetime
import traceback
from bs4 import BeautifulSoup
from redis import Redis
from rq import Queue

redis_conn = Redis()
queue = Queue('Albacars',connection=redis_conn)

logger = logging.getLogger('AlbacarsCrawler')
logger.setLevel(logging.ERROR)
log_file_name = "AlbacarsCrawler.log"
file_handler = logging.FileHandler(f'./{log_file_name}')
formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
file_handler.setFormatter(formatter)
logger.addHandler(file_handler)


def crawl_urls(start_index=0):
   
        try:
            url = f'https://www.albacars.ae/all-cars-ajax?id={start_index}&_token=v1igI8bUlgnUzd9iwhrScZxJpXaSIMH4AlhOYPcB'
            req = albacars_scraper(url)
            html = req.text
            soup = BeautifulSoup(html, 'html.parser')
            
            product_soup = soup.select('.listviews a')
            if  product_soup:
                start_index += 9
                queue.enqueue(crawl_urls, start_index)

            products = []
            for item in product_soup:
                product_url = item.get('href')
                price_list = item.select_one('span.titlenm:not(:has(del))').text.split(' ')
                product_info = {
                    'url': product_url,
                    'name': item.find('h3').text,
                    'make': item.find('h3').text.split(' ')[0],
                    'model': ' '.join(item.find('h3').text.split(' ')[1:]),
                    'odometer': item.select_one('.kms').text,
                    'year': item.select_one('.modelyr').text,
                    'color':None,
                    'location':None,
                    'engine_size':None,
                    'trim':None,
                    'price': price_list[1].strip(),
                    'image' : item.find('img').get('src'),
                    'post_datetime' : None,
                    'extra':{
                            'finance':{'price':item.select_one('.aedprice').text.strip(),
                                    'downpayment':item.select_one('.downpayment').text.split('Downpayment')[0].strip(),
                                    'duration':item.select_one('.downpayment').text.split('Downpayment')[1].strip()
                                    }},
                    'scraped': 0,
                    'scraped_at': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                }

                products.append(product_info)

            if len(products)>0:
                json.dump(products, open('Albacars.json', 'a'),indent=4)

        except Exception as ex:
            logger.error(f'{url} - {str(ex)} - {str(traceback.format_exc())}')
