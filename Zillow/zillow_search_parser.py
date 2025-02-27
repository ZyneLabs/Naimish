import json
from bs4 import BeautifulSoup
import requests
import traceback
import os
from dotenv import load_dotenv

load_dotenv(override=True)

APIKEY = os.getenv("APIKEY")

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



def search_parser(html : str) -> dict | None:

    soup = BeautifulSoup(html,'lxml')

    if json_text_soup := soup.select_one('#__NEXT_DATA__'):
        page_json = json.loads(json_text_soup.text)

    else:
        return 
    try:
        search_json = page_json['props']['pageProps']['searchPageState']['cat1']['searchList']
        details = {
            'url' : 'https://www.zillow.com'+page_json['props']['pageProps']['searchPageState']['searchPageSeoObject']['baseUrl'],
            'title' : search_json['listResultsTitle'],
            'total_listings' : search_json['totalResultCount'],
            'total_pages' : search_json['totalPages'],
        }
        if search_json.get('pagination'):
            details['previous_page'] = 'https://www.zillow.com'+ search_json['pagination']['previousUrl'] if search_json['pagination'].get('previousUrl') else None
            details['next_page'] = 'https://www.zillow.com'+ search_json['pagination']['nextUrl'] if search_json['pagination'].get('nextUrl') else None

        property_list_json = page_json['props']['pageProps']['searchPageState']['cat1']['searchResults'].get('listResults',[])

        properties = []
        for property_json in property_list_json:

            address = {
                "street": property_json.get("addressStreet", ""),
                "city": property_json.get("addressCity", ""),
                "state": property_json.get("addressState", ""),
                "zipcode": property_json.get("addressZipcode", "")
            }
            full_address = f"{address['street']}, {address['city']}, {address['state']} {address['zipcode']}"
            property_details = {
                'url' : property_json['detailUrl'],
                'zillow_id' : property_json['zpid'],
                'address' : full_address,
                **property_json.get('latLong',{}),
                'primary_image' : property_json.get('imgSrc','N/A'),
                'status' : property_json['statusText'],
                'price' : property_json.get("unformattedPrice", 0),
                'currency' : property_json['countryCurrency'],
                'bedrooms' : property_json.get("beds", 0),
                'bathrooms' : property_json.get("baths", 0),
                'area' : property_json.get("area", 0),
                'property_detail_text' : property_json.get("flexFieldText", "N/A"),
                'broker_name': property_json.get('brokerName','N/A'),
                'photos': [ img['url'] for img in property_json['carouselPhotos']] if property_json.get('carouselPhotos') else [],
                'detailed_info' : property_json['hdpData'].get('homeInfo')

            }   
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
        response = zillow_scraper(url)
        data = search_parser(response.text)
        
        return data
    except:
        print(traceback.print_exc())
        return 
    