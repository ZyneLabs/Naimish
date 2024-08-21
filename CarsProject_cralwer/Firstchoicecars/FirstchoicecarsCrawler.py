from common.utils import *
from .FirstchoisecarsScraper import crawl_request_scraper,get_csrf_token
import logging
from bs4 import BeautifulSoup as bs

queue = Queue('Firstchoicecars',connection=redis_conn)

logger = logging.getLogger('FirstchoicecarsCrawler')
logger.setLevel(logging.ERROR)
log_file_name = "FirstchoicecarsCrawler.log"
file_handler = logging.FileHandler(f'./{log_file_name}')
formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
file_handler.setFormatter(formatter)
logger.addHandler(file_handler)

def extract_car_details(text):
    pattern = r"(?P<make>\w+)\s+(?P<model>[\w\- ]+?)\s+(?:(?P<engine_size>\d+(\.\d+)?L \w+)\s+)?(?P<year>\d{4})"
    
    matches = re.match(pattern, text.strip())
    if matches:
        return {
            "make": matches.group("make"),
            "model": matches.group("model").strip(),
            "year": matches.group("year"),
            "engine_size": matches.group("engine_size") or None
        }
    return {
        "make": None,
        "model": None,
        "year": None,
        "engine_size": None
    }

def crawl_urls(start=0):
    try:
        csrf_token = get_csrf_token()
        response = crawl_request_scraper(start,csrf_token)

        if response.json()['success']:
            products = []
            soup = bs(response.json()['data'], 'html.parser')
            for item in soup.select('.col-12.col-sm-6.col-md-6.col-lg-3.c-product__col'):
                product = extract_car_details(item.select_one('a[title]').get('title'))
                product_attrs = item.select('.c-product__attribute__info')
                product_info = {
                    'url':  item.select_one('a[title]').get('href'),
                    'name': item.select_one('a.c-product__name__link').text.strip(),
                    'make' : product['make'],
                    'model' : product['model'],
                    'odometer' : product_attrs[0].text.strip(),
                    'year' : product['year'],
                    'color' :None,
                    'location': None,
                    'engine_size' : product['engine_size'],
                    'trim' : None,
                    'price': item.select_one('.c-product__price').text.replace('AED', '').strip(),
                    'image': item.select_one('.c-product__image').get('src'),
                    'post_datetime' : None,
                    'extra' : {
                        'transmission': product_attrs[1].text.strip(),
                    },
                    'scraped' : 0,
                    'scraped_at' : datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                }

                products.append(product_info)
            if len(products) != 0:
                json.dump(products, open('Firstchoicecars.json', 'a'), indent=4)
                start += 16
                queue.enqueue(crawl_urls, start)

    except Exception as ex:
        logger.error(f'{start} - {str(traceback.format_exc())}')
