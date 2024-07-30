from common import send_req_syphoon
import requests
import json

class MokeRequest:

    def __init__(self,status_code,text):
        self.status_code = status_code
        self.text = json.dumps(text)

    def json(self):
        return json.loads(self.text)
            
def walmart_scraper(product_url,max_try=3):
    while max_try:
        try:
            req = send_req_syphoon(0, 'get', product_url)
            req.raise_for_status()
            return req
        except requests.exceptions.RequestException:
            max_try -= 1

        except Exception as e:
            req = MokeRequest(400,{"message":"This request wants to charge you"})

    return req
