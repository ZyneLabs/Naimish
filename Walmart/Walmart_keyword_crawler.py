import requests
from urllib.parse import urlencode
import json
from bs4 import BeautifulSoup
import traceback
from rq import Queue
from redis import Redis
import time
from hashlib import md5
import os
from Walmart import walmart_parser

APK_KEY=os.getenv('APK_KEY') # Use kW3


class MokeResponse:
    def __init__(self, text, status_code=200):
        self.text = text
        self.status_code = status_code

    def json(self):
        return json.loads(self.text)
    
    def __str__(self):
        return '<Response [{}]>'.format(self.status_code)

# creating a source_dir if not exists

os.makedirs('./source',exist_ok=True)
def walmart_request(url,method,headers={},cookies={},params={},payload={},max_retry=2,cache=True):
    
    # Added cache for debug You can remove it
    if params:
        url = f"{url}?{urlencode(params)}"

    if cookies :
        headers['cookie'] = ";".join([f"{k}={v}" for k, v in cookies.items()])

    file_name = md5(url.encode('utf-8')).hexdigest()

    payload = {
        **payload,
        'key':APK_KEY,
        "method":method,
        'url':url,
    }

    if headers:
        payload['keep_headers'] = True
    
    cookies = {}
    if cache:
        if os.path.exists(f'./source/{file_name}_cookies.json'):
            with open(f'./source/{file_name}_cookies.json','r') as f:
                cookies = json.load(f)
        
        if os.path.exists(f'./source/{file_name}.json'):
            with open(f'./source/{file_name}.json','r') as f:
                response = MokeResponse(f.read(),200)
                print('Exiting from cache')

                return response,cookies
        elif os.path.exists(f'./source/{file_name}.html'):
            with open(f'./source/{file_name}.html','r') as f:
                response = MokeResponse(f.read(),200)
                return response,cookies
        
    

    while max_retry:
        print('Retrying',max_retry)
        try:
            print(payload)
            response = requests.post('https://api.syphoon.com',json=payload,headers=headers)
            print(response.status_code)
            response.raise_for_status()
            
            if cookies_text :=response.headers.get('syphoon_cookie'):

                for cookie in cookies_text.split(';'):
                    k,v = cookie.split('=',1)
                    if k and v.strip():
                        cookies[k.strip()] = v.strip()
            
            if cache:
                try:
                    with open(f'./source/{file_name}.json','w') as f:
                        json.dump(response.json(),f,indent=4)
                        # f.write('\n' +params)
                except:
                    # remove json file
                    os.remove(f'./source/{file_name}.json')
                    with open(f'./source/{file_name}.html','w') as f:
                        f.write(response.text)
                        # f.write('\n' +url)
                
                with open(f'./source/{file_name}_cookies.json','w') as f:
                    json.dump(cookies,f,indent=4)

            return response,cookies
        
        except Exception as ex:
            print(traceback.format_exc())
            max_retry -= 1



def get_products(products_json : dict):
    products = []

    for item in products_json:
        if item.get('__typename'):
            if item['__typename'] != 'Product':
                continue

        product ={
            'name' : item['name'],
            'id' : item['id'],
            'usItemId' : item['usItemId'],
            'url' : 'https://walmart.com'+item['canonicalUrl'] if item.get('canonicalUrl').startswith('/') else item['canonicalUrl'],
            'image' : item.get('image'),
            'average_rating' : item['averageRating'],
            'number_of_reviews' : item['numberOfReviews'],
            'seller_name' : item['sellerName'],
            'seller_id' : item['sellerId'],
            'sales_unit':item['salesUnitType'],
            'additional_offer_count':item['additionalOfferCount'],

        }
        if not product['image']  and item.get('imageInfo'):
            product['image'] = item['imageInfo']['thumbnailUrl']

        if item.get('availabilityStatusDisplayValue'):
            product['avalability'] = item['availabilityStatusDisplayValue']
        elif item.get('availabilityStatusV2'):
            product['avalability'] = item['availabilityStatusV2']['display']
        
        if item.get('priceInfo') and item['priceInfo'].get('itemPrice'):
            product['price'] = item['priceInfo']['itemPrice']
        elif item.get('priceInfo') and item['priceInfo'].get('currentPrice'):
            product['price'] = item['priceInfo']['currentPrice']['priceString']

        if item.get('priceInfo') and item['priceInfo'].get('wasPrice'):
            if isinstance(item['priceInfo']['wasPrice'],dict) and item['priceInfo']['wasPrice'].get('priceString'):
                product['was_price'] = item['priceInfo']['wasPrice']['priceString']
            else:
                product['was_price'] = item['priceInfo']['wasPrice']

        if item.get('priceInfo') and item['priceInfo'].get('unitPrice'):
            if isinstance(item['priceInfo']['unitPrice'],dict) and item['priceInfo']['unitPrice'].get('priceString'):
                product['unit_price'] = item['priceInfo']['unitPrice']['priceString']
            else:
                product['unit_price'] = item['priceInfo']['unitPrice']
        if item.get('priceInfo') and item['priceInfo'].get('listPrice'):
            if isinstance(item['priceInfo']['listPrice'],dict) and item['priceInfo']['listPrice'].get('priceString'):
                product['list_price'] = item['priceInfo']['listPrice']['priceString']
            else:
                product['list_price'] = item['priceInfo']['listPrice']
        if item.get('priceInfo') and item['priceInfo'].get('savingsAmt'):
            product['savings'] = item['priceInfo']['savingsAmt']
        elif item.get('priceInfo') and item['priceInfo'].get('savingsAmount'):
            product['savings'] = item['priceInfo']['savingsAmount']['amount']

        products.append(product)

    return products


def get_products_by_page(url,search_query_json,page,cookies):
    try:
        products = []
        url += f'&page={page}'
        headers = {
            'accept': 'application/json',
            'accept-language': 'en-US',
            'baggage': 'trafficType=customer,deviceType=desktop,renderScope=CSR,webRequestSource=Browser,pageName=searchResults,isomorphicSessionId=wXvgRFPSjrEx5Uk-DjiZF,renderViewId=ad6388d1-2bd8-4944-b2f5-dceb3a24c4d4',
            'content-type': 'application/json',
            'device_profile_ref_id': 'gasp-eitcnsno4oc20vfm1ylm2vfiimsrmvl',
            'downlink': '2.7',
            'dpr': '1',
            'priority': 'u=1, i',
            'referer': url,
            'sec-ch-ua': '"Not/A)Brand";v="8", "Chromium";v="126", "Google Chrome";v="126"',
            'sec-ch-ua-mobile': '?0',
            'sec-ch-ua-platform': '"Linux"',
            'sec-fetch-dest': 'empty',
            'sec-fetch-mode': 'cors',
            'sec-fetch-site': 'same-origin',
            'tenant-id': 'elh9ie',
            'traceparent': '00-181dd6ddb813e15be8d5d29acda4a49f-2d96cf7a8a17b595-00',
            'user-agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36',
            'x-apollo-operation-name': 'Search',
            'x-enable-server-timing': '1',
            'x-latency-trace': '1',
            'x-o-bu': 'WALMART-US',
            'x-o-ccm': 'server',
            'x-o-gql-query': 'query Search',
            'x-o-mart': 'B2C',
            'x-o-platform': 'rweb',
            'x-o-platform-version': 'us-web-1.174.0-37787b886764c3c0bc20b535e3188683604024f1-010715',
            'x-o-segment': 'oaoh',
        }

        search_query_json['affinityOverride'] = 'default'
        search_query_json['pap'] = '{"polaris":{"ms_max_page_within_rerank":0,"ms_slp":0,"ms_triggered":true}}'
        search_query_json['fitmentSearchParams']['affinityOverride'] = 'default'
        search_query_json['fitmentSearchParams']['pap'] = search_query_json['pap']

        search_query_json['page'] = page

        params = {
            'variables': json.dumps(search_query_json)  
        }
        
        page_api_url = 'https://www.walmart.com/orchestra/snb/graphql/Search/3c3a1847bfc8559c28e358801bd4087cd07673ed095e04cefb5c06697fa898e6/search'
        page_response , _ = walmart_request(page_api_url,'get',headers=headers,cookies=cookies,params=params) 

        if page_response.status_code == 200:
            
            products = get_products(page_response.json()['data']['search']['searchResult']['itemStacks'][0]['itemsV2'])

        print(len(products))
    except:
        print(traceback.format_exc())

    return products

def parse_url(url):
    details = {}
    try:
        response , _ = walmart_request(url,'get')
        if response.status_code == 200:
            details = walmart_parser(url,response.text)
    except:
        print(traceback.format_exc())
    return details
        

def walmart_keyword_crawler(url='', keyword='', detailed_records=False, max_results=-1,queue_name='walmart'):

    '''
    url : this is the url of the walmart search page
    keyword : this is the keyword to search
    detailed_records : this is a boolean value to get the detailed records of the products
                if true then it will get the detailed records

    max_results : this is the maximum number of products to get 
                if max_results is -1 then it will get all the products

    '''
    
    return_products = []

    print("Queue name",queue_name)
    q = Queue(queue_name,connection=Redis())
    try:

        if not url and not keyword:
            raise Exception('url or keyword is required')

        if url:
            url = url
        else:
            url = f"https://www.walmart.com/search?query={keyword}"

        response,cookies = walmart_request(url,'get')
        
        no_of_page_to_visit = 0
        visited_pages = 2
        if response.status_code == 200:
            soup = BeautifulSoup(response.text, 'html.parser')
            page_json = json.loads(soup.find('script',id="__NEXT_DATA__").text)['props']['pageProps']
            listing_products = get_products(page_json['initialData']['searchResult']['itemStacks'][0]['items'])

            print('total products',len(listing_products))
            
            no_of_pages = page_json['initialData']['searchResult']['paginationV2']['maxPage']
            no_of_record_per_page = int(page_json['initialData']['searchResult']['paginationV2']['pageProperties']['ps'])
            search_query_json = page_json['initialSearchQueryVariables']
            if max_results == -1:
                max_results = page_json['initialData']['searchResult']['aggregatedCount']
                no_of_page_to_visit = no_of_pages

            elif max_results > len(listing_products):
                no_of_page_to_visit = int((max_results)//no_of_record_per_page)+1

            while len(return_products) < max_results:
                # Print Remain no of results
                # this loop is used for if some results are missing or records are less than max_results
                
                print(f"Remaining results: {max_results - len(return_products)}")

                if no_of_page_to_visit:
                    crawler_jobs = []
                    for page in range(visited_pages, no_of_page_to_visit+1):
                        print(f"Enqueuing job for page {page}")
                        try:
                            job = q.enqueue(get_products_by_page, url=url, search_query_json=search_query_json, page=page, cookies=cookies)
                            crawler_jobs.append(job)
                            print(f"Enqueued job for page {page} with job ID: {job.id}")
                        except Exception as e:
                            print(f"Error enqueuing job for page {page}: {e}")
                    print(f"Enqueued { no_of_page_to_visit} pages")


                    while any(not job.is_finished for job in crawler_jobs): 
                        time.sleep(1)#

                    results = [item for item in job.result for job in crawler_jobs if job.is_finished]

                    print("Dequeued")
                
                    listing_products.extend(results)
                    print('total products',len(listing_products))
                    

                if detailed_records:
                    urls = [item['url'] for item in listing_products[len(return_products):max_results]]

                
                    parser_jobs = []
                    for url in urls:
                        job = q.enqueue(parse_url, url=url)
                        parser_jobs.append(job)

                    while any(not job.is_finished for job in parser_jobs): 
                        print('Waiting')
                        time.sleep(5)

                    results = [job.result for job in parser_jobs if job.is_finished if job.result]
                    return_products.extend(results)
                
                else:
                    return_products = listing_products[:max_results]
                
                # visiting on more page 
                visited_pages = no_of_page_to_visit
                no_of_page_to_visit += 1

                # breaking the loop if we have visited all the pages or we have reached the max results
                if no_of_page_to_visit > no_of_pages or len(return_products) >= max_results:
                    break

            
        return return_products
    except:
        print(traceback.format_exc())

    return return_products

