from common.utils import *

def carnab_product_scraper(url,max_retries=5):
    
    while True:

        headers = {
            'accept': 'application/json',
            'accept-language': 'en-GB,en-US;q=0.9,en;q=0.8',
            'origin': 'https://carnab.com',
            'priority': 'u=1, i',
            'referer': 'https://carnab.com/',
            'sec-ch-ua': '"Not/A)Brand";v="8", "Chromium";v="126", "Google Chrome";v="126"',
            'sec-ch-ua-mobile': '?0',
            'sec-ch-ua-platform': '"Linux"',
            'sec-fetch-dest': 'empty',
            'sec-fetch-mode': 'cors',
            'sec-fetch-site': 'cross-site',
            'user-agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36',
        }

        params = {
            'countryId': '1',
            'language': 'en',
        }

        url = 'https://apis.sac-prod.org/carnabapi/events/'+url.split('/')[-1]
        req = send_req_syphoon(PROXY_VENDOR,'get',url,params=params,headers=headers)
        print(req)
        if req.status_code == 200:
            return req
        max_retries -= 1
        if max_retries == 0:
            raise Exception('Maximum number of retries reached')
    