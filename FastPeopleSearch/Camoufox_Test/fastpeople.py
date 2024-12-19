from camoufox.sync_api import Camoufox
import time
proxies = {
    'server': 'http://geo.iproyal.com:12321',
    'username': 'RAD5VCH0WnT6glQG',
    'password': 'uJUnzLRMv5c5Ap0Z_country-us'
}

def timeit(func):
    def wrapper(*args, **kwargs):
        start = time.time()
        result = func(*args, **kwargs)
        end = time.time()
        print(f'{func.__name__} took {end - start} seconds')
        return result
    return wrapper

@timeit
def fastpeople_scraper(url : str) -> str | None :
    page_html = None
    try:
        with Camoufox(headless=True,os=['windows'],geoip=True,proxy=proxies) as browser:
            page = browser.new_page()
            page.goto(url)
            page.wait_for_selector('div#site-content',timeout=60000)
            page_html = page.content()
    except Exception as e:
        print(e)

    return page_html
