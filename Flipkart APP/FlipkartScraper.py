import requests
import os

PROXY_KEY = os.environ.get('PROXY_KEY')

# Note : Simple request is working but proxy is not working properly 
# we need to look into this

def send_syphoon_request(key,method,url,headers,data,max_retries=3):

    payload = {
        **data,
        'key': key,
        'method': method,
        'url': url,
        'headers': headers,
        'country_code':'in'
    }
    while max_retries:
        try:
            return requests.post('https://api.syphoon.com', json=payload)
        except Exception as e:
            print(e)
            max_retries -= 1


def flipkart_product_page_scraper(url):

    headers = {
        'Cookie': 'vd=VIF6B432DE30D84571A22ABFFDDFF7B3CF-1713463773249-52.1724147504.1724146310.161699880',
        'Content-Type': 'application/json; application/json; charset=UTF-8',
        'secureCookie': 'd1t11ay8/Pz8/DD8WHz8/Ij8/QxtnAsNaMZZwttkDTeQwS0hbVHW3v+VT0HAc2oWbVBWcuwHvgPRdceZKzKBQla42zg==',
        'X-AR-AVAILABILITY': 'PRESENT',
        'x-atlas-versions': '20224000/2090000',
        'X-DLS': 'true',
        'X-Layout-Version': '{"appVersion":"910000","frameworkVersion":"1.0"}',
        'X-MULTIWIDGET-VERSION': '5.21.1',
        'X-NewRelic-ID': 'VwEHUVRUARABUVlaAAQGXlED',
        'x-request-metaInfo': '{"pageUri":"%2Fred-tape-sneaker-casual-shoes-men-soft-cushion-insole-slip-resistance-sneakers%2Fp%2Fitmea62228442270%3Fpid%3DSHOGR5RUWFDQMGXH%26lid%3DLSTSHOGR5RUWFDQMGXH0YEFIS%26marketplace%3DFLIPKART%26hl_lid%3D%26q%3Dsneakers%26store%3Dosp%252Fcil%252Fe1f"}',
        'X-User-Agent': 'Mozilla/5.0 (Linux; Android 12; M2101K6P Build/SQ3A.220705.004) FKUA/Retail/2090000/Android/Mobile (Xiaomi/M2101K6P/ea522e0c9836e27b3a541088d7c870ec)',
    }

    json_data = {
        'pageUri': url.replace('https://www.flipkart.com', ''),
        'pageContext': None,
        'partnerContext': None,
        'locationContext': None,
        'requestContext': None,
    }

    response = requests.post('https://2.rome.api.flipkart.net/4/page/fetch', headers=headers, json=json_data)
    # response = send_syphoon_request(PROXY_KEY,'POST','https://2.rome.api.flipkart.net/4/page/fetch',headers,json_data)

    return response.json()



def flipkart_specification_scraper(productid, listingid):
    headers = {
    'Accept': '*/*',
    'Accept-Language': 'en-GB,en-US;q=0.9,en;q=0.8',
    'Connection': 'keep-alive',
    'Content-Type': 'application/json',
    'Cookie': 'vd=VIF6B432DE30D84571A22ABFFDDFF7B3CF-1713463773249-52.1724147504.1724146310.161699880',
    'Origin': 'https://www.flipkart.com',
    'Referer': 'https://www.flipkart.com/',
    'Sec-Fetch-Dest': 'empty',
    'Sec-Fetch-Mode': 'cors',
    'Sec-Fetch-Site': 'same-site',
    'User-Agent': 'Mozilla/5.0 (Linux; Android 13; SM-G981B) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/116.0.0.0 Mobile Safari/537.36',
    'X-user-agent': 'Mozilla/5.0 (Linux; Android 13; SM-G981B) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/116.0.0.0 Mobile Safari/537.36 FKUA/msite/0.0.3/msite/Mobile',
    'sec-ch-ua': '"Not/A)Brand";v="8", "Chromium";v="126", "Google Chrome";v="126"',
    'sec-ch-ua-mobile': '?1',
    'sec-ch-ua-platform': '"Android"',
}

    json_data = {
        'requestContext': {
            'productId': productid,
            'listingId': listingid,
        },
        'locationContext': {},
    }

    response = requests.post(
        'https://1.rome.api.flipkart.com/3/page/dynamic/product-details',
        headers=headers,
        json=json_data,
    )

    # response = send_syphoon_request(PROXY_KEY,'POST','https://1.rome.api.flipkart.com/3/page/dynamic/product-details',headers,json_data)
    return response.json()
