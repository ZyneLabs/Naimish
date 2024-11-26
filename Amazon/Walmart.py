from bs4 import BeautifulSoup
import json
from common import send_req_syphoon,findall_text_between,clean_str,MokeRequest
import requests
import json
import jsbeautifier
import os
from datetime import datetime
    
 
def walmart_scraper(url,filename:str=None):
    if filename:
        # kepping html for a day
        date = datetime.now().strftime("%Y%m%d")
        os.makedirs(date,exist_ok=True)
        
        try:
            with open(f'{date}/{filename}.html','r',encoding='utf-8') as f:
                html = f.read()
                req = MokeRequest(status_code=200,text=html)
        except:
            try:
                req = send_req_syphoon(0,'get',url)
                # req.raise_for_status()
                html = req.text
                with open(f'{date}/{filename}.html','w',encoding='utf-8') as f:
                    f.write(html)
            except Exception as ex:
                return {'message':f'Error in sending request {url}'}
    else:
        try:
            req = send_req_syphoon(0,'get',url)
            # req.raise_for_status()
            # html = req.text
        except Exception as ex:
            return {'message':f'Error in sending request {url}'}
        
    return req

def get_variant_details(product_json,details):
    
    seleced_variant = product_json['product']['selectedVariantIds']
    details['seleced_variant'] = {}
    details['variants'] = {}

    for variant in product_json['product']['variantCriteria']:
        variant_name = variant['name']
        values  = []
        for option in variant['variantList']:
            if option['id'] in seleced_variant:
                details['seleced_variant'][variant_name] = option['name']
            values.append(option['name'])
        details['variants'][variant_name] = values

    details['available_variants'] = [{
            "id": pid,
            "usItemId": product_json['product']['variantsMap'][pid]['usItemId'],
            "slug" : product_json['product']['variantsMap'][pid]['productUrl']
        }
        for pid in product_json['product']['variantsMap']
        if pid != product_json['product']['id'] and pid != product_json['product']['usItemId']]

    return details

def get_review_details(review_json):
    if review_json:
        review_info = {
            "title": review_json['reviewTitle'],
            "text": review_json['reviewText'],
            "rating": review_json['rating'],
            "positive_feedback": review_json['positiveFeedback'],
            "negative_feedback": review_json['negativeFeedback'],
            "review_submission_time": review_json['reviewSubmissionTime'],
            "user_nickname": review_json['userNickname'],
        }

        if review_json['badges']:
            review_info['customer_type'] = [badge['id'] for badge in review_json['badges']] 

        if review_json['media']:
            review_info['media'] = [{'type' : media['mediaType'] ,'url':media['normalUrl']} for media in review_json['media']]

        return review_info

def get_reviews(reviews_json):
    if reviews_json and reviews_json['roundedAverageOverallRating']:
        reviews_info = {}
        reviews_info['average_rating'] = reviews_json['roundedAverageOverallRating']
        reviews_info['rating_breakdown'] = [
            {'star' : 1 ,'count':reviews_json['ratingValueOneCount'],'percent':reviews_json['percentageOneCount']},
            {'star' : 2 ,'count':reviews_json['ratingValueTwoCount'],'percent':reviews_json['percentageTwoCount']},
            {'star' : 3 ,'count':reviews_json['ratingValueThreeCount'],'percent':reviews_json['percentageThreeCount']},
            {'star' : 4 ,'count':reviews_json['ratingValueFourCount'],'percent':reviews_json['percentageFourCount']},
            {'star' : 5 ,'count':reviews_json['ratingValueFiveCount'],'percent':reviews_json['percentageFiveCount']},
            ]
        
        if reviews_json['aspects']:
            reviews_info['top_mentions'] = [
                {'name':aspect['name'],'count':aspect['snippetCount'],'percent':aspect['score']}
                for aspect in reviews_json['aspects']
            ]

        reviews_info['total_reviews'] = reviews_json['totalReviewCount']

        if reviews_json['topNegativeReview']:
            reviews_info['top_negative_reviews'] = get_review_details(reviews_json['topNegativeReview'])

        if reviews_json['topPositiveReview']:
            reviews_info['top_positive_reviews'] = get_review_details(reviews_json['topPositiveReview'])

        if reviews_json['customerReviews']:
            reviews_info['top_reviews'] = [get_review_details(review) for review in reviews_json['customerReviews']]

        return reviews_info
    return {}
def get_variants(product_json):
    if product_json['product'].get('variantCriteria',''):
        variants = []
        current_selection = {}

        for variant in product_json['product']['variantCriteria']:
            options = []
            for option in variant['variantList']:
                opt = {'name': option['name']}
                if option.get('swatchImageUrl',''):
                    opt['image'] = option['swatchImageUrl']
                
                if option['selected']:
                    current_selection.update({variant["name"]:option["name"]})
                    
                options.append(opt)

            variants.append({
                'name': variant['name'],
                'options': options
            })

        available_variants= [{
            "id": pid,
            "usItemId": product_json['product']['variantsMap'][pid]['usItemId'],
            "url" : product_json['product']['variantsMap'][pid]['productUrl'] or f"/ip/{product_json['product']['variantsMap'][pid]['usItemId']}",
            "availability_status" : product_json['product']['variantsMap'][pid]['availabilityStatus'] 
        }
        for pid in product_json['product']['variantsMap']
        if pid != product_json['product']['id'] and pid != product_json['product']['usItemId']]
        
        
        if available_variants:
            return {'variants': variants, 'current_selection': current_selection, 'available_variants': available_variants}

def walmart_parser(product_url,html):
    soup = BeautifulSoup(html, "html.parser")
    if not soup.find('script',id="__NEXT_DATA__"):
            return {"message": f"Product Not Found from {product_url}"}
    
    try:
        product_json = json.loads(soup.find('script',id="__NEXT_DATA__").text)['props']['pageProps']['initialData']['data']
    except:
        return {"message": f"Product Not Found from {product_url}"}
    
    details = {}

    details['request_url'] = product_url
    # search_info
    maybe_location = product_json['product'].get('location','')
    if maybe_location:
        details['search_info'] = {
            'location' :{
                "postal_code": maybe_location['postalCode'],
                "province_code"  : maybe_location['stateOrProvinceCode'],
                "city" : maybe_location['city'],
                "store_id" : maybe_location['storeIds'][0]
            }
        }

    product  = {}
    product['url'] = soup.find('link',rel="canonical")['href']
    product['us_item_id'] = product_json['product']['usItemId']
    product['product_id'] = product_json['product']['id']
    product['title']  = product_json['product']['name']
    product['upc'] = product_json['product'].get('upc','')
    product['condition_type'] = product_json['product'].get('conditionType') or 'New'
    product['short_description_html'] = product_json['product'].get('shortDescription','')
    product['short_description_text'] = clean_str(BeautifulSoup(product_json['product'].get('shortDescription',''), "html.parser").text)
    product['long_description_html'] = product_json['idml'].get('longDescription','')
    product['long_description_text'] = clean_str(' | '.join([li.text for li in BeautifulSoup(product_json['idml'].get('longDescription',''), "html.parser").find_all('li')]))


    # categories
    try:
        product['categories'] = product_json['product']['category']['path']
       
        start_index = 1 if product['categories'] and product['categories'][0].get('name') == 'Home' else 0
        for idx in range(3):
            category_index = start_index + idx
            if category_index < len(product['categories']):
                product[f'category_{idx + 1}'] = product['categories'][category_index].get('name', '')
                
    except:
        pass
    

    product['specifications'] = {i["name"] : i["value"] for i in product_json['idml']['specifications']}

    if product_json['idml'].get('productHighlights',''):
        product['product_highlights'] = product_json['idml']['productHighlights']

    if product_json['idml'].get('warranty'):
        product['warranty'] = product_json['idml']['warranty']['information']

    if product_json['idml'].get('directions',''):
        product['directions'] = product_json['idml']['directions']

    if product_json['idml'].get('indications',''):
        product['indications'] = product_json['idml']['indications']

    if product_json['idml'].get('ingredients'):
        product['ingredients'] =[ product_json['idml']['ingredients'][indgredient] for indgredient in product_json['idml']['ingredients'] if product_json['idml']['ingredients'][indgredient]]

    if product_json['idml'].get('nutritionFacts') and any(product_json['idml']['nutritionFacts'].values()):
        product['nutrition_facts'] = product_json['idml']['nutritionFacts']

    if product_json['idml'].get('warnings'):
        product['warnings'] = product_json['idml']['warnings']

    product['manufacture_number'] = product_json['product'].get('manufacturerProductId','')
    product['product_type_id']  = product_json['product'].get('productTypeId','')
    product['product_type'] = product_json['product'].get('type','')
    product['brand'] = product_json['product'].get('brand','')

    product['price_info'] = {
         "current_price" : product_json['product']['priceInfo']['currentPrice'],
    }

    if product_json['product']['priceInfo'].get('unitPrice',''):
        product['price_info']['unit_price'] = product_json['product']['priceInfo']['unitPrice']

    if product_json['product']['priceInfo'].get('wasPrice',''):
        product['price_info']['was_price'] = product_json['product']['priceInfo']['wasPrice']
        product['price_info']['saving_amount'] = product_json['product']['priceInfo']['savingsAmount']['amount']

    product['min_quantity'] = product_json['product'].get('orderMinLimit','')
    product['max_quantity'] = product_json['product'].get('orderLimit','')

    product['in_stock'] = True if product_json['product']['availabilityStatus']=='IN_STOCK' else False 
    product['sale_unit'] = product_json['product'].get('salesUnit','EACH')
 
    product['images'] = [img['url'] for img in product_json['product']['imageInfo']['allImages']]

    if product_json['idml'].get('videos',''):
        videos = []
        for video in product_json['idml']['videos']:
            videos.append(video['versions']['large'])
        if videos:
            product['videos'] = videos

    product['offer_id'] = product_json['product'].get('offerId','')
    product['offer_type']  = product_json['product'].get('offerType','')
    
    product['seller_info'] = {
        'seller_id' : product_json['product']['sellerId'],
        'catalog_seller_id': product_json['product'].get('catalogSellerId',''),
        'seller_display_name': product_json['product']['sellerDisplayName'],
        'seller_name': product_json['product']['sellerName'],
        'seller_review_count' : product_json['product']['sellerReviewCount'],
        'seller_rating': product_json['product']['sellerAverageRating']
    }

    maybe_fulfilment= product_json['product']['fulfillmentLabel']
    if maybe_fulfilment:
        product['fulfilment_info'] ={
            'method' : maybe_fulfilment[0]['fulfillmentMethod'],
            'message' : maybe_fulfilment[0]['message'],
            'fulfillment_text' : maybe_fulfilment[0]['fulfillmentText'],
            'location_text' : maybe_fulfilment[0]['locationText']
        }

    product['delivery_date'] = product_json['product']['shippingOption'].get('deliveryDate','')
    
    if product_json['product'].get('pickupOption',''):
        product['pickup_info'] = {
            'availability_status' : product_json['product']['pickupOption']['availabilityStatus'],
            'pickup_type' : product_json['product']['pickupOption']['accessTypes']
        }
    maybe_addon_service = product_json['product'].get('addOnServices','')
    if maybe_addon_service:
        addon_services = []
        for sevice in maybe_addon_service:
            sevice_info = {
                'service_type'  : sevice['serviceType'],
                'service_title': sevice['serviceTitle'],
                'service_subtitle': sevice['serviceSubTitle'],
            } 

            for group in sevice['groups']:
                if group.get('services',''):
                    services = []
                    for option in group['services']:
                        services.append({
                            'name' : option['displayName'],
                            'price' : option['currentPrice']['price']
                        })

                    sevice_info['service_options'] = services
                if group.get('nearByStores',''):
                    nearby_stores = []
                    for store in group['nearByStores']['nodes']:
                        nearby_stores.append({
                            'name' : store['displayName'],
                            'distance' : store['distance']
                        })

                    sevice_info['nearby_stores'] = nearby_stores
            addon_services.append(sevice_info)

        product['addon_services'] = addon_services
    maybe_variant = get_variants(product_json)

    if maybe_variant:
        product['current_selection'] = maybe_variant['current_selection']
        product['variants_options'] = maybe_variant['variants']
        product['available_variants'] = maybe_variant['available_variants']

    if product_json['product']['badges']['flags']:
        product['badges'] = [{
           'id' : badge['id'],
           'key' : badge['key'],
           'name' : badge['text']
        }
           for badge in product_json['product']['badges']['flags']
        ]

    reviews = get_reviews(product_json['reviews'])

    if reviews:
        product['reviews_results'] = reviews

    details['product_info'] = product
    # 
    #  Having changes into headers and cookies for graphql request
    #  without cookies it will not work
    # 
    # seller_offers
    # maybe_webpack_link = get_webpack_link(html)
    # if maybe_webpack_link:
    #     maybe_marketplace_link = get_marketplace_link(maybe_webpack_link)
    #     if maybe_marketplace_link:
    #         maybe_graphql_hash = get_graphql_hash(maybe_marketplace_link)
    #         if maybe_graphql_hash:
    #             details['seller_offers'] = get_seller_offer(product['us_item_id'],maybe_graphql_hash)

    return details


def get_webpack_link(html):
  
    soup = BeautifulSoup(html, 'html.parser')

    for script in soup.select('script[src]'):
        if 'webpack-' in script.get('src'):
            return script.get('src')
    
def get_marketplace_link(webpack_link):

    js_file = webpack_link.split('/')[-1]
    prefix_url = webpack_link.replace(js_file,'')
    try:
        with open(js_file, 'rb') as f:
            raw_js_text = f.read().decode('utf-8')
    except:
        js_response = walmart_scraper(webpack_link)
        with open(js_file, 'wb') as f:
            f.write(js_response.content)
        raw_js_text = js_response.content.decode('utf-8')
    
    raw_js = jsbeautifier.beautify(raw_js_text)
    maybe_token = findall_text_between(raw_js,'node_modules_.pnpm_@graphql-tools+schema@6.2.4_graphql@15.5_node_modules_@graphql-tools_schema_index.esm",',': "marketplace_all-sellers-panel"')
    if maybe_token:
        token = clean_str(maybe_token[0])
        maybe_hash = findall_text_between(raw_js,f'{token}:',",")
        if maybe_hash:
            hash = clean_str(maybe_hash[1]).replace('"','')
            return f'{prefix_url}/marketplace_all-sellers-panel.{hash}.js'
        

def get_graphql_hash(marketplace_link):
    marketplace_file  = marketplace_link.split('/')[-1]
    try:
        with open(marketplace_file, 'rb') as f:
            raw_js_text = f.read().decode('utf-8')
    except:
        marketplace_response = walmart_scraper(marketplace_link)
        with open(marketplace_file, 'wb') as f:
            f.write(marketplace_response.content)

        raw_js_text = jsbeautifier.beautify(marketplace_response.content.decode('utf-8'))
        
    raw_js = jsbeautifier.beautify(raw_js_text)
    with open('raw.js', 'w') as f:
        f.write(raw_js)
    maybe_hashs = findall_text_between(raw_js,'hash','},')
    if maybe_hashs:
        return clean_str(maybe_hashs[0].replace('"','').replace(':',''))
    

def get_seller_offer(item_number,hash):

    x_headers = {
        'accept': 'application/json',
        'accept-language': 'en-US',
        'content-type': 'application/json',
        'cookie': 'locGuestData=eyJpbnRlbnQiOiJTSElQUElORyIsImlzRXhwbGljaXQiOmZhbHNlLCJzdG9yZUludGVudCI6IlBJQ0tVUCIsIm1lcmdlRmxhZyI6ZmFsc2UsImlzRGVmYXVsdGVkIjp0cnVlLCJwaWNrdXAiOnsibm9kZUlkIjoiMzA4MSIsInRpbWVzdGFtcCI6MTcxOTgxMDYyMTM5Nywic2VsZWN0aW9uVHlwZSI6IkRFRkFVTFRFRCJ9LCJzaGlwcGluZ0FkZHJlc3MiOnsidGltZXN0YW1wIjoxNzE5ODEwNjIxMzk3LCJ0eXBlIjoicGFydGlhbC1sb2NhdGlvbiIsImdpZnRBZGRyZXNzIjpmYWxzZSwicG9zdGFsQ29kZSI6Ijk1ODI5IiwiZGVsaXZlcnlTdG9yZUxpc3QiOlt7Im5vZGVJZCI6IjMwODEiLCJ0eXBlIjoiREVMSVZFUlkiLCJ0aW1lc3RhbXAiOjE3MjIyNDYyNTkxNTQsImRlbGl2ZXJ5VGllciI6bnVsbCwic2VsZWN0aW9uVHlwZSI6IkxTX1NFTEVDVEVEIiwic2VsZWN0aW9uU291cmNlIjpudWxsfV0sImNpdHkiOiJTYWNyYW1lbnRvIiwic3RhdGUiOiJDQSJ9LCJwb3N0YWxDb2RlIjp7InRpbWVzdGFtcCI6MTcxOTgxMDYyMTM5NywiYmFzZSI6Ijk1ODI5In0sIm1wIjpbXSwidmFsaWRhdGVLZXkiOiJwcm9kOnYyOmIyODZiNzg4LTc2MTctNDA2Zi05ZmVhLTM1ZGY4ZTQ2OWI3ZiJ9;',
        'downlink': '2.25',
        'dpr': '1',
        'priority': 'u=1, i',
        'referer': 'https://www.walmart.com/ip/ATD-Tools-Utility-Cut-Off-Tool-with-Guard-2139/46639362',
        'sec-ch-ua': '"Not/A)Brand";v="8", "Chromium";v="126", "Google Chrome";v="126"',
        'sec-ch-ua-mobile': '?0',
        'sec-ch-ua-platform': '"Linux"',
        'sec-fetch-dest': 'empty',
        'sec-fetch-mode': 'cors',
        'sec-fetch-site': 'same-origin',
        'tenant-id': 'elh9ie',
        'traceparent': '00-4b8ea95cfefe93cc5ad093a56ad473fa-95936d7561c309cc-00',
        'user-agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36',
        'wm_mp': 'true',
        'wm_page_url': 'https://www.walmart.com/ip/ATD-Tools-Utility-Cut-Off-Tool-with-Guard-2139/46639362',
        'wm_qos.correlation_id': 'yXktS6Zz4zouGa3Us_4YMDkSWm7vk8REEDJk',
        'x-apollo-operation-name': 'GetAllSellerOffers',
        'x-enable-server-timing': '1',
        'x-latency-trace': '1',
        'x-o-bu': 'WALMART-US',
        'x-o-ccm': 'server',
        'x-o-correlation-id': 'yXktS6Zz4zouGa3Us_4YMDkSWm7vk8REEDJk',
        'x-o-gql-query': 'query GetAllSellerOffers',
        'x-o-mart': 'B2C',
        'x-o-platform': 'rweb',
        'x-o-platform-version': 'us-web-1.152.0-e89110474d001fa520916891177bf289432c7c41-072923',
        'x-o-segment': 'oaoh',
    }
    params = {
        'variables': '{"itemId":"'+item_number+'","isSubscriptionEligible":true}',
    }
    payload={
        'headers':x_headers
    }

    req = send_req_syphoon(2,'get',f'https://www.walmart.com/orchestra/home/graphql/GetAllSellerOffers/{hash}',params=params,payload=payload)
    return req.json()

if __name__ == '__main__':
    from rich.pretty import pprint
    with open('disc_product.html','r') as f:
        html = f.read()
    details = walmart_parser('https://www.walmart.com/ip/Great-Value-Milk-Whole-Vitamin-D-Gallon-Plastic-Jug/10450114',html)
    pprint(details)
