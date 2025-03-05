import json
from bs4 import BeautifulSoup
import requests
import traceback
import os
from dotenv import load_dotenv
import urllib.parse

load_dotenv(override=True)

APIKEY = os.getenv("APIKEY")

proxies = {
    'https':os.getenv('PROXY'),
    'http':os.getenv('PROXY'),
}

def zillow_scraper(url:str) -> requests.Response | None:
    try:
        payload = {
            "key" : APIKEY, #kw3
            "method" : "GET",
            "url" : url,
            "keep_headers": True
        }
        headers = {
            'accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7',
            'accept-language': 'en-US,en;q=0.9',
            'cache-control': 'max-age=0',
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

        response = requests.post('https://api.syphoon.com/',json=payload,headers=headers)
        return response
    except:
        print(traceback.print_exc())
        
def prepar_payload(url):
    parsed_url = urllib.parse.urlparse(url)
    query_params = urllib.parse.parse_qs(parsed_url.query)
    encoded_json = query_params.get("searchQueryState", [None])[0]
    if encoded_json:
        
        decoded_json = urllib.parse.unquote(encoded_json)
        json_data = json.loads(decoded_json)
        json_data =  {
            'searchQueryState':json_data,
                'wants': {
                    'cat1': [
                        'mapResults',
                        'listResults',
                    ],
                },
                'requestId': 3,
                'isDebugRequest': True,
            }
        return json_data
    else:
        print("searchQueryState parameter not found.")

    
def search_scraper(url : str) -> requests.Response | None:
    try:
        headers = {
            'accept': '*/*',
            'accept-language': 'en-US,en;q=0.9',
            'content-type': 'application/json',
            'origin': 'https://www.zillow.com',
            'priority': 'u=1, i',
            'referer': url,
            'sec-ch-ua': '"Not/A)Brand";v="8", "Chromium";v="126", "Google Chrome";v="126"',
            'sec-ch-ua-mobile': '?0',
            'sec-ch-ua-platform': '"Linux"',
            'sec-fetch-dest': 'empty',
            'sec-fetch-mode': 'cors',
            'sec-fetch-site': 'same-origin',
            'user-agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36',
        }

        json_data = prepar_payload(url)
        response = requests.put('https://www.zillow.com/async-create-search-page-state',headers=headers, json=json_data,proxies=proxies)
        response.raise_for_status()
        return response
    except:
        print(traceback.print_exc())
        
def search_parser(raw_data : str|dict) -> dict | None:
    if isinstance(raw_data, str):
        soup = BeautifulSoup(raw_data,'lxml')
        if json_text_soup := soup.select_one('#__NEXT_DATA__'):
            page_json = json.loads(json_text_soup.text)

        else:
            return 
    try:
        if isinstance(raw_data, str):
            search_json = page_json['props']['pageProps']['searchPageState']['cat1']['searchList']
            url = page_json['props']['pageProps']['searchPageState']['searchPageSeoObject']['baseUrl']
            property_list_json = page_json['props']['pageProps']['searchPageState']['cat1']['searchResults'].get('listResults',[])

        if isinstance(raw_data, dict):
            search_json = raw_data['cat1']['searchList']
            url = raw_data['searchPageSeoObject']['baseUrl']
            
            property_list_json = []
            if raw_data['cat1']['searchResults'].get('mapResults'):
                property_list_json = raw_data['cat1']['searchResults'].get('mapResults',[])
            if raw_data['cat1']['searchResults'].get('listResults'):
                property_list_json.extend(raw_data['cat1']['searchResults']['listResults'])

        details = {
            'url' : 'https://www.zillow.com'+ url,
            'title' : search_json['listResultsTitle'],
            'total_listings' : search_json['totalResultCount'],
            'total_pages' : search_json['totalPages'],
        }
        if search_json.get('pagination'):
            details['previous_page'] = 'https://www.zillow.com'+ search_json['pagination']['previousUrl'] if search_json['pagination'].get('previousUrl') else None
            details['next_page'] = 'https://www.zillow.com'+ search_json['pagination']['nextUrl'] if search_json['pagination'].get('nextUrl') else None

        

        properties = []
        for property_json in property_list_json:
            
            if property_json.get('addressStreet'):
                address = {
                    "street": property_json.get("addressStreet", ""),
                    "city": property_json.get("addressCity", ""),
                    "state": property_json.get("addressState", ""),
                    "zipcode": property_json.get("addressZipcode", "")
                }
                full_address = f"{address['street']}, {address['city']}, {address['state']} {address['zipcode']}"
            else:
                full_address = property_json.get("address")

            if property_json.get("beds"):
                beds = property_json.get("beds")
            else:
                beds = property_json.get('minBeds')
            
            if property_json.get("baths"):
                baths = property_json.get("baths")
            else:
                baths = property_json.get('minBaths')
            
            if property_json.get("area"):
                area = property_json.get("area")
            else:
                area = property_json.get('minArea')
            
            property_details = {
                'url' : 'https://www.zillow.com'+property_json['detailUrl'] if property_json.get('detailUrl').startswith('/') else property_json.get('detailUrl'),
                'zillow_id' : property_json['zpid'] if property_json.get('zpid') else None,
                'zillow_plid' : property_json['plid'] if property_json.get('plid') else None,
                'zillow_lotid' : property_json['lotId'] if property_json.get('lotId') else None,
                'address' : full_address,
                **property_json.get('latLong',{}),
                'primary_image' : property_json.get('imgSrc','N/A'),
                'status' : property_json.get('statusText'),
                'price' : property_json.get("unformattedPrice", 0),
                'currency' : property_json.get('countryCurrency','USD'),
                'bedrooms' : beds,
                'bathrooms' : baths,
                'area' : area,
                'property_detail_text' : property_json.get("flexFieldText", "N/A"),
                'broker_name': property_json.get('brokerName','N/A'),
                'photos': [ img['url'] for img in property_json['carouselPhotos']] if property_json.get('carouselPhotos') else [],
                'detailed_info' : property_json['hdpData'].get('homeInfo') if property_json.get('hdpData') else None
            }   

            if property_json.get('unitCount'):
                property_details['unit_count'] = property_json.get('unitCount')

            properties.append(property_details)
        details['properties'] = properties
        return details
    except Exception as e:
        print(traceback.print_exc())
        return
        
def zillow_search(url):
    '''
    For any lising URL.
    '''
    try:
        if 'searchQueryState' in url:
            response = search_scraper(url)
            data = search_parser(response.json())
        else:
            response = zillow_scraper(url)
            data = search_parser(response.text)
            
        return data
    except:
        print(traceback.print_exc())
        return 
