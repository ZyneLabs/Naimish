
from bs4 import BeautifulSoup as bs
from common import *

import json
import re

#
# please change the syphoon request with you function
#
 
def get_digit_groups(input_str):
    if input_str is None:
        return []
    return re.findall(r'\d+', input_str)

headers = {
    'priority': 'u=1, i',
    'sec-ch-ua': '"Not/A)Brand";v="8", "Chromium";v="126", "Google Chrome";v="126"',
    'sec-ch-ua-mobile': '?0',
    'sec-ch-ua-platform': '"Linux"',
    'sec-fetch-dest': 'empty',
    'sec-fetch-mode': 'cors',
    'sec-fetch-site': 'same-origin',
    'user-agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36',
    'x-requested-with': 'XMLHttpRequest',
}

def send_pf_inventory_req(product_id,product_url):
    
    headers['referer'] = product_url
    params = {
        'catalogEntryIds': product_id,
        'source': 'pdp',
        '_': '1721710268962',
        'userAction': 'true',
    }

    try:
        ### here ### 
        inv_response = send_req_syphoon(0,'get','https://www.avnet.com/wcs/resources/store/715839035/fetchpf/fetchPFInventoryCatentryIds', headers=headers,params=params)
        inv_response.raise_for_status()

        return inv_response.json()
    except Exception as ex:
        print(ex)
        return {'message' : 'Inventory page loading failed'}
    
def send_inventory_req(product_id, product_url):
    
    headers['referer'] = product_url
    params = {
        'catalogEntryIds': product_id,
        'invRefreshFlag': 'true',
        'source': 'pdp',
        'onOrderedStock': 'true',
        '_': '1721646135576',
        'userAction': 'true',
    }
    try:

        ### here ###
        inv_response = send_req_syphoon(0,'get','https://www.avnet.com/wcs/resources/store/715839035/inventory/fetchInventoryCatentryIds', headers=headers,params=params)
        inv_response.raise_for_status()

        return inv_response.json()
    except Exception as ex:
        print(ex)
        return {'message' : 'Inventory page loading failed'}
    
def parse_price_inventory_content(product_html,inventory_json):
    soup = bs(product_html, "html.parser")

    details = {}


    try:
        product_json = json.loads(soup.find("script", {"type": "application/ld+json"}).text)
        product_id = product_json["url"].split("-")[-1].replace('/','')
        details['url'] = product_json['url']
        rows = {
            "{:,}+".format(int(get_digit_groups(row['eligibleQuantity']['minValue'])[0])): row['price']
            for row in product_json['offers'][0]['offers']
        }
        if rows:
            details["price_breakdown"] = rows
            details["unit_price"] = list(rows.values())
            details["volume_break"] = list(rows.keys())
            details["minimum_order_qty"] = details["volume_break"][0].replace('+','')
            details["selling_price"] = float(product_json['offers'][0]['highPrice'])
            details["packaging_type_specs"] = 'Each'
    except Exception as ex:
        ...

    try:
        maybe_mult_qty =int (get_digit_groups(product_html.split('"multQuantity":')[1].split(',')[0])[0])
        details["increment_of_qty"] = maybe_mult_qty
    except Exception as ex:
        ...

    try:
        details["total_price"] ='{:,}'.format(round(float(details["selling_price"]) * float(
            int(details["minimum_order_qty"].replace(',',''))
        ),2))
    except Exception as ex:
        ...

    try:
        maybe_factory_stock = int(get_digit_groups(inventory_json['InventoryAvailability'][product_id].get('factoryInventory','0'))[0])
        maybe_current_stock = inventory_json['InventoryAvailability'][product_id]['availableQuantity'] if "Int'l" not in product_html else maybe_factory_stock
        if maybe_current_stock :
            details['stock_condtion'] = {'In Stock': maybe_current_stock}

        elif maybe_factory_stock :
            if 'Partner Stock' in product_html:
                details['stock_condtion'] = {'Partner Stock': maybe_factory_stock}
            else:
                details['stock_condtion'] = {'Factory Stock': maybe_factory_stock}
        else:
            details['stock_condtion'] = {'Out of Stock': 0}
    except Exception as ex:
        ...

    try:
        maybe_fulfilled_soup = soup.find(string=re.compile('Fulfilled by'))
        if maybe_fulfilled_soup:
            details["fulfillment_by"] = maybe_fulfilled_soup.text.replace("Fulfilled by","").strip()
    except Exception as ex:
        ...

    try:
        maybe_domestic_soup = soup.find(string=re.compile('Domestic:'))
        if maybe_domestic_soup:
            details["domestic_ship_or_lead_time"] = maybe_domestic_soup.text.replace("Domestic: Ships in","").strip()
            details["domestic_ship_or_lead_time_org"] = maybe_domestic_soup.text.strip()
    except Exception as ex:
        print(ex)
        ...

    try:
        maybe_international_soup = soup.find(string=re.compile("Int'l:"))
        if maybe_international_soup:
            details["international_ship_or_lead_time"] = maybe_international_soup.text.replace("Int'l: Ships in","").strip()
            details["international_ship_or_lead_time_org"] = maybe_international_soup.text.strip()
    except Exception as ex:
        print(ex)
        ...

    try:

        maybe_in_stock_soup = soup.select('span.in-stock.green-pdp ~ div.grey')
        if len(maybe_in_stock_soup) != 0 and "Int'l:" not in product_html :
            if maybe_current_stock:
                details["distributor_ship_or_lead_time_org"] = maybe_in_stock_soup[0].text.strip()
                details["distributor_ship_or_lead_time"] = maybe_in_stock_soup[0].text.replace(
                    "Ships in ", ""
                ).strip()
            
            else:
                details["factory_stock_ship_or_lead_time_org"] = maybe_in_stock_soup[0].text.strip()
                details["factory_stock_ship_or_lead_time"] = maybe_in_stock_soup[0].text.replace(
                    "Ships in ", ""
                ).strip()
            
    except Exception as ex:
        ...

    try:
        maybe_factory_lead_time = inventory_json['InventoryAvailability'][product_id]['leadTimeMsg']
        if maybe_factory_lead_time:
            details["manufacture_lead_time"] = maybe_factory_lead_time
            details["manufacture_lead_time_org"] = "Factory Lead Time: " + maybe_factory_lead_time
    except:
        try:
            maybe_factory_lead_time = int(get_digit_groups(product_html.split('"factoryLeadTime":')[1].split(',')[0])[0])
            weeks = maybe_factory_lead_time // 7
            days = maybe_factory_lead_time % 7
            
            if days == 0:
                maybe_factory_lead_time = f"{weeks} weeks"
            else:
                maybe_factory_lead_time = f"{weeks} weeks {days} days"

                
            details["manufacture_lead_time"] = maybe_factory_lead_time
            details["manufacture_lead_time_org"] = "Factory Lead Time: " + maybe_factory_lead_time
        except Exception as ex:
            ...

    return details


def avenet_parser(url):
    product_id = url.split("-")[-1].replace('/','')
    headers = {
        'sec-ch-ua': '"Not/A)Brand";v="8", "Chromium";v="126", "Google Chrome";v="126"',
        'sec-ch-ua-mobile': '?0',
        'sec-ch-ua-platform': '"Windows"',
        'sec-fetch-dest': 'empty',
        'sec-fetch-mode': 'cors',
        'sec-fetch-site': 'same-origin',
        'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36',
        'Content-Type': 'application/json'
    }  

    res = send_req_syphoon(0, "GET", url, headers=headers)
    product_html = res.text

    soup = BeautifulSoup(product_html, 'html.parser')
    maybe_international_stock = soup.find(id=re.compile("avtPfFlag_"))
    if maybe_international_stock:
        maybe_international_stock = int(maybe_international_stock.get('value')) == 20
        
    inventory_json =send_pf_inventory_req(product_id,url) if maybe_international_stock else  send_inventory_req(product_id,url)

    return parse_price_inventory_content(product_html,inventory_json)
