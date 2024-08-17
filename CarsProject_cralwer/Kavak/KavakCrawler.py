from common.utils import *
import logging

logger = logging.getLogger('KavakCrawler')
logger.setLevel(logging.ERROR)
log_file_name = "KavakCrawler.log"
file_handler = logging.FileHandler(f'./{log_file_name}')
formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
file_handler.setFormatter(formatter)
logger.addHandler(file_handler)

redis_conn = Redis()
queue = Queue('Kavak',connection=redis_conn)

    
def save_urls_from_html(soup):
    products = []

    products_json = json.loads(soup.find('script',id="serverApp-state").text.replace('&q;','"'))['engine-main-state']['grid']['cars']

    for product in products_json:

        products.append({
            'url': product['url'],
            'name': product['name'],
            'make' : product['make'],
            'model' : product['model'],
            'odometer' : product['km'],
            'year' : product['year'],
            'color' : product['color'],
            'location' : product['regionName'],
            'engine_size' : None,
            'trim' : product['trim'],
            'price' : product['price'].replace('AED','').strip(),
            'image' : product['image'],
            'post_datetime' : None,
            'extra' : {
                'transmission' : product['transmission'],
            },
            'scraped' : 0,
            'scraped_at' : datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
        })
    if len(products) != 0:
       json.dump(products, open('Kavak.json', 'a'), indent=4)

def crawl_urls(page=0):
    try:
        req_url = 'https://www.kavak.com/ae/preowned'
        if page != 0:
            req_url += f'?page={page}'
       
        res = send_req_syphoon(PROXY_VENDOR, 'GET', req_url)
        status = res.status_code
        res.raise_for_status()
        soup = BeautifulSoup(res.text, 'lxml') 
        
        save_urls_from_html(soup)

        total_page = int(soup.select_one('div.results span.total').text)

        for page in range(1, total_page+1):
            queue.enqueue(crawl_urls, page)
            
    except Exception as ex:
        logger.error(f'{page} - {str(traceback.format_exc())}')