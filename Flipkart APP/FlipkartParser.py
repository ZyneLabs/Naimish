
import json
import traceback
from FlipkartScraper import flipkart_product_page_scraper,flipkart_specification_scraper
from bs4 import BeautifulSoup as bs

def specification_details_parser(extra_details_json):

    try:
        extra_details = extra_details_json['RESPONSE']['data']
    except:
        return {}

    specification_details = {}
    
    try:
        specification_details['Product Description'] =bs(extra_details['product_text_description_1']['data'][0]['value']['text'],'html.parser').get_text(strip=True)
    except: ...
    
    specification_details['Product Specification']=[]
    try:
        specification_details['Product Specification'] = [item['value']['text'] for item in extra_details['product_key_features_1']['data']]
    except: 
        print("Product Specification not found")
        print(traceback.format_exc())

    try:
        for item in extra_details['product_specification_1']['data']:
            for attribute in item["value"]["attributes"]:
                if attribute["name"]=='Color':
                    specification_details['Color'] = attribute["values"][0]

                specification_details['Product Specification'].append(f'{attribute["name"]} : {attribute["values"][0]}' )
    except:
        print("Color not found")
        print(traceback.format_exc())
    
    specification_details['Product Specification'] = ' | '.join(specification_details['Product Specification'])

    return specification_details

def flipkart_parser(response_json):

    try:
        product_page = response_json['RESPONSE']['pageData']['pageContext']
    except:
        return {"message" : "Invalid Response"},{}
    details = {}

    details['Product Name'] = product_page['titles']['title']
    details['Brand'] = product_page['brand']
     
    extra_info = {
        "productId": product_page['productId'],
        "listingId": product_page['listingId'],
    }
    try:
        pricing = product_page['pricing']

        details['List Price'] = pricing['mrp']
        details['Promo Price'] = pricing['finalPrice']['value']
        details['Discount'] = pricing['totalDiscount']

        if details['List Price'] == details['Promo Price']:
            details['Discount'] = None
            details['Promo Price'] = None
    
    except:...

    try:
        for items in response_json['RESPONSE']['slots']:

            if items['widget']['type'] == "MULTIMEDIA":
                images =[]

                for image in items['widget']['data']['multimediaComponents']:
                    if image['value'].get('contentType','') != "IMAGE":continue

                    image = image['value']['url'].replace("{@width}", "832").replace("{@height}", "832").replace("{@quality}", "70")
                    images.append(image)
                details['Images'] =' | '.join(images)

            elif items['widget']['type'] == "SWATCH_VARIANTS":
                details['Color Grouping'] = ' | '.join(color['value']['swatchValue']['value'] for color in items['widget']['data']['renderableComponents'])
    except:
        ...

    details['Rating'] = product_page['rating']['average']
    details['Review Count'] = product_page['rating']['reviewCount']
    details['Seller Name'] = product_page['trackingDataV2']['sellerName']
    
    return details, extra_info


def flipkart(url):
    response_json = flipkart_product_page_scraper(url)
    details, extra_info = flipkart_parser(response_json)
    specification_json = flipkart_specification_scraper(extra_info['productId'], extra_info['listingId'])
    specification_data = specification_details_parser(specification_json)
    response_data = {'requested_url':url,**details,**specification_data}
    return response_data
