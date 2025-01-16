import re
import execjs
import json
from bs4 import BeautifulSoup
import requests

def get_search_data(raw_data : json):
    if raw_data['pages']['current']['name'] != "search":
        return {}
    
    page_url = raw_data['pages']['current']['pageUrl']
    search_data = raw_data['pages']['search'][page_url]['sections']
    return search_data

def prepare_payload(raw_data : dict): 
    location_data = raw_data['location']['currentLocation']
    appliedFilter = []
    search_meta_data = get_search_data(raw_data)['SECTION_SEARCH_META_INFO']['searchMetaData']
   
   
    for search_filter in  search_meta_data['filterInfo']['railFilters']:
        if search_filter.get('isApplied'):
            search_filter.pop('name',None)
            appliedFilter.append(search_filter)
            
    if location_data.get('addressBlocker','') == 0:
        location_data.pop('addressBlocker')
    
    json_data = {
        'context': 'dineout',
        'filters': '{"searchMetadata":{"previousSearchParams":previousSearchParams_value,"postbackParams":postbackParams_value,"totalResults":'+str(search_meta_data['totalResults'])+',"hasMore":true,"getInactive":false},"dineoutAdsMetaData":{},"appliedFilter":'+json.dumps(appliedFilter)+',"urlParamsForAds":{}}',
    } | location_data

    return json_data

   
def load_json(soup : BeautifulSoup):
    preload_state = soup.find('script', string=re.compile('__PRELOADED_STATE__')).text.replace('window.__PRELOADED_STATE__ = JSON.parse',"JSON.parse")
    javascript_code = """
    function extractData() {
        const preloadedState = """+preload_state+"""
        return preloadedState;
    }
    """
    ctx = execjs.compile(javascript_code)
    data = ctx.call("extractData")
    return data


def get_headers(url,cookies):
        if not cookies:
            return {} ,{}
        if not cookies.get('csrf'):
            csrf_request = requests.get('https://www.zomato.com/webroutes/auth/csrf',headers={
                        'accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7',
                        'accept-language': 'en-US,en;q=0.9',
                        'cache-control': 'max-age=0',
                        'priority': 'u=0, i',
                        'sec-ch-ua': '"Not/A)Brand";v="8", "Chromium";v="126", "Google Chrome";v="126"',
                        'sec-ch-ua-mobile': '?0',
                        'sec-ch-ua-platform': '"Linux"',
                        'sec-fetch-dest': 'document',
                        'sec-fetch-mode': 'navigate',
                        'sec-fetch-site': 'none',
                        'sec-fetch-user': '?1',
                        'upgrade-insecure-requests': '1',
                        'user-agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36',
                    }
                    )
            if csrf_request.status_code == 200:
                csrf = csrf_request.cookies.get('csrf')
                cookies['csrf'] = csrf
            print(csrf_request.text)
        req_headers = {
            'accept': '*/*',
            'accept-language': 'en-US,en;q=0.9',
            'content-type': 'application/json',
            'referer': url,
            'user-agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36',
            'x-zomato-csrft': cookies['csrf'],
        }
        return req_headers, cookies

def extract_restaurant_data(restaurants_json : dict):
    restaurants = []
    for data in restaurants_json:
        try:
            if data.get('type') != 'restaurant':
                continue
            restaurant = data.get('info', {})
            
            restaurant_data = {
                "resId": restaurant.get('resId', None),
                "url": 'https://www.zomato.com'+data.get('cardAction', {}).get('clickUrl', None),
                "name": restaurant.get('name', None),
                "image": restaurant.get('image', {}).get('url', None),
                "rating": {
                    "aggregate_rating": restaurant.get('rating', {}).get('aggregate_rating', None),
                    "rating_text": restaurant.get('rating', {}).get('rating_text', None),
                    "votes": restaurant.get('rating', {}).get('votes', None)
                },
                "cost_for_two": restaurant.get('cft', {}).get('text', None),
                "locality": {
                    "name": restaurant.get('locality', {}).get('name', None),
                    "address": restaurant.get('locality', {}).get('address', None),
                },
                "cuisines": [cuisine.get('name', None) for cuisine in restaurant.get('cuisine', [])],
                "is_promoted": data.get('isPromoted', False),
                "timing": restaurant.get('timing', {}).get('text', None),
                "distance": data.get('distance', None),
            }

            # Check if an offer is available (e.g., gold offer)
            gold_offer = restaurant.get('gold', {})
            if gold_offer.get('gold_offer', False):
                restaurant_data["offer"] = {
                    "offer_type": gold_offer.get('text', None),
                    "offer_value": gold_offer.get('offerValue', None)
                }
            else:
                restaurant_data["offer"] = None
            
            # Return the extracted data
            restaurants.append(restaurant_data)
        
        except Exception as e:
            # Handle errors gracefully
            print(f"An error occurred: {e}")
            
    return restaurants

def process_api_request(raw_json_data,req_data,headers,cookies):
    restaurants_data = []
    
    while True:
        search_meta_data = req_data['SECTION_SEARCH_META_INFO']['searchMetaData']
        previousSearchParams = search_meta_data['previousSearchParams']
        postbackParams = search_meta_data['postbackParams']
        
        json_data = raw_json_data.copy()
        json_data['filters'] = json_data['filters'].replace('previousSearchParams_value', json.dumps(previousSearchParams)).replace('postbackParams_value', json.dumps(postbackParams))

        response = requests.post('https://www.zomato.com/webroutes/search/home',headers=headers,cookies=cookies,json=json_data)
        data =  response.json()
        restaurants_data.extend(extract_restaurant_data(data['sections']['SECTION_SEARCH_RESULT']))
        has_more = data['sections']['SECTION_SEARCH_META_INFO']['searchMetaData']['hasMore']
        if has_more:
            req_data = data['sections']
        else:
            break

    return restaurants_data


def crawl_location(url : str):
    headers = {
        'accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7',
        'accept-language': 'en-GB,en-US;q=0.9,en;q=0.8',
        'priority': 'u=0, i',
        'referer': url,
        'sec-ch-ua': '"Not/A)Brand";v="8", "Chromium";v="126", "Google Chrome";v="126"',
        'sec-ch-ua-mobile': '?0',
        'sec-ch-ua-platform': '"Linux"',
        'sec-fetch-dest': 'document',
        'sec-fetch-mode': 'navigate',
        'sec-fetch-site': 'same-origin',
        'sec-fetch-user': '?1',
        'upgrade-insecure-requests': '1',
        'user-agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36',
    }
    restaurants_data = []
    response = requests.get(url,headers,cookies=cookies)
    print(response)
    soup = BeautifulSoup(response.text, 'html.parser')
   
    data = load_json(soup)
    
    search_data = get_search_data(data)
    restaurants_data.extend(extract_restaurant_data(search_data['SECTION_SEARCH_RESULT']))
    raw_json_data = prepare_payload(data)

    headers,cookies = get_headers(url,response.cookies)
    req_data = get_search_data(data)
    restaurants_data.extend(process_api_request(raw_json_data,req_data,headers,cookies))

    return restaurants_data

def crawl_zomato(url : str):
    
    cookies = {
        'fre': '0',
        'rd': '1380000',
        'zl': 'en',
        'fbtrack': 'ac9c3543f07a6c87decbec878815778c',
        '_gcl_au': '1.1.1584101446.1736166538',
        '_fbp': 'fb.1.1736166538864.582029324633959',
        '_ga_LJCDTHF5JB': 'GS1.2.1736170629.1.0.1736170629.0.0.0',
        'uspl': 'true',
        '_ga_3RRGJR50N2': 'GS1.2.1736170676.1.1.1736170710.0.0.0',
        '_ga_96J56M9NW7': 'GS1.2.1736170721.1.1.1736170727.54.0.0',
        '_ga_N2QG83CZZ2': 'GS1.2.1736170777.1.1.1736170973.0.0.0',
        'fbcity': '51',
        'PHPSESSID': 'af8c8b05bb9aeb15d8dfa0016d248559',
        'csrf': '14f4047616887005880869b34626b123',
        'ak_bmsc': 'CBEB9AEA3AC75D68E448ED9C478248C9~000000000000000000000000000000~YAAQtIosMWwpyWCUAQAAiHmeaBoG6A6GAE4KbtT0tjiS67+rMZZh/ZcZRQJlk89Yxt5noZKKbP/ReCaJWjEaHw2NM5vJUqZEMC1z+bUIAAQEKau/C8e1HAmCiV7NA4SWftiFK/Xuh1VWsTQYqq3u76BZ301xFrKJjcZbmaeGpNPEArgDzwWDZFgilEhwE8n14YRRHct785XYsUKeU0j1bkc42iyEN4euuyjGcXDd5kx4QY4rUzQUYfyIa6ocgv3PDR0g2NluGWSrHrKOn3cr1m5/T8M5NBnHZ4rPTE7nrp/g9yZX9VqoPriBXZ4TwmyWQa64eFIAPWG3cH8Xl6QbBhaqHFl0GmlYSSPPDQ4f/qMihOc/uS+fCiOf6+Uo5PbD7/1exrXuamXTdpMtRnMDusHBMMsiQ6VgXnJtt51jN55Hqw==',
        '_gid': 'GA1.2.508851978.1736922004',
        'ltv': '51502',
        'lty': '51502',
        'locus': '%7B%22addressId%22%3A0%2C%22lat%22%3A25.24555%2C%22lng%22%3A55.304397%2C%22cityId%22%3A51%2C%22ltv%22%3A51502%2C%22lty%22%3A%22subzone%22%2C%22fetchFromGoogle%22%3Afalse%2C%22dszId%22%3A3792%7D',
        '_ga': 'GA1.1.281351775.1736166537',
        '_abck': 'B2AE55627456E0F11AC085DD18FC6747~-1~YAAQvYosMQsImEaUAQAAAKzAaA3aMAlSLZ72BCXRAXAQq3kbkp95YW7gENplw4yqcebkBkusTRyiSqm16SdL8hkHGlvfgjd0YA8vm2AETiC7cNcHensplQK9vBAwvbUzKW9auzsBYt62eu1fBZOjBemv6xBiBq9CtA+YsOmbdgicvqwFHEIPQoOHsdilwAWakekYdXlJ30LjnO2CBAICw/Xorzy4/8CThzVjbj1LyrJRShOs3G0y5MchjV/W5JJKTlNgJg0JGaDrvZwGU5MHnC0tZ2+ZFk3lu0n7N/JLEkklUmcE+Fg9xZkmyBEJCoo+RGE7hQybos4umufD/uVQLL2DF156xcrF0e66kHV+rt1jU4kV6Jm4LoSP/RV2+RYzVADzXra+Yto3G55DKiWHspErwf220ZMrj+LYqvcrHeUwEH14c3EO~-1~-1~-1',
        '_ga_J180KJM1D0': 'GS1.2.1736924200.6.1.1736924245.15.0.0',
        '_ga_3NLB2V9G4W': 'GS1.2.1736924200.6.1.1736924245.15.0.0',
        '_ga_2XVFHLPTVP': 'GS1.1.1736924199.7.1.1736924251.8.0.0',
        'AWSALBTG': '4ziqUzWNhH+yg4z3MyF/0zzxsV9LkMSGQh7tbV5X3578UTL/XVeN61GeVFqOnqQFtiA0KxIj+uTssd+y6S3k6vhJ3CjoXZwmy5gtUuRP1Xa5iEajAfvQdMOZjRLWKCx1d6DFCx/4VIQIivjLbXZeWzQhn8NJHXI21zx/32Jzyxcj',
        'AWSALBTGCORS': '4ziqUzWNhH+yg4z3MyF/0zzxsV9LkMSGQh7tbV5X3578UTL/XVeN61GeVFqOnqQFtiA0KxIj+uTssd+y6S3k6vhJ3CjoXZwmy5gtUuRP1Xa5iEajAfvQdMOZjRLWKCx1d6DFCx/4VIQIivjLbXZeWzQhn8NJHXI21zx/32Jzyxcj',
        '_dd_s': 'rum=0&expire=1736925283477',
    }

    headers = {
        'accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7',
        'accept-language': 'en-GB,en-US;q=0.9,en;q=0.8',
        'priority': 'u=0, i',
        'referer': 'https://www.zomato.com/dubai/rooftop',
        'sec-ch-ua': '"Not/A)Brand";v="8", "Chromium";v="126", "Google Chrome";v="126"',
        'sec-ch-ua-mobile': '?0',
        'sec-ch-ua-platform': '"Linux"',
        'sec-fetch-dest': 'document',
        'sec-fetch-mode': 'navigate',
        'sec-fetch-site': 'same-origin',
        'sec-fetch-user': '?1',
        'upgrade-insecure-requests': '1',
        'user-agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36',
    }
    response = requests.get(url, headers=headers,cookies=cookies)

    restaurants = []
    soup = BeautifulSoup(response.text, 'html.parser')
    data = load_json(soup)
    
    for location  in data['pages']['city']['51']['sections']['SECTION_POPULAR_LOCATIONS']['locations']:
        restaurants.extend(crawl_location(location['url']))
