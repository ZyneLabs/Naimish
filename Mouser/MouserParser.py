from bs4 import BeautifulSoup
import re
import json
import requests
import os
from urllib.parse import quote_plus

try:
    from deep_translator import GoogleTranslator
    translator = GoogleTranslator()
except ModuleNotFoundError:
    print("Deep Translator module not found. Please run 'pip install deep-translator' to install it.")
    exit(1)


def get_digits(input_str):
    return re.sub(r"[^0-9]", "", input_str)

def mouser_scraper(url,method='get',max_tries=5):
    while True:
        try:
            payload = {
                "url": url,
                "key":os.environ.get("MOUSER_API_KEY"),
                "method": method,
            }
            response = requests.post('https://api.syphoon.com', json=payload)
            response.raise_for_status()
            if response.status_code == 200:
                return response
        except:
            if max_tries <= 0:
                return None
            max_tries -= 1

def clean_str(input_str, sep="|"):
    if input_str is None:
        return ""

    if type(input_str) is not str:
        return input_str

    input_str = re.sub(r"\s+", " ", input_str).replace("\n", sep).replace("\u200e", '').replace('\u200f','').replace('\xa0','')

    return input_str.strip()


def mouser_parser(html:str):
    soup = BeautifulSoup(html, 'html.parser')
    details  = {}
    try:
        maybe_product_title = soup.select_one('#pdpProdInfo h1')
        if not maybe_product_title:
            return {'Error': 'Product title not found'}
        
        #1. URL
        url = soup.select_one('meta[itemprop="url"]').get('content')
        details['URL'] = url

        #2. Category Path
        category_path = ' > '.join([clean_str(i.text) for i in soup.select('ol.breadcrumb li a')])
        details['Category_Path'] = category_path

        # 3. Mouser ID
        mouser_id = soup.select_one('#spnMouserPartNumFormattedForProdInfo').get_text(strip=True)
        details['Mouser_ID'] = mouser_id

        # 4. Manufacturer Part Number
        manufacturer_id = soup.select_one('#spnManufacturerPartNumber').get_text(strip=True)
        details['Manufacturer_Part_Number'] = manufacturer_id

        # 5. Manufacturer
        manufacturer = soup.select_one('#lnkManufacturerName').get_text(strip=True)
        details['Manufacturer'] = manufacturer

        # 6. Description
        description = soup.select_one('#spnDescription').get_text(strip=True)
        details['Description'] = description

        # 7. Life Cycle
        maybe_life_cycle = soup.find(class_='lblMfrInfo',string=re.compile('Lifecycle:'))
        if maybe_life_cycle:
            life_cycle = maybe_life_cycle.parent.find_next_sibling().get_text(strip=True)
            details['Life_Cycle'] = life_cycle

        # 8. Documents
        details['Documents'] = []
        maybe_documents = soup.select('.pdp-product-documents-list a')
        if maybe_documents:
            details['Documents'].extend([a.get('href') for a in maybe_documents])
        
        maybe_datasheet = soup.select_one('a#pdp-datasheet_0')
        if maybe_datasheet:
            if maybe_datasheet.get('href') not in details['Documents']:
                details['Documents'].append(maybe_datasheet.get('href'))
        
        details['Documents'] = ' | '.join(details['Documents'])

        # 9. Is Buyable
        maybe_buyable = soup.select_one('#btnBuy')
        if maybe_buyable:
            details['Is_Buyable'] = True
        else:
            details['Is_Buyable'] = False

        # 10. Stock
        maybe_stock = soup.select_one('#pdpPricingAvailability .pdp-product-availability #stockLabelHeader')
        if maybe_stock:
            stock_text = maybe_stock.find_parent('dt').find_next_sibling('dd').find('div').text.split()
            details['Stock'] = stock_text[0]

            # 11. Availability
            details['Availability'] = ' '.join(stock_text[1:])

        # 12. Factory Lead Time
        maybe_lead_time = soup.select_one('#factoryLeadTimeMsg')
        if maybe_lead_time:
            print(maybe_lead_time.parent.get_text(strip=True))
            maybe_lead_time = translator.translate(maybe_lead_time.parent.get_text(strip=True))
            print(maybe_lead_time)
            details['Factory_Lead_Time'] = maybe_lead_time.split('Estimated')[0]

        # 13. Minimum_Order
        maybe_minimum_order = soup.select_one('#minmultdisplaytext')
        if maybe_minimum_order:
            details['Minimum_Order'] = maybe_minimum_order.get_text(strip=True).split('Minimum')[1].split()[0].replace('&nbsp','').replace(':',"")

        # 14. Product Title
        details['Product_Title'] = maybe_product_title.get_text(strip=True)

        # 15. Product Image
        try:
            product_json = json.loads(soup.find('script',attrs={'type':"application/ld+json"},string=re.compile('"Product"')).get_text(strip=True))
            details['Product_Images'] = product_json['image']
        except:
            details['Product_Images'] = soup.select_one('meta[property="og:image"]').get('content')
        maybe_more_imgages = soup.select_one('#plusMoreImagesText')
        if maybe_more_imgages:
            image_count = int(get_digits(maybe_more_imgages.get_text(strip=True)))
            images = [details['Product_Images']]
            for i in range(1,image_count+1):
                images.append(details['Product_Images'].replace('_t.JPG',f'_{i}.JPG'))
            details['Product_Images'] = ' | '.join(images)

        maybe_pricing_table = soup.select_one('.pdp-pricing-table')
        if maybe_pricing_table:
            # 16. Volume breakdown
            details['Volume_Breakdown'] = [ clean_str(i.get_text(strip=True)) for i in maybe_pricing_table.find_all(attrs={'headers':"quantitycolhdr"})]

            # 17. Exect Price
            details['Exect_Price'] = [ clean_str(i.get_text(strip=True)) for i in maybe_pricing_table.find_all(attrs={'headers':"extpricecolhdr"})]

            # 18. Unit Price
            details['Unit_Price'] = [ clean_str(i.get_text(strip=True)) for i in maybe_pricing_table.find_all(attrs={'headers':"unitpricecolhdr"})]

        # 22. Specifications
        details['Specifications'] = []
        details['RoHS'] = 'No'
        details['Packaging']  = []

        maybe_specification_table = soup.select('#collapseProductSpecs .specs-table tr[id]')
        if maybe_specification_table:
            for row in maybe_specification_table:
                key = clean_str(row.select_one('td.attr-col').text).replace(':','')
                value = clean_str(row.select_one('td.attr-value-col').text)
                comp_key = translator.translate(key)
                # 23. RoHS
                if comp_key == 'RoHS':
                    details['RoHS'] = 'Yes' if translator.translate(value) == 'Details' else value
                
                # 24. Series
                elif comp_key == 'Series':
                    details['Series'] = value

                #28. Packaging 
                elif 'Packaging' == comp_key:
                    details['Packaging'].append(value)

                # 29. Factory Pack Quantity
                elif 'Factory Pack Quantity' in comp_key:
                    key = 'Factory Pack Quantity'
                    details['Factory_Pack_Quantity'] = value

                    
                details['Specifications'].append(f'{key}: {value}')

        details['Packaging'] = ' | '.join(details['Packaging'])

        # More info
        maybe_more_info = soup.select('#pdpProdMoreInfo #detail-feature-desc')
        if maybe_more_info:
            for item in maybe_more_info:
                if item.select_one('h3'):
                    key = clean_str(item.select_one('h3').text)
                elif item.select_one('h2'):
                    key = clean_str(item.select_one('h2').text)
                else:
                    continue
                val = clean_str(' '.join([i.text for i in item.select('p') if i.text]))
                details['Specifications'].append(f'{key}: {val}')

        details['Specifications'] = ' | '.join(details['Specifications'])
        # 25. Environment Documents 
        maybe_environment = soup.select('#pdpProdEnvDocs a')
        if maybe_environment:
            details['Environment_Documents'] = ' | '.join([a.get('href') for a in maybe_environment])
        else:
            details['Environment_Documents'] = html.split('"event_ihs_object_id":"')[1].split('"')[0]

        # 26. Product Compliance
        maybe_compliance = soup.select_one('.compliance-dlist')
        if maybe_compliance:
            compliances = dict(zip(maybe_compliance.select('dt'), maybe_compliance.select('dd')))
            details['Product_Compliance'] = ' | '.join([f'{clean_str(k.text)} {clean_str(v.text)}' for k,v in compliances.items()])

        # 28.1 Currency
        currency = soup.select_one('#h2PricingTitle')
        if currency:
            details['Currency'] = currency.get_text(strip=True).split('(')[1].split(')')[0]

        # 28.2 Reel Quantity
        reel_qty = soup.select_one('#reelammohdr')
        if reel_qty:
            details['Reel_Quantity'] = clean_str(reel_qty.get_text(strip=True))

        # On Order
        maybe_on_order = soup.select_one('#content-onOrderShipments .onOrderQuantity')
        if maybe_on_order:
            details['On_Order'] = clean_str(maybe_on_order.get_text(strip=True))

        # 31. Featured Products
        maybe_featured_products = soup.select('#pdpNewestProds a.list-group-item')
        if maybe_featured_products:
            products = []
            for item in maybe_featured_products:
                maybe_product_name = item.select_one('.pdp-newest-products-link-text-bold')
                
                if not maybe_product_name:continue
                product = {
                    'URL': 'https://mouser.com' + item.get('href'),
                    'Product_Name': clean_str(maybe_product_name.text),
                    'Description': clean_str(item.select_one('.pdp-newest-products-link-text').text),
                    'Image': 'https://mouser.com' + item.select_one('img').get('src')
                }

                products.append(product)
        details['Featured_Products'] = products

        # 40. 360 image
        maybe_360_image = soup.select_one('#spinThumbImg')
        if maybe_360_image:
            details['360_Image'] = maybe_360_image.get('src')

        # Product id for Also Boughth
        if soup.select_one('#pdpCustAlsoBought'):
            pid = soup.select_one('#ProductIdEncForCustPartNum').get('value')
        else:
            pid = None

        return details, pid
    except Exception as e:
        return {'URL': url, 'Error': str(e)}, None
# also_bought_url =f'https://www.mouser.com/Product/GetCustomersAlsoBoughtProducts?qs={pid}'

def also_bought_parser(response):

    if type(response) is not dict or not response['success']:
        return []
    
    products = []
    for item in response['customersAlsoBoughtProducts']:
        product = {
            'URL': item['PdpLink'],
            'PartNumber': item['MouserPartNumber'],
            'Description': item['Description'],
            'Image': item['LocalImageLink'],
            'Stock': item['Stock'],
        }
        products.append(product)
    return products

def environment_doc_parser(environment_html):
    soup = BeautifulSoup(environment_html, 'html.parser')

    docs = []
    for item in soup.select('.pdp-product-documents-list a'):
        docs.append(item.get('href'))
    return ' | '.join(docs)

def mouser(url):
    print('Sending request to Mouser', url)
    req = mouser_scraper(url)
    if not req:
        return None
    
    html = req.text
    data,pid = mouser_parser(html)
    if data.get('Environment_Documents') and data.get('Environment_Documents') !='none' and  not data.get('Environment_Documents').startswith('https'):
        # this is not working we need to check this
        print(data.get('Environment_Documents'))
        environment_doc_url = f'https://www.mouser.com/Product/Product/GetEnvironmentalDocs?objectId={data.get("Environment_Documents")}'
        response = mouser_scraper(environment_doc_url,method='POST')
        environment_doc = environment_doc_parser(response.text)
        data['Environment_Documents'] = environment_doc
    
    if pid:
        also_bought_url =f'https://www.mouser.com/Product/GetCustomersAlsoBoughtProducts?qs={quote_plus(pid)}'
        print('Also_bought_url: ', also_bought_url)
        response = mouser_scraper(also_bought_url)
        also_bought_products = also_bought_parser(response.json())
        data['Also_Bought_Products'] = also_bought_products
    else:
        data['Also_Bought_Products'] = []

    return data

