import requests
from bs4 import BeautifulSoup
from urllib.parse import urlencode
import os 
from dotenv import load_dotenv

load_dotenv()

API_KEYS = os.getenv("API_KEYS").split(",")

def send_req_syphoon(
    scraper_class, method, url, params=None, headers=None, payload=None, cookies=None, total_retries=5
):

    if params is not None:
        url = f"{url}?{urlencode(params)}"
    
    if payload is None:
        payload = {}

    if headers is not None:
        payload['keep_headers'] = True
    else:
        headers = {}


    payload = {
        **payload,
        "key": API_KEYS[scraper_class],
        "url": url,
        "method": method,
        "keep_headers": True
    }
    
    if cookies is not None:
        headers["cookie"] = ";".join([f"{k}={v}" for k, v in cookies.items()])

    retry_count = 0

    while retry_count < total_retries:
        try:
            return requests.post(
                "https://api.syphoon.com", json=payload, headers=headers, verify=False
            )
        except Exception as ex:
            retry_count += 1


def get_cookie_from_page(url):
    req = send_req_syphoon(1, 'GET',url)
    if req.status_code == 200:
        return req.headers['set-cookie']
    

def get_common_headers():
    return {
        'origin': 'https://www.grainger.com',
        'priority': 'u=1, i',
        'sec-ch-ua': '"Not/A)Brand";v="8", "Chromium";v="126", "Google Chrome";v="126"',
        'sec-ch-ua-mobile': '?0',
        'sec-ch-ua-platform': '"Windows"',
        'sec-fetch-dest': 'empty',
        'sec-fetch-mode': 'cors',
        'sec-fetch-site': 'same-origin',
        'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36',
    }
    
def get_token(cookie):
    headers = get_common_headers()
    headers['x-requested-with'] = 'XMLHttpRequest'
    headers['cookie'] = cookie
    token_req = send_req_syphoon(1, 'GET', 'https://www.grainger.com/GenericController?domain=www.grainger.com', headers=headers)

    return token_req.json()


def change_zipcode(zipcode,cookie):
    headers = get_common_headers()
    headers['cookie'] = cookie
    zipcode_req = send_req_syphoon(1, 'GET', f'https://www.grainger.com/cart/getAvailability?zipCode={zipcode}', headers=headers)

    return zipcode_req

def check_zipcode(cookie):
    headers = get_common_headers()
    headers['cookie'] = cookie

    zipcode_req = send_req_syphoon(1, 'POST', 'https://www.grainger.com/rta/getlastusedrtainfo?deliveryMode=Pickup', headers=headers)

    return zipcode_req

def clean_cart(cookie):
    headers = get_common_headers()
    headers['cookie'] = cookie
    clean_cart_req = send_req_syphoon(1, 'POST', 'https://www.grainger.com/cart/clearItems', headers=headers)

    return clean_cart_req


def add_item_to_cart(cookie,params):
    headers = get_common_headers()
    
    #################################
    ### need to make changes here ###
    #################################
    
    headers['content-type'] = 'application/x-www-form-urlencoded'
    headers['contenttype'] = 'application/x-www-form-urlencoded'
    headers['cookie'] = cookie
    headers['x-requested-with'] = 'XMLHttpRequest'
    add_item_to_cart_req = send_req_syphoon(1, 'POST', f'https://www.grainger.com/cart/addItem', headers=headers,params=params)

    return add_item_to_cart_req


def get_cart_info(cookie):
    headers = get_common_headers()
    headers['cookie'] = cookie
    cart_info_req = send_req_syphoon(1, 'GET', 'https://www.grainger.com/cart', headers=headers)
    
    details = {}
    soup = BeautifulSoup(cart_info_req.text, 'html.parser')

    if cart_info_req.status_code != 200: return {'error': 'Failed to get cart info'}

    if soup.find(attrs={"data-automated-test":"summary-subtotal-value"}):
        details['sub_total'] = soup.find(attrs={"data-automated-test":"summary-subtotal-value"}).text.replace('$','').strip()
        details['estimated_tax'] = soup.find(attrs={"data-automated-test":"summary-tax-value"}).text.replace('$','').strip()
        details['estimated_shipping'] = soup.find(attrs={"data-automated-test":"summary-shipping-value"}).text.replace('$','').strip()
        details['estimated_total'] = soup.find(class_="checkout-summary__total-value").text.replace('$','').strip()
        return details
    
    else:
        return {'error': 'Failed to get cart info'}


def get_price_info(url):
    
    zipcode_list = ['17601','42101','49512','77041','92121']

    # getting initial cookie
    cookie = get_cookie_from_page(url)
    

    item_number = url.split("/product/")[1].split("?")[0].split("-")[-1]

    tokens = get_token(cookie)
   
    params = {
        'cartEntries[0].quantity': '1',
        'cartEntries[0].sku': item_number,
        tokens['tokenKey']: tokens['tokenValue'],
    }

    # adding item to cart
    add_item_to_cart(cookie,params)

    price_details = {}
    # changing zipcode and getting cart info
    for zipcode in  zipcode_list:   

        change_zipcode(zipcode,cookie)
        
        # verifying zipcode
        # print(check_zipcode(cookie).text)

        
        price_details[zipcode] = get_cart_info(cookie)

    return price_details

