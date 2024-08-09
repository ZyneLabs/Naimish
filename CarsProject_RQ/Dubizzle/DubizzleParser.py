from common.utils import *


db = client['dubizzle']
product_collection = db['urls']
cache_collection = db['cache']
error_collection = db['error']
car_details_collection = db['car_details']

def check_cache_for(data):
    return cache_collection.find_one(data)

def save_cache_for(url,data):
    
    cache_collection.insert_one(
            {
                'url': url,
                'data': data,
                'updated_at': datetime.now(),
                'data_format': 'html',
                'info_type': 'parse',
                'info_subtype': 'product_parse',
            }
        )



def dubizzle_parser(html):
    soup = BeautifulSoup(html, 'html.parser')
    product_text = soup.find('script',id='__NEXT_DATA__')

    if product_text is None:
        return {'message':'Not Found'}

    similar_product_json = []
    products_json = []
    try:
        page_json = json.loads(product_text.text)['props']['pageProps']['reduxWrapperActionsGIPP']
        for item in page_json:
            if item['type'] == "listings/detailRequest/fulfilled":
                products_json = item['payload']
                
            if item['type'] == "similarAds/getSimilarAdsRequest/fulfilled":
                similar_product_json = item['payload']
    except:
        return {'message':'Not Found'}

    if not products_json:
        return {'message':'Not Found'}
    
    details = {}

    details['id'] = products_json['listing']['listing_id']
    details['name'] = products_json['listing']['name']
    details['posted_at'] = datetime.fromtimestamp(products_json['listing']['posted_timestamp']).strftime('%Y-%m-%d %H:%M:%S')
    details['price'] = products_json['listing']['price']['raw']
    details['currency'] = products_json['listing']['price']['currency']

    details['make'] = products_json['ad_ops']['make']
    details['model'] = products_json['ad_ops']['model']
    details['year'] = products_json['ad_ops']['year']
    details['location'] = products_json['listing']['location']['name']
    details['categories'] = [ {'name':category['name'],'link':'https://dubai.dubizzle.com/'+category['full_slug']} for category in products_json['listing']['categories']]
    details['images'] = products_json['listing']['photos']

    details['specifications'] = {
        item['label'] : item['value']
        for spec in ['primary','secondary'] for item in products_json['listing']['details'][spec]
    }

    details['description'] = products_json['listing']['description']
    
    details['seller_info'] = {
        'name': products_json['lister']['name'],
        'first_name': products_json['lister']['first_name'],
        'last_name': products_json['lister']['last_name'],
        'joined_at': datetime.fromtimestamp(products_json['lister']['joined_timestamp']).strftime('%Y-%m-%d %H:%M:%S'),
        'active_listings_count' : products_json['lister']['active_listings_count'],
        'is_verified_user': products_json['lister']['is_verified_user'],
        'image': products_json['lister']['photo_url']
    }

    if similar_product_json:
        details['similar_products'] = []

        for product in similar_product_json['listings']:
            details['similar_products'].append({
                'name': product['name']['en'],
                'id': product['id'],
                'url': 'https://dubai.dubizzle.com' + product['absolute_url'],
                'price': product['price'],
                'odometer': product['details']['kilometers'],  
            })
    return details


def collect_dubizzle_data():
    for product in product_collection.find({'scraped':0}):
        url = product['url']
        try:
            if car_details_collection.find_one({'url': url}) is not None:
                continue

            cache_data = check_cache_for({'url': url})

            if cache_data is not None:
                html = cache_data['data']
                status = 200
            else:
                req = send_req_syphoon(PROXY_VENDOR, 'GET', url)
                html = req.text
                status = req.status_code
                save_cache_for(url, html)

            data = dubizzle_parser(html)
            data = {'url': url, **data}

            car_details_collection.insert_one(data)

            product_collection.update_one({'url': url}, {'$set': {'scraped': 1}})
            # break
        except Exception as ex:
            error_collection.insert_one(
                {
                    'url': url,
                    'status': status,
                    'runner': 'Dubizzle_product',
                    'error': str(ex),
                    'traceback': traceback.format_exc(),
                }
            )

