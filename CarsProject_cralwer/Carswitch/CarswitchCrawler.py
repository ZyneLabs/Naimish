from common.utils import *
import logging

logger = logging.getLogger('CarswitchCrawler')
logger.setLevel(logging.ERROR)
log_file_name = "CarswitchCrawler.log"
file_handler = logging.FileHandler(f'./{log_file_name}')
formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
file_handler.setFormatter(formatter)
logger.addHandler(file_handler)
redis_conn = Redis()
queue = Queue('Carswitch',connection=redis_conn)


def extract_car_details(car_description):
    make_pattern = r"(?P<make>\w+)"
    model_pattern = r"(?P<model>[A-Za-z0-9\s]+?)"
    engine_pattern = r"(?P<engine_size>\d+\.\d+L)"

    pattern = re.compile(
        fr"^{make_pattern}\s+{model_pattern}\s+{engine_pattern}"
    )
    
    match = pattern.search(car_description)
    
    if match:
        make = match.group('make')
        model = match.group('model').strip() if match.group('model') else None
        engine_size = match.group('engine_size') if match.group('engine_size') else None
        return make, model, engine_size
    else:
        return None, None, None
 
def save_urls_from_html(html):
    soup = BeautifulSoup(html, 'lxml')
    products = []

    for i in soup.select('section#main-listing-div div.pro-item'):
        url = 'https://carswitch.com'+i.find('a').get('href')
        name = i.select_one('.title h2').text.strip()
        make, model, engine_size = extract_car_details(name)
        products.append(
        {
            'url' : url,
            'name': name,
            'make' : make,
            'model' : model,
            'odometer' : i.select_one('.item.mileage').text.strip(),
            'year' : i.select_one('.item.year').text.strip(),
            'color' : None,
            'location' : None,
            'engine_size' : engine_size,
            'trim' : None,
            'price' : i.select_one('.discounted-price').text.strip(),
            'image' : 'https:'+i.select_one('.image-wrapper img').get('data-src'),
            'post_datetime' : None,
            'extra' : {
                'specs': i.select_one('.specs span').text.strip(),
            },
            'scraped' : 0,
            'scraped_at' : datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
        }
        )
    
    if len(products) != 0:
        json.dump(products, open('Carswitch.json', 'a'), indent=4)

def crawl_page(category_url,page ):
    try:
        res = send_req_syphoon(PROXY_VENDOR, 'GET', category_url+f'?page={page}')   
        res.raise_for_status()
        data = res.text
        save_urls_from_html(data)

    except Exception as ex:
        logger.error(f'{category_url} - {page} - {str(traceback.format_exc())}')
        
def crawl_urls():
    res = send_req_syphoon(PROXY_VENDOR, 'GET', 'https://carswitch.com/uae/used-cars/search')
    soup = BeautifulSoup(res.text, 'html.parser')
   
    total_page = int(soup.select_one('div.page-number_holder a:last-child').text)
    save_urls_from_html(res.text)

    for page in range(2,total_page+1):
        queue.enqueue(crawl_page, 'https://carswitch.com/uae/used-cars/search',page)