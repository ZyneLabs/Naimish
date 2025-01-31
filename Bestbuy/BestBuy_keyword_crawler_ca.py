import requests
from urllib.parse import urlencode,urlparse,parse_qs
import json
import traceback
from rq import Queue
from redis import Redis
import time
from hashlib import md5
import os
from BestBuy_Global import bestbuy_parser

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
def bestbuy_request(url,method,headers={},cookies={},params={},payload={},max_retry=2,cache=True):
    
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
            # response = requests.post('https://api.syphoon.com',json=payload,headers=headers)
            response = requests.get(url,headers=headers)
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
        
        product ={
            'name' : item['name'],
            'sku' : item['sku'],
            'url' : 'https://www.bestbuy.ca'+item['productUrl'] if item.get('productUrl').startswith('/') else item['productUrl'],
            'image' : item.get('highResImage'),
            'short_description': item['shortDescription'],
            'average_rating' : item['customerRating'],
            'rating_count' : item['customerRatingCount'],
            'number_of_reviews' : item['customerReviewCount'],
            'regular_price' : item['regularPrice'],
            'categoryName' : item['categoryName'],
        }
        if item.get('salePrice'):
            product['sale_price'] = item['salePrice']

        products.append(product)

    return products


def get_products_by_page(url,page):
    try:
        products = []
        headers = {
            'sec-ch-ua': '"Not/A)Brand";v="8", "Chromium";v="126", "Google Chrome";v="126"',
            'Referer': url,
            'sec-ch-ua-mobile': '?0',
            'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36',
            'sec-ch-ua-platform': '"Linux"',
        }

        params = {
            'categoryid': '',
            'currentRegion': 'ON',
            'include': 'facets, redirects',
            'lang': 'en-CA',
            'page': f'{page}',
            'pageSize': '48',
            'path': '',
            'query': 'iphone 13',
            'exp': 'labels,search_abtesting_personalization_epsilon:b1',
            'contextId': '',
            'isPLP': 'true',
            'hasConsent': 'true',
            'sortBy': 'relevance',
            'sortDir': 'desc',
        }

        if url_param := parse_qs(urlparse(url).query):
            if 'path' in url_param:
                params['path'] = url_param['path'][0]
            params['query'] = url_param['search'][0]

        
        page_api_url = 'https://www.bestbuy.ca/api/v2/json/search'
        page_response , _ = bestbuy_request(page_api_url,'get',headers=headers,params=params) 

        if page_response.status_code == 200:
            
            products = get_products(page_response.json()['products'])

        print(len(products))
    except:
        print(traceback.format_exc())

    return products

def parse_url(url):
    details = {}
    try:
        headers = {
            'sec-ch-ua': '"Not/A)Brand";v="8", "Chromium";v="126", "Google Chrome";v="126"',
            'Referer': url,
            'sec-ch-ua-mobile': '?0',
            'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36',
            'sec-ch-ua-platform': '"Linux"',
        }
        print(url)
        response , _ = bestbuy_request(url,'get',headers=headers)
        if response.status_code == 200:
            details = bestbuy_parser(url,response.text)
    except:
        print(traceback.format_exc())
    return details
        
        

def bestbuy_keyword_crawler(url='', keyword='', detailed_records=False, max_results=-1,queue_name='bestbuy'):

    '''
    url : this is the url of the bestbuy search page
    keyword : this is the keyword to search
    detailed_records : this is a boolean value to get the detailed records of the products
                if true then it will get the detailed records

    max_results : this is the maximum number of products to get 
                if max_results is -1 then it will get all the products

    '''
    
    return_products = []

    print("Queue name",queue_name)
    q = Queue(queue_name,connection=Redis())

    headers = {
            'sec-ch-ua': '"Not/A)Brand";v="8", "Chromium";v="126", "Google Chrome";v="126"',
            'Referer': url,
            'sec-ch-ua-mobile': '?0',
            'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36',
            'sec-ch-ua-platform': '"Linux"',
        }

    params = {
        'categoryid': '',
        'currentRegion': 'ON',
        'include': 'facets, redirects',
        'lang': 'en-CA',
        'page': '1',
        'pageSize': '48',
        'path': '',
        'query': '',
        'exp': 'labels,search_abtesting_personalization_epsilon:b1',
        'contextId': '',
        'isPLP': 'true',
        'hasConsent': 'true',
        'sortBy': 'relevance',
        'sortDir': 'desc',
    }

    try:

        if not url and not keyword:
            raise Exception('url or keyword is required')

        if url:
            if url_param := parse_qs(urlparse(url).query):
                params['query'] = url_param['search'][0]
                if 'path' in url_param:
                    params['path'] = url_param['path'][0]
        else:
            params['query'] = keyword

        api_url = 'https://www.bestbuy.ca/api/v2/json/search'
        response , _ = bestbuy_request(api_url,'get',headers=headers,params=params)
        
        no_of_page_to_visit = 0
        visited_pages = 2
        if response.status_code == 200:
            page_json = response.json()
            listing_products = get_products(page_json['products'])


            print('total products',len(listing_products))
            
            no_of_pages = min(43,page_json['totalPages'])
            no_of_record_per_page = int(page_json['pageSize'])
        
            if max_results == -1:
                max_results = page_json['total']
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
                            job = q.enqueue(get_products_by_page, url=url, page=page)
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

