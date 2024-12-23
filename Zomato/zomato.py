from bs4 import BeautifulSoup
import requests
import re
try:
    import execjs
except ImportError:
    execjs = None
    print('Please install PyExecJS to run this script')
    print('pip install PyExecJS')
    exit()

import json
from pydantic import BaseModel
import os


def zomato_scraper(url: str):
    payload = {
        "url": url,
        "method": "GET",
        "key": os.getenv('API_KEY'),  # `kW4` is working
    }
    response = requests.post('https://api.syphoon.com/', json=payload)
    if response.status_code == 200:
        return response.text
    return None


class Item(BaseModel):
    id: str
    name: str
    price: float
    desc: str
    min_price: float
    max_price: float
    default_price: float
    display_price: float
    variant_id: str
    item_state: str
    parent_menu_id: str
    item_image_url: str | None = None


def load_json_from_js(soup: BeautifulSoup):
    try:
        preload_state = soup.find('script', string=re.compile('__PRELOADED_STATE__')).text.replace(
            'window.__PRELOADED_STATE__ = JSON.parse', "JSON.parse")
        javascript_code = """
        function extractData() {
            const preloadedState = """+preload_state+"""
            return preloadedState;
        }
        """
        ctx = execjs.compile(javascript_code)
        data = ctx.call("extractData")
        return data
    except:
        return None


def get_restaurant_json(response_json: dict):
    try:
        resId = response_json['pages']['current']['resId']
        restaurant_json = response_json['pages']['restaurant'][str(
            resId)]['sections']
        return restaurant_json
    except:
        return None


def get_restaurant_info(response_json: dict):
    restaurant_json = get_restaurant_json(response_json)
    if not restaurant_json:
        return None

    data = {}

    data['name'] = restaurant_json['SECTION_BASIC_INFO']['name']
    data['address'] = restaurant_json['SECTION_RES_CONTACT']['address']
    data['cusines'] = restaurant_json['SECTION_BASIC_INFO']['cuisine_string']
    # rating
    data['rating'] = restaurant_json['SECTION_BASIC_INFO']['rating']['aggregate_rating']
    # Number of Reviews
    data['reviews'] = restaurant_json['SECTION_BASIC_INFO']['rating']['votes']

    # Price range/ Ticket size
    if cfts:= restaurant_json['SECTION_RES_DETAILS']['CFT_DETAILS'].get('cfts'):
        data['price_range'] = [ cft['title'] for cft in cfts]

    # operational status: Open/Permanently closed
    data['status'] = restaurant_json['SECTION_BASIC_INFO']['res_status_text']

    # Dining/Prebook offers
    data['offers'] = []
    if restaurant_json.get('SECTION_DINING_OFFERS_V2') and restaurant_json['SECTION_DINING_OFFERS_V2'].get('offers'):
        for offer in restaurant_json['SECTION_DINING_OFFERS_V2']['offers']:

            offer_data = {
                'heading': offer['heading'],
                'title': offer['title'],
                'sub_title': offer['subtitle'],
                'offer_value': offer['offerDetails'].get('offerVal')
            }
            if offer['offerDetails'].get('offer_details') and offer['offerDetails']['offer_details'].get('offer_value'):
                offer_data['offer_value'] = offer['offerDetails']['offer_details']['offer_value']
            data['offers'].append(offer_data)

    # Top Dishes
    if restaurant_json['SECTION_RES_DETAILS'].get('TOP_DISHES'):
        data['top_dishes'] = restaurant_json['SECTION_RES_DETAILS']['TOP_DISHES']['description'].split(
            ', ')

    # Events details - Business Lunch /chrismas
    if restaurant_json.get('SECTION_EVENTS_HIGHLIGHTS') and restaurant_json['SECTION_EVENTS_HIGHLIGHTS'].get('entities'):

        data['events'] = []
        for entity in restaurant_json['SECTION_EVENTS_HIGHLIGHTS']['entities']:
            for event_id in entity['entity_ids']:
                event = response_json['entities']['EVENTS'][str(event_id)]
                event_data = {
                    'name': event['eventName'],
                    'description': event['description'],
                    'time': event['timingHeading'],
                    'photos': [photo['url'] for photo in event['photos']]
                }
                data['events'].append(event_data)

    # People Say This Place Is Known For
    if restaurant_json['SECTION_RES_DETAILS'].get('KNOWN_FOR'):
        data['known_for'] = restaurant_json['SECTION_RES_DETAILS']['KNOWN_FOR']['knownFor']

    # Facilties : Not found

    if restaurant_json['SECTION_RES_DETAILS'].get('HIGHLIGHTS') and restaurant_json['SECTION_RES_DETAILS']['HIGHLIGHTS'].get('highlights'):
        data['highlights'] = [highlight['text'] for highlight in restaurant_json['SECTION_RES_DETAILS']['HIGHLIGHTS']['highlights']]
    # Restaurant photo

    if restaurant_json['SECTION_IMAGE_CAROUSEL'].get('entities'):
        data['photos'] = []
        for entity in restaurant_json['SECTION_IMAGE_CAROUSEL']['entities']:
            for photo_id in entity['entity_ids']:
                photo = response_json['entities']['IMAGES'][str(photo_id)]
                data['photos'].append(photo['url'])

    # Restaurant Menu
    if restaurant_json['SECTION_RES_DETAILS'].get('IMAGE_MENUS'):
        data['menu'] = restaurant_json['SECTION_RES_DETAILS']['IMAGE_MENUS']['menus']

    # Google Place ID : Not found
    data['google_link'] = ''

    # Lat- Long
    data['lat'] = restaurant_json['SECTION_RES_CONTACT']['latitude']
    data['long'] = restaurant_json['SECTION_RES_CONTACT']['longitude']

    data['google_link'] = f'https://www.google.com/maps/dir/?api=1&destination={data["lat"]},{data["long"]}'
    # Contact
    if restaurant_json['SECTION_RES_CONTACT'].get('is_phone_available'):
        data['phone'] = restaurant_json['SECTION_RES_CONTACT']['phoneDetails']['phoneStr']

    # Website details : Not found

    # Servings hours
    data['serving_hours'] = restaurant_json['SECTION_BASIC_INFO']['timing']['customised_timings']

    return data


def get_menu(response_json: dict, data: dict):
    restaurant_json = get_restaurant_json(response_json)
    if restaurant_json and restaurant_json.get('SECTION_IMAGE_MENU'):
        data['menu'] = restaurant_json['SECTION_IMAGE_MENU']['menuItems']
    return data


def get_order_details(response_json: dict):
    try:
        resId = response_json['pages']['current']['resId']
        items = {}

        for menu in response_json['pages']['restaurant'][str(resId)]['order']['menuList']['menus']:
            items[menu['menu']['name']] = {}
            products = []
            for category in menu['menu']['categories']:

                for item in category['category']['items']:
                    products.append(Item(**item['item']).model_dump())

                if category['category']['name']:
                    items[menu['menu']['name']
                          ][category['category']['name']] = products
                    products = []
                else:
                    items[menu['menu']['name']] = products
        return items
    except Exception as e:
        print(e)
        return None


def zomato(url: str, menu=False, online_order=False):

    credit_count = 1
    zomato_data = {}

    if url.split('/')[-1] in ('menu', 'order', 'info', 'book', 'reviews', 'photos'):
        url = '/'.join(url.split('/')[:-1])

    if html := zomato_scraper(url):
        soup = BeautifulSoup(html, 'html.parser')
    else:
        return None

    if response_json := load_json_from_js(soup):
        zomato_data = get_restaurant_info(response_json)

        if menu:
            credit_count += 1

            menu_url = f'{url}/menu'
            if html := zomato_scraper(menu_url):
                menu_soup = BeautifulSoup(html, 'html.parser')
                if menu_response_json := load_json_from_js(menu_soup):
                    zomato_data = get_menu(menu_response_json, zomato_data)

        if online_order:
            resId = response_json['pages']['current']['resId']

            if navbar_item := response_json['pages']['restaurant'][str(resId)]['navbarSection']:
                for nav_item in navbar_item:
                    if '/order' in nav_item['pageUrl']:

                        order_url = f'{url}/order'
                        if html := zomato_scraper(order_url):

                            order_soup = BeautifulSoup(html, 'html.parser')
                            credit_count += 1
                            if order_response_json := load_json_from_js(order_soup):
                                if order_details := get_order_details(order_response_json):
                                    zomato_data['order'] = order_details
    print(f'Credits used: {credit_count}')
    return zomato_data
