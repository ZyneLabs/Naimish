from bs4 import BeautifulSoup,MarkupResemblesLocatorWarning
import json
import warnings

warnings.filterwarnings("ignore", category=MarkupResemblesLocatorWarning)

def clean_data(data,extra_removal_val = [],remove_keys = []):
    removable_values = [None, [], {},'']
    if extra_removal_val:
        removable_values.extend(extra_removal_val)

    if isinstance(data, dict):
        cleaned_dict = {k: clean_data(v,extra_removal_val,remove_keys) for k, v in data.items() if k != "__typename" and v not in removable_values and k not in remove_keys}
        
        return {k: v for k, v in cleaned_dict.items() if v not in removable_values and k not in remove_keys}
    
    elif isinstance(data, list):
        return [clean_data(item,extra_removal_val,remove_keys) for item in data if item not in removable_values]
    
    return data


def product_parser(html : str) -> dict | None:

    product_data = {}

    soup = BeautifulSoup(html,'html.parser')

    try:
        page_json = json.loads(soup.select_one('script[type="application/discover+json"]').text)['mfe-orchestrator']['props']['apolloCache']

        if not page_json:
            return None
    except:
        return None
    
    product_url = soup.select_one('link[rel="canonical"]').get('href')
    product_id = product_url.split('/')[-1].split('?')[0]
   
    product_json = page_json.get(f"MPProduct:{product_id}") or page_json.get(
        f"ProductType:{product_id}"
        )
   
    product_data['item_id'] = product_id
    product_data['brand'] = product_json['brandName']
    product_data['product_name'] = product_json['title']
    product_data['product_url'] = product_url
    product_data["product_specification"] = None

    if product_json['details'].get("specifications"):
        product_data["product_specification"] = [
            f'{item["name"]} : {item["value"]}'
            for item in product_json["details"]["specifications"][0][
                "specificationAttributes"
            ]
        ]

    if product_json.get('defaultImageUrl'):    
        product_data['main_image'] = product_json['defaultImageUrl'].split('?')[0]
    
    if product_json['images'] and product_json['images'].get('display'):
        product_data['images'] = ' | '.join([img['default']['url'] for img in product_json['images']['display']])
        product_data['no_of_pictures'] = len(product_json['images']['display'])

    if product_json['price'] and product_json['price'].get('actual'):
        product_data['retail_price'] = product_json['price']['actual']

    if product_json.get('promotions') and product_json['promotions'][0].get('__ref'):
        
        promotion_json  = page_json[product_json['promotions'][0].get('__ref')]
        if promotion_json['price'] and promotion_json['price'].get('beforeDiscount'):
            product_data['msrp_price'] = promotion_json['price']['beforeDiscount']
        
        product_data['offers'] = []
        for offer in product_json['promotions']:
            product_data['offers'].append(clean_data(page_json[offer.get('__ref')],remove_keys=['id','promotionType','qualities','attributes','afterDiscount']))

        
    if product_json['reviews({"count":10,"offset":0})'].get('stats'):
        product_data['avg_tating'] = product_json['reviews({"count":10,"offset":0})'].get('stats').get('overallRating')
        product_data['no_of_reviews'] = product_json['reviews({"count":10,"offset":0})'].get('stats').get('noOfReviews')

        if product_json['reviews({"count":10,"offset":0})'].get('entries'):
            product_data['reviews'] = clean_data(product_json['reviews({"count":10,"offset":0})'].get('entries'),remove_keys=['syndicated','reviewId','authoredByMe'])

    try:
        product_data["baseProductId"] =  product_json['baseProductId']
        product_data["gtin"] =  product_json['gtin']
        product_data["tpnb"] = product_json["tpnb"]
        product_data["tpnc"] =  product_json["tpnc"]
    except:
        ...
    
    product_data['in_stock'] = False
    product_data['max_buy_limit'] = product_json['bulkBuyLimit']
    if product_json['status'] == 'AvailableForSale' or product_json['isForSale']:
        product_data['in_stock'] = True

    if availability_text := soup.select_one('div[data-auto="pdp-product-tile-messaging"] div[role="status"] span'):
        product_data['availability_text'] = availability_text.text

    if product_json['seller'] and product_json['seller'].get('__ref'):
        product_data['Seller_name'] = page_json[product_json['seller'].get('__ref')]['name']

    try:
        product_data['category'] = ' > '.join([i.text for i in soup.select('nav[aria-label="breadcrumb"] li a') if i.text.strip()])
        product_data['category_url'] = soup.select('nav[aria-label="breadcrumb"] li a')[-1].get('href')
    except:
        ...


    if product_json['details'].get('components'):
        
        if product_json['details']['components'][0].get('isLowEverydayPricing'):
            product_data['is_low_everyday_pricing'] = True
        
        if product_json['details']['components'][0].get('isLowPricePromise'):
            product_data['is_low_price_promise'] = True
        
        if (len(product_json['details']['components']) > 1  and
            product_json['details']['components'][1].get('competitors')):
            competitors = product_json['details']['components'][1]['competitors']
            product_data['competitors'] = [ 
                                            {
                                                "name": competitor['id'], 
                                                "is_price_matched": competitor['priceMatch']['isMatching']
                                            }
                                            for competitor in competitors
                                            ]


    if product_json['details'].get('guidelineDailyAmount') and product_json['details']['guidelineDailyAmount'].get('dailyAmounts'):
        product_data['guideline_daily_amount'] = clean_data(product_json['details']['guidelineDailyAmount'])

    if product_json['details'].get('numberOfUses'):
        product_data['number_of_uses'] = product_json['details']['numberOfUses']

    if product_json['details'].get('features'):
        product_data['features'] = ' | '.join(product_json['details'].get('features'))

    product_data['product_description'] = ''
    if product_json['description']:
        product_data['product_description'] = ','.join(product_json['description'])

    marking_keys = ['marketing','manufacturerMarketing','productMarketing','brandMarketing','otherInformation']

    if product_json['details'].get('marketing') == product_json['details'].get('productMarketing') :
        marking_keys.remove('productMarketing')

    for marketing in marking_keys :
        if product_json['details'].get(marketing):
            product_data['product_description'] += '| '+' | '.join([BeautifulSoup(item,'html.parser').text.strip() for item in  product_json['details'][marketing] if BeautifulSoup(item,'html.parser').text.strip()])

    if product_json['restrictions']:
        product_data['restrictions'] = ' | '.join([BeautifulSoup(item.get('message'),'html.parser').text.strip() for item in product_json['restrictions']])

    if product_json['details'].get('packSize') and product_json['details']['packSize'][0].get('value'):
        product_data['pack_size'] =  ' | '.join([f'{pack["value"]} {pack["units"]}'  for pack in product_json['details']['packSize']])


    if product_json['details']['ingredients']:
        product_data['ingredients'] = ', '.join([BeautifulSoup(item,'html.parser').text for item in product_json['details']['ingredients']])

    if product_json['details'].get('healthClaims'):
        product_data['health_claims'] = ', '.join(product_json['details']['healthClaims'])
    
    if product_json['details'].get('nutritionalClaims'):
        product_data['nutritional_claims'] = ', '.join(product_json['details']['nutritionalClaims'])

    if product_json['details']['allergens']:
        product_data['allergens'] = ', '.join([f'{item["name"]} : {",".join(item["values"])}'
                                                if item["name"] != "Other Allergen Info"
                                                else ",".join(item["values"])
                                                for item in product_json['details']['allergens']])
    

    if product_json['icons']:
        product_data['third_party_logos'] = ', '.join([page_json[item.get('__ref')]['id'] for item in product_json['icons']])

    if product_json['details'].get('storage'):
        product_data['storage'] = ' | '.join(product_json['details']['storage'])

    if product_json['details'].get('nutrition'):
        nutrition_json = product_json['details']['nutrition']
        keys_for_nutrition = [nutrition_json[0]['name']]
        keys_for_nutrition.extend([nutrition_json[0][f'value{i}'] for i in range(1,5) if nutrition_json[0].get(f'value{i}')])
        product_data['nutrition'] = []
        for item in nutrition_json[1:]:
            nuttion = {
                keys_for_nutrition[0] : item['name'],
            }
            for i in range(len(keys_for_nutrition)-1):
                nuttion[keys_for_nutrition[i+1]] = item[f'value{i+1}']
            product_data['nutrition'].append(nuttion)
        
    if product_json['details'].get('netContents'):
        product_data['net_contents'] = clean_data(product_json['details']['netContents'])

    if product_json['details'].get('originInformation'):
        product_data['origin_information'] = ' | '.join([f'{i["title"]} : {i["value"]}' for i in product_json['details']['originInformation']])

    if product_json['details'].get('cookingInstructions') :
        if cooking_json :=  clean_data(product_json['details']['cookingInstructions']):
            product_data['cooking_instructions'] = cooking_json

    if product_json['details'].get('recyclingInfo'):
        product_data['recycling_info'] = clean_data(product_json['details']['recyclingInfo'])

    if product_json['details'].get('warnings'):
        product_data['warnings/safety_info'] = ' | '.join(product_json['details']['warnings'])

    if product_json['details'].get('preparationAndUsage'):
        product_data['preparation_and_usage'] = ' | '.join([BeautifulSoup(item,'html.parser').text.strip() for item in product_json['details']['preparationAndUsage']])
    
    if product_json['details'].get('nutritionalClaims'):
        product_data['nutritional_claims'] = ' | '.join([BeautifulSoup(item,'html.parser').text.strip() for item in product_json['details']['nutritionalClaims']])
    
    if product_json['details'].get('alcohol'):
        product_data['alcohol'] = clean_data(product_json['details']['alcohol'])

    remain_points = {
        'freezingInstructions': 'freezing_instructions',
        'additives': 'additives',
        'drainedWeight' : 'drained_weight',
        'safetyWarning' : 'safety_warning',
        'lowerAgeLimit' : 'lower_age_limit',
        'upperAgeLimit': 'upper_age_limit',
        'healthmark': 'healthmark',
        'nappies': 'nappies',
        'dosage' : 'dosage',
        'directions' : 'directions',
        'boxContents' : 'box_contents',
    }

    for key,value in remain_points.items():
        if product_json['details'].get(key):
            product_data[value] = clean_data(product_json['details'][key])
            if isinstance(product_data[value],list):
                product_data[value] = ' | '.join(product_data[value])

    addresses_dict = {
        'distributorAddress' : 'distributor_address',
        'manufacturerAddress' : 'manufacturer_address',
        'importerAddress' : 'importer_address',
        'returnTo' : 'return_address'
    }
    
    for key,value in addresses_dict.items():
        if product_json.get(key):
            product_data[value] = []
            for i in range(1,13):
                if address_line :=product_json[key][f'addressLine{i}']:
                    product_data[value].append(address_line)
                else:
                    break
            product_data[value] = ' '.join(product_data[value])

    
    return product_data
