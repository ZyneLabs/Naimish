from common.utils import *
from .Dubizzlescraper import dubizzle_scraper
import logging

queue = Queue('Dubizzle',connection=redis_conn)

logger = logging.getLogger('DubizzleCrawler')
logger.setLevel(logging.ERROR)
log_file_name = "DubizzleCrawler.log"
file_handler = logging.FileHandler(f'./{log_file_name}')
formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
file_handler.setFormatter(formatter)
logger.addHandler(file_handler)

def crawl_brands(html):

    main_soup = BeautifulSoup(html, 'html.parser')
    brand_urls = ['https://dubai.dubizzle.com'+a.get('href') for a in main_soup.select('.contentContainer.MuiBox-root a')]
    return brand_urls


def crawl_listing_details(brand_url,page=1):
    if page != 1:
        brand_url +=f'?page={page}'
    try:
       
        req = dubizzle_scraper(brand_url)
        html = req.text
        req.raise_for_status()
        soup = BeautifulSoup(html, 'html.parser')

        page_json = json.loads(soup.find('script',id="__NEXT_DATA__").text)['props']['pageProps']['reduxWrapperActionsGIPP']
        for item in page_json:
            if item['type'] =="listings/fetchListingDataForQuery/fulfilled":
                products_json = item['payload']
                break
        products = []
        if products_json.get('cotdListings',''):
            products_json['cotdListings'].extend(products_json['hits'])
            products_json['hits'] = products_json['cotdListings']

        for product in products_json['hits']:
            product_url = product['absolute_url']['en']

            product_info = {
                'url':  product_url,
                'name': product['name']['en'],
                'make' : product['details']['Make']['en']['value'] if product['details'].get('Make','') else None,
                'model' : product['details']['Model']['en']['value'] if product['details'].get('Model','') else None,
                'odometer' : product['details']['Kilometers']['en']['value'] if product['details'].get('Kilometers','') else None,
                'year' : product['details']['Year']['en']['value'] if product['details'].get('Year','') else None,
                'color' : product['details']['Exterior Color']['en']['value'] if product['details'].get('Exterior Color','') else None,
                'location': ', '.join(product['location_list']['en'][::-1]),
                'engine_size' : product['details']['Engine Capacity (cc)']['en']['value'] if product['details'].get('Engine Capacity (cc)','') else None,
                'trim' : product['details']['Trim']['en']['value'] if product['details'].get('Trim','') else None,
                'price': product['price'],
                'image': ' | '.join([image.replace('?impolicy=lpv','') for image in product['photo_thumbnails']]),
                'post_datetime' : datetime.fromtimestamp(product['added']).strftime('%Y-%m-%d %H:%M:%S'),
                'extra' : {
                    'category': product['category_v2']['names_en'],
                    'is_premium': product['is_premium'],
                    'is_reserved': product['is_reserved'],
                },
                'scraped' : 0,
                'scraped_at' : datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            }
            
            product_info['extra'].update(
                {detail['en']['label']: ', '.join(detail['en']['value']) if isinstance(detail['en']['value'], list) else detail['en']['value'] 
                for detail in product['details'].values() if detail['en']['label'] not in ['Make','Model','Kilometers','Year','Exterior Color','Engine Capacity (cc)','Trim','Price']}
            )
            products.append(product_info)
        
        if len(products) > 0:
            json.dump(products, open('Dubizzle.json', 'a'),indent=4)

        if page == 1:
            last_page = int(soup.select_one('a[data-testid="page-last"]')['href'].split('page=')[-1])
            for page in range(2,last_page):
                queue.enqueue(crawl_listing_details,brand_url, page)

    except Exception as ex:
        print(traceback.print_exc(
            
        ))
        logger.error(f'{brand_url} - {page} - {str(traceback.format_exc())}')

def crawl_urls():
    req = dubizzle_scraper('https://dubai.dubizzle.com/motors/used-cars/')
    brand_urls = crawl_brands(html = req.text)
    for brand_url in brand_urls:
        queue.enqueue(crawl_listing_details, brand_url)
