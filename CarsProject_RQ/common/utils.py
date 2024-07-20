from bs4 import BeautifulSoup
import requests
from pymongo.mongo_client import MongoClient
from urllib.parse import urlencode
from typing import Union as union
from dotenv import load_dotenv
from os import getenv
import json
import traceback
import re
from datetime import datetime
from rq import Queue
from redis import Redis 


# load_dotenv()

# API_KEYS= os.getenv("API_KEYS").split(",")
MONGO_URI = getenv('MONGODB_URI')
PROXY_VENDOR = getenv('PROXY_VENDOR')
redis_url = getenv('REDIS_URI')

redis_conn = Redis.from_url(redis_url)

client = MongoClient(MONGO_URI)


def send_req_syphoon(
    api_key, method, url, params=None, headers=None, payload=None, cookies=None, total_retries=5
) -> union[requests.Response, None]:

    if params is not None:
        url = f"{url}?{urlencode(params)}"

    if headers is None:
        headers = {}

    if payload is None:
        payload = {}

    payload = {
        **payload,
        "key": api_key,
        "url": url,
        "method": method,
        "keep_headers": True,
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

