from common.utils import * 

def reddit_scraper(url):
    return send_req_syphoon(PROXY_VENDOR,'get',url)