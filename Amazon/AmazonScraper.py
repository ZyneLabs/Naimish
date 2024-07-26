from common import *


us_headers = {
    'accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7',
    'accept-language': 'en-GB,en-US;q=0.9,en;q=0.8',
    'cache-control': 'max-age=0',
    'cookie': 'session-id=146-1927424-0708753; i18n-prefs=USD; ubid-main=133-9102078-3948428; lc-main=en_US; session-id-time=2082787201l; skin=noskin; session-token=7b00p7MafSxA3/CiE5XRybBP4mIsZeNeGoHVMS2Mk6tvg1qWpA4kY6mLfe6qvfVoZByVWkf74kIl9c+kkBl9TuEs9xNivi772dfYf0t8nsC/Zc1lMbhKZWRArWDqOF941gJKZ6bissl5vSRy8+T+CYGaicJZX4ABQeaYFawC96cUv1xNVqXC3GYS12lY3Xl6TUeXy+RUB8fFWSmnqLOIOrlft9ZJSu7FUfjrywqloeTamXPVwWMloXALM5GOERiMsZuslF7kmmMhzAl0ylyitDDjV+M49oIaPm/HtJKmskxWlkosXmBA7cr2l2NH3yN1wfF1QBBrWCK5TnYAmQhjY/cp+Rr1dekA; csm-hit=tb:s-HSQY2A8JXBE48RRSXM3Q|1721897014652&t:1721897017059&adb:adblk_no',
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


ca_headers = {
    'accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7',
    'accept-language': 'en-GB,en-US;q=0.9,en;q=0.8',
    'cache-control': 'max-age=0',
    'cookie': 'session-id=134-1247248-5763556; session-id-time=2082787201l; i18n-prefs=CAD; ubid-acbca=134-9375664-3903801; lc-acbca=en_CA; session-token=XCMubtnE9DRjf+BsrNVtps1/c9TXa3SbXDZ9T7YOnYu7MDwp84eaU3C2gRGy7cMNxv+eV6a/rPmBn+bqMVfUr2FJdqW1ckC5dE8a5+UqV2/au7znOFge4dvd95SSrEAer8d2WFOInWGg/Q021CqoDtoM9tRUQlke+EcLKGigFnQ9oPJ75Cugns+DlHks89wUi+LWRvkNQM8pvlQCMOHY/lb9mCj0B+mVwQ5F7re1FWSGSrlnv/ZfKdc0ejO4RFAWCddL3xIjOYzMZ30iyQOAEQ93MN0MIarG4Lrjzy4aZiBIXpEDujUVXFj7dJXzOJay8OZ3iAhm8F2Vh+/gPZeH7BHh0SqiPhf1; csm-hit=tb:K685X55XBBJ31B364NZJ+s-1D2XF497NRWPBFBGJWG2|1721973185364&t:1721973185365&adb:adblk_no',
    'device-memory': '8',
    'downlink': '10',
    'dpr': '1',
    'ect': '4g',
    'priority': 'u=0, i',
    'referer': 'https://www.amazon.ca/',
    'rtt': '150',
    'sec-ch-device-memory': '8',
    'sec-ch-dpr': '1',
    'sec-ch-ua': '"Not/A)Brand";v="8", "Chromium";v="126", "Google Chrome";v="126"',
    'sec-ch-ua-mobile': '?0',
    'sec-ch-ua-platform': '"Linux"',
    'sec-ch-ua-platform-version': '"6.5.0"',
    'sec-ch-viewport-width': '1850',
    'sec-fetch-dest': 'document',
    'sec-fetch-mode': 'navigate',
    'sec-fetch-site': 'same-origin',
    'sec-fetch-user': '?1',
    'upgrade-insecure-requests': '1',
    'user-agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36',
    'viewport-width': '1850',
}


def amazon_scraper(url,asin):

    # kepping html for a day
    date = datetime.now().strftime("%Y%m%d")
    os.makedirs(date,exist_ok=True)

    headers = ca_headers if 'www.amazon.ca' in url else us_headers
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