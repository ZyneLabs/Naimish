import requests
from bs4 import BeautifulSoup
import re
import requests
from urllib.parse import urlencode
import json
from os import getenv
from pymongo.mongo_client import MongoClient
from datetime import datetime
import traceback
from random import randint
from rq import Queue, Retry
from redis import Redis

API_KEYS = getenv('API_KEYS').split(',')

MONGO_URI = getenv('MONGODB_URI')
PROXY_VENDOR = getenv('PROXY_VENDOR')


def send_req_syphoon(
    scraper_class, method, url, params=None, headers=None, payload=None, cookies=None, total_retries=5
):

    if params is not None:
        url = f"{url}?{urlencode(params)}"
    
    if payload is None:
        payload = {}

    if headers is not None:
        payload['keep_headers'] = True
    else:
        headers = {}


    payload = {
        **payload,
        "key": API_KEYS[scraper_class],
        "url": url,
        "method": method,
    }
    
    if cookies is not None:
        headers["cookie"] = ";".join([f"{k}={v}" for k, v in cookies.items()])

    retry_count = 0

    while retry_count < total_retries:
        try:
            return requests.post(
                "https://api.syphoon.com", json=payload, headers=headers, verify=False
            )
        except Exception as ex:
            retry_count += 1

headers = {
    'accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7',
    'accept-language': 'en-GB,en-US;q=0.9,en;q=0.8',
    'cache-control': 'max-age=0',
    'downlink': '3.8',
    'dpr': '1',
    'priority': 'u=0, i',
    'sec-ch-ua': '"Not/A)Brand";v="8", "Chromium";v="126", "Google Chrome";v="126"',
    'sec-ch-ua-mobile': '?0',
    'sec-ch-ua-platform': '"Linux"',
    'sec-fetch-dest': 'document',
    'sec-fetch-mode': 'navigate',
    'sec-fetch-site': 'same-origin',
    'sec-fetch-user': '?1',
    'upgrade-insecure-requests': '1',
    'user-agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36',
}
