from common import *

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

def walmart_parser(product_url,variant_data=False):

    details = {}

    if product_url.startswith('https://www.walmart.ca'):
        param = {'country_code':'ca'}
    else:param = {}

    req = send_req_syphoon(0,'get',product_url,headers=headers,params=param)
    # req = requests.get(product_url,headers=headers)
    soup = BeautifulSoup(req.content, "html.parser")
    

    if not soup.find('script',id="__NEXT_DATA__"):
        return {"message": f"Product Not Found from {product_url}"}
 
    try:
        product_json = json.loads(soup.find('script',id="__NEXT_DATA__").text)['props']['pageProps']['initialData']['data']
    except:
        return {"message": f"Product Not Found from {product_url}"}
    
    details['url'] = product_url
    details['id'] = product_json['product']['id']
    details['usItemId'] = product_json['product']['primaryUsItemId']
    details['name'] = product_json['product']['name']
    
    details['reviews'] = product_json['product'].get('numberOfReviews','')
    details['rating'] = product_json['product'].get('averageRating','')
    
    details['manufactore_id'] = product_json['product'].get('manufacturerProductId','')
    details['brand'] = product_json['product'].get('brand','')
    details['upc'] = product_json['product'].get('upc','')
    
    details['condition'] = product_json['product'].get('conditionType')
    details['stock']= 'Yes' if product_json['product'].get('availabilityStatus') else 'No'

    if product_json['product']['priceInfo'].get('currentPrice'):
        details['currency'] = product_json['product']['priceInfo']['currentPrice']['currencyUnit']
        details['retail_price'] = product_json['product']['priceInfo']['currentPrice']['price']

    if product_json['product']['priceInfo'].get('wasPrice'):
        details['msrp_price'] = product_json['product']['priceInfo']['wasPrice']['price']
        details['discount'] = round((details['msrp_price'] - details['retail_price']) / details['msrp_price'] * 100,2)

    details['images'] = '|'.join([img['url'] for img in product_json['product']['imageInfo']['allImages']])
    
    description = []
    description.append(BeautifulSoup(product_json['product']['shortDescription'],'html.parser').text)

    for i in BeautifulSoup(product_json['idml'].get('longDescription'), 'html.parser').contents:
        if i.name == 'ul':
            description.append(' | '.join([j.text.strip() for j in i.contents if j.text.strip()]))
        elif type(i) is None:
            continue
        else:
            if i.text.strip() :
                description.append(i.text)

    details['description'] = ' '.join(description)

    if product_json['idml'].get('specifications'):
        details['specifications'] = ' | '.join([ f'{i["name"]}: {i["value"]}' for i in product_json['idml']['specifications']])

    if product_json['idml'].get('warranty'):
        details['warranty'] = product_json['idml']['warranty']['information']

    if product_json['idml'].get('ingredients'):
        details['ingredients'] = product_json['idml']['ingredients']['ingredients']['value']

    details['sale_unit'] = product_json['product'].get('salesUnit','Each')
 

    if product_json['product'].get('variantCriteria') and len(product_json['product'].get('variantsMap'))>1: 
        details = get_variant_details(product_json,details)

    if variant_data and details.get('available_variants'):
        available_variant = details.pop('available_variants')
        data = [details]
        for i in available_variant:
            url = f'https://www.walmart.ca/en/ip/{i["id"]}' if product_url.startswith('https://www.walmart.ca') else f'https://www.walmart.com/{i["slug"]}'
            variant_response = walmart_parser(url)
            if not variant_response.get('message',''):
                variant_response.pop('available_variants')
            data.append(variant_response)

        return data

    return details

if __name__ == "__main__":
    with open('walmart.json', 'w',encoding='utf-8') as f:
        json.dump(walmart_parser('https://www.walmart.ca/en/ip/better-homes-gardens-willow-sage-egg-chair-other/6000205126304',True),f,indent=4)

    """
    walmart_parser :
        product_url  :  product url from walmart
        variant_data : False (default) for single product, 
                       True for variant data which returns list of all variants
    """