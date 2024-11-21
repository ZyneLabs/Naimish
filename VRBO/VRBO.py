import requests
from dateutil.parser import parse
import time
import json
import os

def parse_date(date_string):
    parsed_date = parse(date_string)
    return parsed_date.day, parsed_date.month, parsed_date.year
    

def construct_payload(destination, check_in, check_out, adults, property_reviews_group=None,start_index=0,num_results=50):
    
    check_in_day, check_in_month, check_in_year = parse_date(check_in)
    check_out_day, check_out_month, check_out_year = parse_date(check_out)

    json_data = {
        'variables': {
            'context': {
                'siteId': 9001001,
                'locale': 'en_US',
                'eapid': 1,
                'tpid': 9001,
                'currency': 'USD',
                'device': {
                    'type': 'DESKTOP',
                },
                'identity': {
                    'duaid': 'fea7c99b-178d-7fb3-f15c-ae4bdb1642f0',
                    'authState': 'ANONYMOUS',
                },
                'privacyTrackingState': 'CAN_TRACK',
                'debugContext': {
                    'abacusOverrides': [],
                },
            },
            'criteria': {
                'primary': {
                    'dateRange': {
                        'checkInDate': {
                            'day': check_in_day,
                            'month': check_in_month,
                            'year': check_in_year,
                        },
                        'checkOutDate': {
                            'day': check_out_day,
                            'month': check_out_month,
                            'year': check_out_year,
                        },
                    },
                    'destination': {
                        'regionName': destination,
                        'regionId': None,
                        'coordinates': None,
                        'pinnedPropertyId': None,
                        'propertyIds': None,
                        'mapBounds': None,
                    },
                    'rooms': [
                        {
                            'adults': adults,
                            'children': [],
                        },
                    ],
                },
                'secondary': {
                    'counts': [
                        {
                            'id': 'resultsStartingIndex',
                            'value': start_index,
                        },
                        {
                            'id': 'resultsSize',
                            'value': num_results,
                        },
                    ],
                    'booleans': [],
                    'selections': [
                        {
                            'id': 'privacyTrackingState',
                            'value': 'CAN_TRACK',
                        },
                        {
                            'id': 'productCardViewType',
                            'value': 'GRID',
                        },
                        {
                            'id': 'searchId',
                            'value': '99e07843-ccf2-429c-b3d1-d45593b565c4',
                        },
                        {
                            'id': 'sort',
                            'value': 'RECOMMENDED',
                        },
                    ],
                    'ranges': [],
                },
            },
            'destination': {
                'regionName': None,
                'regionId': None,
                'coordinates': None,
                'pinnedPropertyId': None,
                'propertyIds': None,
                'mapBounds': None,
            },
            'shoppingContext': {
                'multiItem': None,
            },
            'returnPropertyType': False,
            'includeDynamicMap': True,
        },
        'operationName': 'PropertyListingQuery',
        'extensions': {
            'persistedQuery': {
                'sha256Hash': 'c5a1252025c741e2e1b8f2e2aa2ef91f325da31b01a72ae8d8e3238fb2348a93',
                'version': 1,
            },
        },
    }

    if property_reviews_group:
            json_data['variables']['criteria']['secondary']['selections'].append({
            'id': 'property_reviews_group',
            'value': property_reviews_group,
        })
    return json_data


def vrbo_search_scraper(key,destination,check_in,check_out,adults,property_reviews_group=None,start_index=0,num_results=50):
    json_data = construct_payload(destination, check_in, check_out, adults,property_reviews_group=property_reviews_group,start_index=start_index,num_results=num_results)
    try:
        headers = {
            'accept': '*/*',
            'accept-language': 'en-GB,en-US;q=0.9,en;q=0.8',
            'client-info': 'shopping-pwa,unknown,unknown',
            'content-type': 'application/json',
            'origin': 'https://www.vrbo.com',
            'priority': 'u=1, i',
            'referer': 'https://www.vrbo.com/',
            'sec-ch-ua': '"Not/A)Brand";v="8", "Chromium";v="126", "Google Chrome";v="126"',
            'sec-ch-ua-mobile': '?0',
            'sec-ch-ua-platform': '"Linux"',
            'sec-fetch-dest': 'empty',
            'sec-fetch-mode': 'cors',
            'sec-fetch-site': 'same-origin',
            'user-agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36',
            'x-enable-apq': 'true',
            'x-page-id': 'page.Hotel-Search,H,20',
            'x-shopping-product-line': 'lodging',
        }

        payload = {
            'url': 'https://www.vrbo.com/graphql',
            'method': 'POST',
            'key': key,
            'keep_headers': True,
            **json_data
        }

        response = requests.post('https://api.syphoon.com', headers=headers, json=payload)

        if response.status_code == 200:
            hotels = [item for item in response.json()['data']['propertySearch']['propertySearchListings'] if item.get('priceSection')]
            return hotels
        else:
            return []
    except Exception as e:
        print(e)
        return []

if __name__ == '__main__':

    # Inputs
    destination = 'Toronto'
    check_in = '2024-12-24'
    check_out = '2024-12-26'
    adults = 2
    property_reviews_group = '4_stars'
    start_index = 0
    num_results = 50
    key=os.getenv('API_KEY')
    
    start_index = 0
    saved_index = 1
    hotels_data = []
    unique_ids = []
    while True:
        try:
            print(start_index)
            data_availability = False
            hotels = vrbo_search_scraper(key,destination,check_in,check_out,adults,property_reviews_group=property_reviews_group,start_index=start_index,num_results=num_results)

            if hotels:
                for hotel in hotels:
                    id = hotel['cardLink']['resource']['value'].split('?')[0].split('/')[-1]
                    if id not in unique_ids:
                        data_availability = True
                        unique_ids.append(id)
                        hotels_data.append(hotel)

            if len(hotels_data) >= 1000 or not data_availability:
                with open(f'{destination}_{check_in}_{check_out}_{saved_index}.json', 'w') as f:
                    json.dump(hotels_data, f, indent=4)
                print('Saved {} hotels in file {}'.format(len(hotels_data,f'{destination}_{check_in}_{check_out}_{saved_index}.json')))
                saved_index += 1
                hotels_data = []
        
            
            if not data_availability:
                break
            start_index += num_results
        except KeyboardInterrupt:
            break

        except Exception as e:
            print(e)
            time.sleep(15)
            # pass