
from celery_worker import celery_app
from common import *

db = client['automalluae']
product_collection = db['urls']
cache_collection = db['cache']
error_collection = db['error']

base_headers  =  {
    'accept': 'application/json, text/plain, */*',
    'accept-language': 'en',
    'authorization': 'Bearer eyJhbGciOiJSUzI1NiIsImtpZCI6InJSNEZMVXI3ajRSZWVMX3lrYWo5Q0FvREhVZmRYRUktNkVLSWV1eDRXemciLCJ0eXAiOiJKV1QifQ.eyJhdWQiOiI5ZTNhN2Y2OC00Zjc5LTQwOGYtODQwMi1lZTU5ZmZiZjVhMTYiLCJpc3MiOiJodHRwczovL2lkZW50aXR5LmFsZnV0dGFpbW9ubGluZS5jb20vOWU3N2Y4NTQtYTAzYy00N2I4LWE3YTItMmU3YWVhOTdjOWJlL3YyLjAvIiwiZXhwIjoxNzE5NTc4MjM0LCJuYmYiOjE3MTk0OTE4MzQsInN1YiI6ImFkODNkM2RlLWJhYWYtNDhhMS04NjczLTdmMjUzZWMwNTIwZCIsIm9iamVjdElkIjoiYWQ4M2QzZGUtYmFhZi00OGExLTg2NzMtN2YyNTNlYzA1MjBkIiwiZW1haWwiOiJFSVQuTW9iaWxpdHlAYWxmdXR0YWltLmNvbSIsInN0cm9uZ0F1dGhlbnRpY2F0aW9uUGhvbmVOdW1iZXIiOiIrOTcxMDAwMDAwMDAwIiwidGl0bGUiOiJNUiIsIm5hbWUiOiJFSVQgTW9iaWxpdHkiLCJmaXJzdE5hbWUiOiJFSVQiLCJsYXN0TmFtZSI6Ik1vYmlsaXR5IiwicGhvbmUiOiIwIiwiY291bnRyeUNvZGUiOiJBRSIsInRpZCI6IjllNzdmODU0LWEwM2MtNDdiOC1hN2EyLTJlN2FlYTk3YzliZSIsImF6cCI6IjllM2E3ZjY4LTRmNzktNDA4Zi04NDAyLWVlNTlmZmJmNWExNiIsInZlciI6IjEuMCIsImlhdCI6MTcxOTQ5MTgzNH0.ktuwMxTsrP__-lfYSMq4NISXdZ_ZRL0mXv90T6TZX86lGqxaJHG7E1ReAcd1Qp65fH1CNhppp314g8ioogJxKERW-uiH-AWQ9aQlrd7AWfyNkw1Mf9f1Tiqd-3F3pg7nljYymOyBBovyXqqn1EpoBamLj7S3NXmb8pPpUCFYQp9AEzDeQNs1yfh34BSJdWx1QZf_xBPbj2mKeomZKtR5WXcvI3CYWcyfgU9zLomAmjRZUUGhjqxWwCFv8bhoLNj7yA7-5MSGXE12fVlafFwvnN_EkYdd6lUyxCOePK8ealbMo3MBA9vPyzhp4g_ZOL3J1OK3o5D13FhwlZS5T-HPQQ',
    'priority': 'u=1, i',
    'referer': 'https://www.automalluae.com/en/used-cars-shop/',
    'request-context': 'appId=cid-v1:c98ad234-3df7-4249-af42-0f70f5b3f4cb',
    'request-id': '|46c8b44630d34ee99b41bcde633059b3.6997723a8cbc40dd',
    'sec-ch-ua': '"Not/A)Brand";v="8", "Chromium";v="126", "Google Chrome";v="126"',
    'sec-ch-ua-mobile': '?0',
    'sec-ch-ua-platform': '"Windows"',
    'sec-fetch-dest': 'empty',
    'sec-fetch-mode': 'cors',
    'sec-fetch-site': 'same-origin',
    'traceparent': '00-46c8b44630d34ee99b41bcde633059b3-6997723a8cbc40dd-01',
    'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36',
    'x-content-type-options': 'nosniff',
}


def check_cache_for(data):
    return cache_collection.find_one(data)


def get_authorization():
    req = send_req_syphoon(PROXY_VENDOR,'get','https://www.automalluae.com/en/used-cars-shop/',payload={'keep_headers':True})
    print(req)
    print(req.text)
    try:
        return req.headers['set-cookie'].split('AUTH_TOKEN=')[1].split(';')[0]
    except:
        return None
    
@celery_app.task(queue='automalluae')
def crawl_urls():
    main_api_url = 'https://www.automalluae.com/bff/v2/vehicles?q=type=auto_used_automobiles|price%3E0|attributes.auto_sap_vehicle_status.values.EN=AV,CT&fields=id|price|discount|equatedMonthlyInstallment|attributes.auto_sap_model_year.values.EN%20as%20modelYear|attributes.auto_sap_model.values.EN%20as%20model|attributes.auto_sap_engine_capacity.values.EN%20as%20engineCapacity|attributes.auto_sap_odometer.values.EN%20as%20odometer|attributes.auto_used_car_image1.values.EN%20as%20image|attributes.auto_sap_vehicle_status.values.EN%20as%20vehicleStatus|attributes.auto_vehicle_location.values.EN%20as%20vehicleLocation|attributes.auto_sap_model_grade.values.EN%20as%20modelGrade|attributes.auto_basic_exterior_colours.values.EN%20as%20exteriorColours|attributes.auto_IsHotOffer.values.EN%20as%20isHotOffer|attributes.auto_sap_make.values.EN%20as%20make|attributes.auto_sap_model_code.values.EN%20as%20modelCode|attributes.auto_sap_body_type.values.EN%20as%20bodyType&sort=price=1'
    auth_token = get_authorization()
    start_index = 0
    
    while True:
        try:
            saved_page = check_cache_for(
                {'input': {'url': main_api_url, 'page': start_index}}
            )
            if saved_page is not None:
                data = saved_page['data']

            else:

                base_headers['paging-info'] =f'start-index={start_index}|no-of-records=28'
                base_headers['authorization'] = f'Bearer {auth_token}'
                # res = send_req_syphoon(0, 'GET', main_api_url, headers=base_headers)
                res = requests.get(main_api_url,headers=base_headers)
            
                data = res.json()

            cache_collection.insert_one(
                    {
                        'input': {
                            'url': main_api_url,
                            'page': start_index
                        },
                        'data': data,
                        'updated_at': datetime.now(),
                        'data_format': 'json',
                        'info_type': 'crawl',
                        'info_subtype': 'url_crawl',
                    }
                )
            if len(data) == 0: break
            start_index += len(data)

            products = [
                
                {'url':f'https://www.automalluae.com/en/used-cars-shop/details/{item["id"].lower()}',
                'make':item['make'],
                'model':item['model'],
                'modelYear' : item['modelYear'],
                'scraped':0}
                
                for item in data 

                if product_collection.find_one({'url':f'https://www.automalluae.com/en/used-cars-shop/details/{item["id"]}'}) is None
            ]

            product_collection.insert_many(products)

        except Exception as ex:
            error_collection.insert_one(
                {
                  
                    'url': main_api_url,
                    'page': start_index,
                    'error': str(ex),
                    'traceback': traceback.format_exc(),
                }
            )
