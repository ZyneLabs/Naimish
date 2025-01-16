import scrapy
import json
import re
from bs4 import BeautifulSoup
from scrapy.http import JsonRequest
import execjs
import requests
from scrapy.http.cookies import CookieJar

class ZomatoSpider(scrapy.Spider):
    name = 'zomato'
    
    def __init__(self, url=None, *args, **kwargs):
        super(ZomatoSpider, self).__init__(*args, **kwargs)
        self.start_urls = [url] 
        print("INITIAL")
        print(url)

    def parse(self, response):
        try:
            soup = BeautifulSoup(response.text, 'html.parser')
            data = self.load_json(soup)
            
            search_data = self.get_search_data(data)
            restaurants = self.extract_restaurant_data(search_data['SECTION_SEARCH_RESULT'])
            
            for restaurant in restaurants:
                yield restaurant
            
            raw_json_data = self.prepare_payload(data)
            
            json_data = raw_json_data.copy()

            search_meta_data = self.get_search_data(data)['SECTION_SEARCH_META_INFO']['searchMetaData']
            previousSearchParams = json.dumps(search_meta_data['previousSearchParams'])
            postbackParams = json.dumps(search_meta_data['postbackParams'])

            json_data['filters'] = json_data['filters'].replace('previousSearchParams_value', previousSearchParams).replace('postbackParams_value', postbackParams)

            next_url = 'https://www.zomato.com/webroutes/search/home'
            headers,cookies = self.get_headers(response)
            yield JsonRequest(
                url=next_url, 
                method='POST', 
                body=json.dumps(json_data), 
                headers=headers, 
                cookies=cookies, 
                callback=self.parse_more,
                meta = {'raw_json_data': raw_json_data, 'req_headers': headers, 'req_cookies': cookies}
            )
        except:
            # Retry Same Page
            yield scrapy.Request(response.url, callback=self.parse)

    def parse_more(self, response):
        data = response.json()
        
        restaurants = self.extract_restaurant_data(data['sections']['SECTION_SEARCH_RESULT'])
        # log number of restaurants

        self.logger.info(f"Found {len(restaurants)} restaurants")
        for restaurant in restaurants:
            yield restaurant

        has_more = data['sections']['SECTION_SEARCH_META_INFO']['searchMetaData']['hasMore']
        req_headers = response.meta['req_headers']
        req_cookies = response.meta['req_cookies']
        print(has_more)
        if has_more and len(restaurants) > 0:
            # Prepare the next page request with updated json_data
            search_meta_data = data['sections']['SECTION_SEARCH_META_INFO']['searchMetaData']
            previousSearchParams = search_meta_data['previousSearchParams']
            postbackParams = search_meta_data['postbackParams']
            
            # Create a fresh json_data for the next page
            json_data = response.meta['raw_json_data'].copy()
            json_data['filters'] = json_data['filters'].replace('previousSearchParams_value', json.dumps(previousSearchParams)).replace('postbackParams_value', json.dumps(postbackParams))

            next_url = 'https://www.zomato.com/webroutes/search/home'
            
            yield JsonRequest(
                url=next_url, 
                method='POST', 
                body=json.dumps(json_data), 
                headers=req_headers, 
                cookies=req_cookies, 
                callback=self.parse_more,
                meta = {'raw_json_data': response.meta['raw_json_data'],
                        'req_headers': req_headers,
                        'req_cookies': req_cookies}
            )

    def get_headers(self, response):
        cookies = response.headers.getlist('Set-Cookie')
        if not cookies:
            self.logger.warning("No Set-Cookie header found in the response.")
            return {} ,{} # Or some default value
        req_cookies = {}
        for cookie in cookies:
            name, value = cookie.decode('utf-8').split(';')[0].split('=')
            req_cookies[name] = value
        if not req_cookies.get('csrf'):
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
                req_cookies['csrf'] = csrf
            print(csrf_request.text)
        req_headers = {
            'accept': '*/*',
            'accept-language': 'en-US,en;q=0.9',
            'content-type': 'application/json',
            'referer': self.start_urls[0],
            'user-agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36',
            'x-zomato-csrft': req_cookies['csrf'],
        }
        return req_headers, req_cookies
    
    def load_json(self, soup):
        preload_state = soup.find('script', string=re.compile('__PRELOADED_STATE__')).text.replace('window.__PRELOADED_STATE__ = JSON.parse',"JSON.parse")
        javascript_code = f"""
        function extractData() {{
            const preloadedState = {preload_state}
            return preloadedState;
        }}
        """
        ctx = execjs.compile(javascript_code)
        data = ctx.call("extractData")
        return data

    def get_search_data(self, raw_data):
        if raw_data['pages']['current']['name'] != "search":
            return {}

        page_url = raw_data['pages']['current']['pageUrl']
        search_data = raw_data['pages']['search'][page_url]['sections']
        return search_data

    def extract_restaurant_data(self, restaurants_json):
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
                self.logger.error(f"An error occurred while extracting restaurant data: {e}")
        
        return restaurants

    def prepare_payload(self, raw_data):
        location_data = raw_data['location']['currentLocation']
        appliedFilter = []
        search_meta_data = self.get_search_data(raw_data)['SECTION_SEARCH_META_INFO']['searchMetaData']
        
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
        self.raw_json_data = json_data
        return json_data