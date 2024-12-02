import requests
from bs4 import BeautifulSoup
import json
import os
from datetime import datetime


API_KEY = os.getenv('SYPHOON_API_KEY')

def send_request(url : str, max_retires : int=2) -> str | None:

    while max_retires:
        try:
            payload = {
                "key":API_KEY,
                "url":url,
                "method":"GET"
            }

            response = requests.post('https://api.syphoon.com',json=payload)

            if response.status_code == 200:
                return response.text
            
            max_retires -= 1

        except:
            max_retires -= 1
    
    return None


def product_parser(html : str) -> dict | None:

    product_data = {}

    soup = BeautifulSoup(html,'html.parser')

    page_json = json.loads(soup.select_one('script[type="application/discover+json"]').text)['mfe-orchestrator']['props']['apolloCache']

    if not page_json:
        return None

    product_url = soup.select_one('link[rel="canonical"]').get('href')
    product_id = product_url.split('/')[-1].split('?')[0]
    product_json = page_json[f'MPProduct:{product_id}']


    product_data['Record id'] = product_id
    product_data['Probe id'] = ''
    product_data['Probe date'] = datetime.now().strftime('%Y-%m-%d')
    product_data['URL date time'] = datetime.now().isoformat()

    product_data['Shop URL'] = ''
    product_data['Producer Name'] = product_json['brandName']
    product_data['Product Name'] = product_json['title']
    product_data['Product URL'] = product_url
    product_data['Product attributes'] = [f'{item["name"]} : {item["value"]}' for item in product_json['details']['specifications'][0]['specificationAttributes']]

    product_data['Photo URL'] = product_json['defaultImageUrl'].split('?')[0]
    product_data['Price'] = product_json['price']['actual']

    if soup.select_one('div.ddsweb-buybox__price.ddsweb-price__container p'):
        product_data['Price_text'] = soup.select_one('div.ddsweb-buybox__price.ddsweb-price__container p').text.replace('Â','')
    else:
        product_data['Price_text'] = ''

    product_data['Price before promotion'] = None
    product_data['Price before promotion_text'] = None
    if product_json.get('promotions') and product_json['promotions'][0].get('__ref'):
        
        promotion_json  = page_json[product_json['promotions'][0].get('__ref')]
        product_data['Price before promotion'] = promotion_json['price']['beforeDiscount']
        product_data['Price before promotion_text'] = soup.select_one('div[class*="value-bar__promo-text"] span').text.lower().split('now')[0].replace('was','').replace('â','').strip()

    # product_data['Star Rating']  = None
    if product_json['reviews({"count":10,"offset":0})'].get('stats'):
        product_data['Star Rating'] = product_json['reviews({"count":10,"offset":0})'].get('stats').get('overallRating')
        product_data['Reviews'] = product_json['reviews({"count":10,"offset":0})'].get('stats').get('noOfReviews')

    product_data['Codes'] = ' | '.join([
        "baseProductId : " + product_json['baseProductId'],
        "gtin : " + product_json['gtin'],
        "tpnb : " +product_json["tpnb"],
        "tpnc : " + product_json["tpnc"]
    ])
    
    
    product_data['Availability'] = 0

    if product_json['status'] == 'AvailableForSale':
        product_data['Availability'] = 1

    if availability_text := soup.select_one('div[data-auto="pdp-product-tile-messaging"] div[role="status"] span'):
        product_data['Product availability text'] = availability_text.text


    product_data['Is product is sold by official seller'] = 'Y'
    product_data['Is product is shipped by official seller'] = 'Y'

    if product_json['seller'] and product_json['seller'].get('__ref'):
        product_data['Seller name'] = page_json[product_json['seller'].get('__ref')]['name']

    product_data['category'] = ' > '.join([i.text for i in soup.select('nav[aria-label="breadcrumb"] li a') if i.text.strip()])
    product_data['Category URL'] = soup.select('nav[aria-label="breadcrumb"] li a')[-1].get('href')

    # To maintain column index 
    product_data['Search Keyword'] = ''
    product_data['Page'] = '' 
    product_data['Position'] = ''
    product_data['Total position'] = ''


    # Taking this details from the product card
    product_data['Product title'] = '-'
    product_data['Product description'] = '-'


    # product_data['Product description'] = ','.join(product_json['description'])

    # if product_json['details'].get('marketing'):
    #     product_data['Bullet point'] = ' | '.join([item for item in  product_json['details']['marketing'] if item.lower().replace('<br>','').strip()])
    #     product_data['Product description'] += '| '+product_data['Bullet point']

    # if product_json['details'].get('packSize'):
    #     product_data['Product description'] += ' | '+f'Pack size: {product_json["details"]["packSize"][0]["value"]}{product_json["details"]["packSize"][0]["units"]}'

    # if product_json['details']['ingredients']:
    #     product_data['Product description'] += '| '+f'Ingredients : '+', '.join(product_json['details']['ingredients'])

    # if product_json['details']['allergens']:
    #     product_data['Product description'] += '| '+f'Allergy Information : '+', '.join([f'{item["name"]} : {",".join(item["values"])}' for item in product_json['details']['allergens']])
    
    product_data['Rich content presence']  = 'Yes'
    product_data['Video presence'] = 'No'
    product_data['Gallery pictures'] = len(product_json['images']['display'])
    product_data['Gallery images URLs'] = ' | '.join([img['default']['url'] for img in product_json['images']['display']])
    
    product_data['Product list HTML'] = ''
    product_data['Product PDP HTNL'] = ''

    return product_data


def tesco_product_crawler(category_url : str):

    # Sending Category request

    
    category_page = send_request(category_url)

    category_soup = BeautifulSoup(category_page,'html.parser')
    
    current_page = category_soup.select_one('a[aria-current="page"]').get('data-page')

    pagination = category_soup.select('div.ddsweb-pagination__results strong')
    starts_from = int(pagination[0].text.split('to')[0].replace(',',''))
    total_products = int(pagination[1].text.replace(',',''))

    keyword_soup = category_soup.select_one('h1')
    if keyword_soup and 'Showing results for' in keyword_soup.text:
        keyword = keyword_soup.text.split('for ')[1]
    else:
        keyword = None

    data = []
    for inx,product in enumerate(category_soup.select('ul#list-content li h3.ddsweb-title-link__container a'),start=starts_from):
        print('Processing Product',product.get('href'))
        product_page = send_request('https://www.tesco.com'+product.get('href'))

        product_data = product_parser(product_page)

        # currently i am considering probid same as inx value
        # adding remaining data
        product_data['Probe id'] = inx
        product_data['Shop URL'] = category_url
        product_data['Product title'] = product.text.strip()
        product_data['Search Keyword'] = keyword
        product_data['Page'] = current_page 
        product_data['Position'] = inx
        product_data['Total position'] = total_products
        product_data['Product list HTML'] = category_page
        product_data['Product PDP HTNL'] = product_page

        data.append(product_data)

    return data
