from common import send_req_syphoon
import datetime,os,traceback


headers = {
    'accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7',
    'accept-language': 'en-GB,en-US;q=0.9,en;q=0.8',
    'cache-control': 'max-age=0',
    'device-memory': '8',
    'downlink': '10',
    'dpr': '1',
    'ect': '4g',
    'priority': 'u=0, i',
    'rtt': '100',
    'sec-ch-device-memory': '8',
    'sec-ch-dpr': '1',
    'sec-ch-ua': '"Not/A)Brand";v="8", "Chromium";v="126", "Google Chrome";v="126"',
    'sec-ch-ua-mobile': '?0',
    'sec-ch-ua-platform': '"Linux"',
    'sec-ch-viewport-width': '1850',
    'sec-fetch-dest': 'document',
    'sec-fetch-mode': 'navigate',
    'sec-fetch-site': 'same-origin',
    'sec-fetch-user': '?1',
    'upgrade-insecure-requests': '1',
    'user-agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36',
    'viewport-width': '1850',
}

cookies = {
    'amazon.com':'i18n-prefs=USD;  lc-main=en_US',
    'amazon.co.uk':'i18n-prefs=GBP;  lc-main=en_GB',
    'amazon.ca':'i18n-prefs=CAD;  lc-main=en_CA'
}


def amazon_scraper(url,asin,domain):
    # kepping html for a day
    date = datetime.now().strftime("%Y%m%d")
    os.makedirs(date,exist_ok=True)
    headers['cookie'] = cookies[domain]
    try:
        with open(f'{date}/{asin}.html','r',encoding='utf-8') as f:
            html = f.read()
    except:
        try:
            req = send_req_syphoon(1,'get',url,headers=headers)
            print(req.status_code)
            req.raise_for_status()
            html = req.text
            with open(f'{date}/{asin}.html','w',encoding='utf-8') as f:
                f.write(html)
        except Exception as ex:
            print(traceback.print_exc())
            return {'message':f'Error in sending request {url}'},{}

    return html