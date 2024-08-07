from common.utils import *
from .Dubizzlescraper import dubizzle_scraper

queue = Queue('Dubizzle',connection=redis_conn)


db = client['dubizzle']
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
                'data_format': 'html',
                'info_type': 'crawl',
                'info_subtype': 'url_crawl',
            }
        )

def crawl_brands(html):

    main_soup = BeautifulSoup(html, 'html.parser')
    brand_urls = ['https://dubai.dubizzle.com'+a.get('href') for a in main_soup.select('.contentContainer.MuiBox-root a')]
    return brand_urls


def crawl_page(brand_url,page=1):

    if page != 1:
        brand_url +=f'?page={page}'
    try:
        cache_data = check_cache_for({'url': brand_url, 'page': page})
        if cache_data is not None:
            html = cache_data['data']
            status = 200
        else:
            req = dubizzle_scraper(brand_url)
            html = req.text
            status = req.status_code
            req.raise_for_status()
            save_cache_for(brand_url, html, page)
        soup = BeautifulSoup(html, 'html.parser')

        products_soup = soup.select('#listings-container a[type="primary"]')
        products = []
        for product in products_soup:
            product_url = 'https://dubai.dubizzle.com'+product.get('href')
            if product_collection.find_one({'url': product_url}) is not None: continue

            product_info = {
                'url':  product_url,
                'name': product.find('h2').text,
                'price': product.select_one('div[data-testid="listing-price"]').text,
                'currency' : product.select_one('div[data-testid="listing-price"]').previous_sibling.text.strip(),
                'brand' : product.select_one('.heading .heading-text-1').text,
                'model' : product.select_one('.heading .heading-text-2').text,
                'year' : product.select_one('div[data-testid="listing-year"]').text,
                'odometer' : product.select_one('div[data-testid="listing-kms"]').text,
                'steering_side':product.select_one('div[data-testid="listing-steering side"]').text,
                'listing_region':product.select_one('div[data-testid="listing-regional specs"]').text,
                'location':product.select_one('img[alt="location pin icon"]').next_sibling.text.strip(),
                'images': [image.get('src') for image in product.select_one('[data-testid="image-gallery"]').parent.parent.select('img[src]') if '/assets/' not in image.get('src')],
            }
            products.append(product_info)
        
        if len(products) > 0:
            product_collection.insert_many(products)

        if page == 1:
            last_page = int(soup.select_one('a[data-testid="page-last"]')['href'].split('page=')[-1])
            for page in range(2, last_page):
                queue.enqueue(crawl_page, brand_url, page)

    except Exception as ex:
        error_collection.insert_one(
            {
                'url': brand_url,
                'page': page,
                'status': status,
                'error': str(ex),
                'traceback': traceback.format_exc(),
            }
        )

def crawl_listing_details(brand_url,page=1):
    if page != 1:
        brand_url +=f'?page={page}'
    try:
        cache_data = check_cache_for({'url': brand_url, 'page': page})
        if cache_data is not None:
            html = cache_data['data']
            status = 200
        else:
            req = dubizzle_scraper(brand_url)
            html = req.text
            status = req.status_code
            req.raise_for_status()
            save_cache_for(brand_url, html, page)
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
            if product_collection.find_one({'url': product_url}) is not None: continue

            product_info = {
                'url':  product_url,
                'name': product['name']['en'],
                'price': product['price'],
                'details': {detail['en']['label']:detail['en']['value']  for detail in product['details'].values()},
                'location': ', '.join(product['location_list']['en'][::-1]),
                'images': [image.replace('?impolicy=lpv','') for image in product['photo_thumbnails']],
                'category': product['category_v2']['names_en'],
                'is_premium': product['is_premium'],
                'is_reserved': product['is_reserved'],
            }
            products.append(product_info)
        
        if len(products) > 0:
            product_collection.insert_many(products)

        if page == 1:
            last_page = int(soup.select_one('a[data-testid="page-last"]')['href'].split('page=')[-1])
            for page in range(2,last_page):
                queue.enqueue(crawl_page, brand_url, page)

    except Exception as ex:
        error_collection.insert_one(
            {
                'url': brand_url,
                'page': page,
                'status': status,
                'error': str(ex),
                'traceback': traceback.format_exc(),
            }
        )

def crawl_duizle():
    req = dubizzle_scraper('https://dubai.dubizzle.com/motors/used-cars/')
    brand_urls = crawl_brands(html = req.text)
    print(brand_urls)
    for brand_url in brand_urls:
        queue.enqueue(crawl_listing_details, brand_url)
