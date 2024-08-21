import os
import requests

XHEAD = os.environ.get('PROXY_VENDOR')


def crawl_request_scraper(start,csrf_token):
    headers = {
        'accept': 'application/json, text/javascript, */*; q=0.01',
        'accept-language': 'en-GB,en-US;q=0.9,en;q=0.8',
        'content-type': 'application/x-www-form-urlencoded; charset=UTF-8',
        'cookie':f'csrf_cookie_name={csrf_token}',
        'origin': 'https://www.firstchoicecars.com',
        'priority': 'u=1, i',
        'referer': 'https://www.firstchoicecars.com/buy-used-cars-uae/',
        'sec-ch-ua': '"Not/A)Brand";v="8", "Chromium";v="126", "Google Chrome";v="126"',
        'sec-ch-ua-mobile': '?0',
        'sec-ch-ua-platform': '"Linux"',
        'sec-fetch-dest': 'empty',
        'sec-fetch-mode': 'cors',
        'sec-fetch-site': 'same-origin',
        'user-agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36',
        'x-requested-with': 'XMLHttpRequest',
    }

    data = {
        'start': f'{start}',
        'limit': '16',
        'make_id': '',
        'model_id': '',
        'price_range': '18500-605000',
        'list_type': '0',
        'csrf_test_name': csrf_token,
    }

    payload  = {
        'key': XHEAD,
        'url': 'https://www.firstchoicecars.com/buy/ajax_search',
        'method': 'POST',
        'keep_headers': True,
        **data,
    }

    # return requests.post('https://api.syphoon.com', json=payload,headers=headers)
    return requests.post('https://www.firstchoicecars.com/buy/ajax_search', data=data,headers=headers)


def get_csrf_token():
    req = requests.get('https://www.firstchoicecars.com/buy-used-cars-uae/')
    return req.cookies.get('csrf_cookie_name')
