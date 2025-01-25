from bs4 import BeautifulSoup
import json
from common import send_req_syphoon,clean_str
import requests
import json
import jsbeautifier
import os
from datetime import datetime
import traceback
 
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

    if product_json['idml'].get('nutritionFacts'):
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
        try:
            for sevice in maybe_addon_service:
                sevice_info = {
                    'service_type'  : sevice['serviceType'],
                    'service_title': sevice['serviceTitle'],
                    'service_subtitle': sevice['serviceSubTitle'],
                } 

                for group in sevice['groups']:
                    if group.get('services',None):
                        services = []
                        for option in group['services']:
                            if option.get('currentPrice'):
                                services.append({
                                    'name' : option['displayName'],
                                    'price' : option['currentPrice']['price']
                                })
                        if services:
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
        except:
            print(traceback.format_exc())
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
    return details



def walmart_seller_parser(offer_json : dict):
    offer_details = {}

    if offer_json.get('data') and offer_json['data'].get('product') and offer_json['data']['product'].get('allOffers'):

        offers = []
        for offer in offer_json['data']['product']['allOffers']:
            offer_details['usItemId'] = offer['usItemId']

            offer_detail = {
                'offerId' : offer['offerId'],
                'sellerDisplayName' : offer['sellerDisplayName'],
                'sellerName' : offer['sellerName'],
                'currentPrice' : offer['priceInfo']['currentPrice']['price'],   
            }

            if offer['priceInfo'].get('wasPrice'):
                offer_detail['wasPrice'] = offer['priceInfo']['wasPrice']['price']
            
            if offer['priceInfo'].get('unitPrice'):
                offer_detail['unitPrice'] = offer['priceInfo']['unitPrice']['price']

            if offer.get('discounts'):
                offer_detail['discounts'] = offer['discounts']

            fullfilments = []
            for opption in offer['fulfillmentOptions']:
                if opption.get('availabilityStatus') == 'IN_STOCK':
                    fullfilment_detail = {
                        'type' : opption['type'],
                        'location_text' : opption['locationText'],
                    }
                    if opption.get('availableQuantity'):
                        fullfilment_detail['available_quantity'] = opption['availableQuantity']

                    if opption.get('maxOrderQuantity'):
                        fullfilment_detail['max_order_quantity'] = opption['maxOrderQuantity']
                    
                    if opption.get('orderLimit'):
                        fullfilment_detail['order_limit'] = opption['orderLimit']

                    fullfilments.append(fullfilment_detail)

            if fullfilments:
                if len(fullfilments) == 1:
                    offer_detail['fullfilment'] = ' | '.join([f"{k}: {v}" for k,v in fullfilments[0].items()])
                else:
                    offer_detail['fullfilments'] = fullfilments

            offers.append(offer_detail)

        offer_details['offers'] = offers

    return offer_details