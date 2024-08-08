from common.utils import *


db = client['opensooq']
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



def opensooq_parser(html):
    soup = BeautifulSoup(html, 'html.parser')
    product_text = soup.find('script',id='__NEXT_DATA__')

    if product_text is None:
        return {'message':'Not Found'}

    page_json = json.loads(product_text.text)['props']['pageProps']
    product_json = page_json['postData']['listing']
    details = {}

    details['url'] = product_json['post_url']
    details['id'] = product_json['listing_id']
    details['title'] = product_json['title']
    details['price'] = product_json['price']['price']
    details['currency'] = product_json['price']['currencies'][0]['symbol_label']
    details['publish_date'] = product_json['publish_date']

    category_soup = soup.select('#breadcrumbs a')

    if category_soup:
        details['category'] = []
        details['category_flat'] = []

        for category in category_soup:
            details['category'].append({
                'name': category.text.replace('/','').strip(),
                'link': 'https://ae.opensooq.com/' + category['href']
            })

            details['category_flat'].append(category.text)

        details['category_flat'] = ''.join(details['category_flat'])

    details['description'] = product_json['masked_description']
    details['images'] = page_json['seoPage']['ogImages']
    details['informations'] = {
        item['field_label'] : item['reporting_value_label'] 
        for item in product_json['basic_info'] if item.get('reporting_value_label','')
    }
    details['location'] = {
        'text' : product_json['city']['name_english'] +' - '+product_json['neighborhood']['name_english'],
        'link': f'https://ae.opensooq.com/en/find?PostSearch[cityId]={product_json["city"]["id"]}&PostSearch[neighborhood_id]={product_json["neighborhood"]["id"]}'
    }

    if product_json.get('post_map',''):
        details['location']['map'] = f'https://www.google.com/maps/search/?api=1&query={product_json["post_map"]["lat"]},{product_json["post_map"]["lng"]}&zoom=15'

    if product_json.get('seller',''):
        details['seller'] = {
            'id': product_json['seller']['id'],
            'is_authorised_seller': product_json['seller']['authorised_seller'],
            'name' : product_json['seller']['full_name'],
            'link': product_json['seller']['member_link'],
            'profile_picture' : product_json['seller']['profile_picture'],
            'rating' : product_json['seller']['rating_avg'],
            'reviews_count' : product_json['seller']['number_of_ratings'],
            'join_date' : product_json['seller']['member_since'],
            'response_time': product_json['seller']['response_time']
        }

    if product_json.get('similar_recommended','') and product_json['similar_recommended'].get('blocks',''):

        for block in product_json['similar_recommended']['blocks']:
            block_name = block['label'].replace(' ','_')
            details[block_name] = []

            for item in block['items']:
                product = {
                    'id': item['post_id'],
                    'title': item['title'],
                    'url': 'https://ae.opensooq.com'+item['postUrl'],
                    'highlights': item['highlights'],
                    'location': item['city_label'],
                    'nhood' : item['nhood_reporting'],
                    'price': item['price_amount'],
                    'currency': item['localized_currency'],
                    'image': item['first_image_uri']

                    }

                details[block_name].append(product)

    return details


def collect_opensooq_data():
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

            data = opensooq_parser(html)
            car_details_collection.insert_one(data)

            product_collection.update_one({'url': url}, {'$set': {'scraped': 1}})
        except Exception as ex:
            error_collection.insert_one(
                {
                    'url': url,
                    'status': status,
                    'runner': 'Opensooq_product',
                    'error': str(ex),
                    'traceback': traceback.format_exc(),
                }
            )

