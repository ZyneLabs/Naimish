from common.utils import send_req_syphoon,PROXY_VENDOR,redis_conn
import json
import logging
from datetime import datetime
import traceback
from rq import Queue
from bs4 import BeautifulSoup
from datetime import datetime


logger = logging.getLogger('AltayermotorsCrawler')
logger.setLevel(logging.ERROR)
log_file_name = "AltayermotorsCrawler.log"
file_handler = logging.FileHandler(f'./{log_file_name}')
formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
file_handler.setFormatter(formatter)
logger.addHandler(file_handler)

queue = Queue('Altayermotors',connection=redis_conn)


def get_products(brand_url,page_id=None,brand_name=None,page=1):

    try:
        if page_id is None:
            req = send_req_syphoon(PROXY_VENDOR,'get',brand_url)
            soup = BeautifulSoup(req.text, 'html.parser')
            page_id = soup.select_one('[data-page-id]').attrs.get('data-page-id')
            brand_name = soup.select_one('[data-make]').attrs.get('data-make').lower()

        request_url = f'https://www.altayermotors.com/{brand_name}/ajax/stock-listing/get-items/pageId/{page_id}/ratio/4_3/taxBandImageLink//taxBandImageHyperlink//imgWidth/440/?page={page}'
        resp = send_req_syphoon(PROXY_VENDOR,'get',request_url)
        resp.raise_for_status()
        data = resp.json()

        if page==1:
            total_pages = data['count']//24

            for i in range(2,total_pages+1):
                queue.enqueue(get_products,brand_url,page_id=page_id,brand_name=brand_name,page=i)

        products =  [
            {'url' :'https://www.altayermotors.com/'+i['url'],
                'name' : i['link_title'],
                'make': i['make'],
                'model':i['model'],
                'odometer':i['mileage'],
                'year':i['model_year'],
                'color':i['colour'],
                'location':i['location_name'],
                'engine_size':i['engine_size'],
                'trim':None,
                'price': i['price_now_raw'],
                'image':i.get('image',''),
                'post_datetime':None,
                'extra':{
                    'fuel_type':i.get('fuel',''),
                    'transmission':i.get('transmission',''),
                    'vin_number':i.get('vin',''),
                    'interior_color':i.get('interior_colour',''),
                    'exterior_color':i.get('exterior_colour',''),
                    'body_type':i.get('bodystyle',''),
                    'interior_trim':i.get('interior_trim',''),
                },
                'scraped':0,
                'scraped_at': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                }
            for i in data.get('vehicles') 
        ]

        if len(products) > 0:
            json.dump(products, open('Altayermotors.json', 'a'), indent=4)
        

    except:
        logger.error(f'{brand_url} - {str(traceback.format_exc())}')



def crawl_urls():
    
    brand_url = 'https://www.altayermotors.com/stock/'
    req = send_req_syphoon(PROXY_VENDOR,'get',brand_url)
    soup = BeautifulSoup(req.text, 'html.parser')

    brands = [a.get('href') for a in soup.select('.list-item.contentsection.stock.listing .cycle a')]

    for brand in brands:
        queue.enqueue(get_products,brand_url=brand)
