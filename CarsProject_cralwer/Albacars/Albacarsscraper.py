from common.utils import *

def albacars_scraper(url,max_retries=5):
    
    while True:
        req = send_req_syphoon(PROXY_VENDOR,'get',url)
        print(req)
        if req.status_code == 200:
            return req
        max_retries -= 1
        if max_retries == 0:
            raise Exception('Maximum number of retries reached')
    