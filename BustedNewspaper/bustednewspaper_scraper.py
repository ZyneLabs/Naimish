import requests

def bustednewspaper_scraper(API_KEY, method, url):
    payload = {
        "key": API_KEY,
        "url": url,
        "method": method,
    }
    
    try:
        return requests.post(
            "https://api.syphoon.com", json=payload)
    
    except Exception as ex:
        print(ex)

    