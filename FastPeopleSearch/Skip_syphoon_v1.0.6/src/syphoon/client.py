import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
from concurrent.futures import ThreadPoolExecutor
from functools import partial
from urllib.parse import urlencode


class SyphoonClient:
    def __init__(self, apikey: str, retries: int = 0, concurrency: int = 5):
        self.api_url = "https://api.syphoon.com"
        self.apikey = apikey

        self.executor = ThreadPoolExecutor(max_workers=concurrency)

        self.requests_session = requests.Session()
        if (retries > 0):
            max_retries = Retry().new(
                total=retries,
                backoff_factor=0.001,
                status_forcelist=[422, 429, 500, 502, 503, 504, 404],
                raise_on_status=False,
            )
            adapter = HTTPAdapter(max_retries=max_retries)
            self.requests_session.mount("https://", adapter)
            self.requests_session.mount("http://", adapter)

    def get(
        self, url: str, params: dict = None, headers: dict = None, **kwargs
    ) -> requests.Response:
        if params is not None:
            url = url + urlencode(params)

        res = requests.post(url=self.api_url, data={"key": self.apikey, "method": "GET", "url": url, "keep_headers": headers != None, }, headers=headers, **kwargs)
        return res
    
    def post(
        self, url: str, params: dict = None, headers: dict = None, data: dict = {}, **kwargs
    ) -> requests.Response:
        if params is not None:
            url = url + urlencode(params)
        res = requests.post(url=self.api_url, data={"key": self.apikey, "method": "POST", "url": url, "keep_headers": headers != None, **data}, headers=headers,  **kwargs)
        return res    