import requests
from urllib.parse import urlencode,urlparse,parse_qs
import json
import traceback
from rq import Queue
from redis import Redis
from bs4 import BeautifulSoup
import time
from hashlib import md5
import os
from BestBuy_Global import bestbuy_parser
from dotenv import load_dotenv
load_dotenv(override=True)

API_KEY=os.getenv('API_KEY') # Use kW3

print(API_KEY)
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
        'key':API_KEY,
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
            # response = requests.get(url,headers=headers)
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



def get_products(page_soup : BeautifulSoup):
    products = page_soup.select('.sku-item-list .sku-item[data-sku-id]')

    if not products:
        return []
    
    products_list = []
    for product in products:
        product_dict = {}
        product_dict['url'] ='https://www.bestbuy.com'+product.select_one('.sku-title a')['href']
        product_dict['name'] = product.select_one('.sku-title a').text.strip()
        product_dict['retail_price'] = float(product.select_one('div[data-testid="customer-price"] span').text.strip().replace('$','').replace(',',''))
        
        product_json = None
        
        if product_json := product.select_one('.sku-list-item-price script[type="application/json"]'):
            # print(product_json.text)
            product_json = json.loads(product_json.text)
            if product_json['app'].get('priceDomain') and product_json['app']['priceDomain'].get('regularPrice'):
                product_dict['retail_price'] = product_json["app"]["priceDomain"]["customerPrice"]
                product_dict['list_price'] = product_json['app']['priceDomain']['regularPrice']
                product_dict['saving_amt'] = product_json['app']['priceDomain']['totalSavings']
                product_dict['saving_per'] = product_json['app']['priceDomain']['totalSavingsPercent']



        if sale_unit := product.select_one('.priceView-subscription-units'):
            product_dict['sale_unit'] = sale_unit.text.strip()

        if sale_period := product.select_one('.priceView-price-disclaimer'):
            product_dict['sale_period'] = sale_period.text.strip()


        product_dict['image'] = product.select_one('img')['src'].split(';')[0]

        if product.find('span',string='Model:'):
            product_dict['model'] = product.find('span',string='Model:').find_next_sibling().text
        
        if product.find('span',string='SKU:'):
            product_dict['sku'] = product.find('span',string='SKU:').find_next_sibling().text
        
        if variations := product.select('div.variation-info .product-variation-header'):
            product_dict['variations'] = {}
            for variation in variations:
                val = variation.select_one('.product-variation-name').text.strip()
                product_dict['variations'][val] = variation.select_one('.hover-name').text.strip()
        
        if review_soup := product.select_one('div.ratings-reviews'):
            if 'Not Yet Reviewed' not in review_soup.text:
                product_dict['rating'] = review_soup.text.split('out of')[0].replace('Rating','').strip()
                product_dict['reviews'] = review_soup.select_one('.c-reviews').text.replace('(','').replace(')','').strip()


        if product_json:
            if product_json['app'].get('productInfo') and product_json['app']['productInfo'].get('brand'):
                product_dict['brand'] = product_json['app']['productInfo'].get('brand')

            if product_json['app'].get('priceDomain') and product_json['app']['priceDomain'].get('offerQualifiers'):
                offers = []
                for offer in product_json['app']['priceDomain']['offerQualifiers']:
                    offers.append(offer['offerName'])
                if offers:
                    product_dict['no_offers'] = len(offers)
                    product_dict['offers'] = ' | '.join(offers)
        products_list.append(product_dict)
    return products_list


def get_products_by_page(url,page):
    try:
        products = []
        if '?' in url:
            url += '&cp='+str(page)
        else:
            url += '?cp='+str(page)

        page_response , _ = bestbuy_request(url,'get') 

        if page_response.status_code == 200:
            soup = BeautifulSoup(page_response.text,'html.parser')
            products = get_products(soup)

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

    try:

        if not url and not keyword:
            raise Exception('url or keyword is required')
        
        if keyword:
            url = 'https://www.bestbuy.com/site/searchpage.jsp?st='+keyword

        response , _ = bestbuy_request(url,'get')
        with open('response.html','w') as f:
            f.write(response.text)
        soup = BeautifulSoup(response.text,'html.parser')

        no_of_page_to_visit = 0
        visited_pages = 2
        if response.status_code == 200:
            
            listing_products = get_products(soup)


            print('total products',len(listing_products))
            if pages_list := soup.select('.paging-list .page-item'):
                no_of_pages = int(pages_list[-1].text)
            
            no_of_record_per_page = len(listing_products)
        
            if max_results == -1:
                max_results = int(soup.select_one('.item-count').text.split('')[0])
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

