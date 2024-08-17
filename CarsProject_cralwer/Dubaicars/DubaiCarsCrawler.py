from common.utils import *
import logging

redis_conn = Redis()
queue = Queue('Dubaicars',connection=redis_conn)

logger = logging.getLogger('DubaicarsCrawler')
logger.setLevel(logging.ERROR)
log_file_name = "DubaicarsCrawler.log"
file_handler = logging.FileHandler(f'./{log_file_name}')
formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
file_handler.setFormatter(formatter)
logger.addHandler(file_handler)


def crawl_products(maker_id,page):
    try:
        main_url= f'https://www.dubicars.com/search?c=new-and-used&ma={maker_id}&mo=0&b=&set=&eo=export-only&stsd=&cr=USD&cy=&co=&s=&gi=&f=&g=&l=&st='
       
        res = send_req_syphoon(PROXY_VENDOR,'get',main_url+f'&page={page}')
        res.raise_for_status()
        data = res.text

        soup = BeautifulSoup(data, 'html.parser')
        maybe_products_soup = soup.select('section li.serp-list-item')
        if maybe_products_soup:
            product_urls = []

            for product_soup in maybe_products_soup:
                product_url = product_soup.find('a').get('href')

                product_details = json.loads(product_soup.get('data-mixpanel-detail'))
                product_urls.append({
                    'url': product_url,
                    'name': product_soup.select_one('.detail a').text.strip(),
                    'make' : product_details.get('item_make',None),
                    'model' : product_details.get('item_model',None),
                    'odometer' : product_details.get('item_mileage',None),
                    'year' : product_details.get('item_year',None),
                    'color' : product_details.get('item_exterior_color',None),
                    'location' : product_details.get('item_location',None),
                    'engine_size' : None,
                    'trim' : None,
                    'price' : product_details.get('item_export_price',None),
                    'image' : 'https:'+product_soup.select_one(' .image-container img').get('src'),
                    'post_datetime' : None,
                    'extra' : {
                        'currency':'USD',
                        'specs': product_details.get('item_specs',None),
                        'condition': product_details.get('item_condition',None),
                        'interior_color': product_details.get('item_interior_color',None),
                        'fuel_type': product_details.get('item_fuel_type',None),
                        'transmission': product_details.get('item_gearbox',None),
                        'body_type': product_details.get('item_body_type',None),
                        'seller_name': product_details.get('item_seller_name',None),
                        'seller_type': product_details.get('item_seller_type',None),
                    },
                    'scraped' : 0,
                    'scraped_at' : datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                })


            if len(product_urls) != 0:
                json.dump(product_urls, open('Dubaicars.json', 'a'), indent=4)

            if page == 1 == soup.find('a',attrs={"rel":"next"}):
                total_pages = int(soup.find('a',attrs={"rel":"next"}).parent.find_previous('li').find('a').text)

                for page in range(1,total_pages+1):
                    queue.enqueue(crawl_products, (maker_id,page))

    except Exception as ex:
        logger.error(f'{maker_id} - {page} - {str(traceback.format_exc())}')

def crawl_urls():
    res = send_req_syphoon(PROXY_VENDOR,'get','https://www.dubicars.com/')
    main_soup = BeautifulSoup(res.content, 'html.parser')
    makers = main_soup.find('input',attrs={"name":"ma"}).parent.find_all('li')
    for i in makers[1:]:
        queue.enqueue(crawl_products,i.get("data-value"),1)

        