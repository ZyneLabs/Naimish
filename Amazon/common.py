from bs4 import BeautifulSoup
import re
import requests
from urllib.parse import urlencode
import json
from os import getenv
import os
from random import randint
import traceback


from pymongo.mongo_client import MongoClient
from datetime import datetime
from random import randint
from rq import Queue, Retry
from redis import Redis


# API_KEYS = getenv('API_KEYS').split(',')

API_KEYS = ['YV749KjNlvgdbjsVWkW3','YV749KjNlvgdbjsVWkW4']
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
        # "country_code": "us",
    }
    
    if cookies is not None:
        headers["cookie"] = ";".join([f"{k}={v}" for k, v in cookies.items()])

    retry_count = 0

    while retry_count < total_retries:
        try:
            return requests.post(
                "https://api.syphoon.com", json=payload, headers=headers,
            )
        except Exception as ex:
            retry_count += 1


def get_digit_groups(input_str):
    if input_str is None:
        return []
    return re.findall(r'\d+', input_str)

def clean_str(input_str, sep="|"):
    if input_str is None:
        return ""

    if type(input_str) is not str:
        return input_str

    input_str = re.sub(r"\s+", " ", input_str).replace("\n", sep).replace("\u200e", '').replace('\u200f','')

    return input_str.strip()

def get_domain_name(url):
    pattern = re.compile(r'https?://(?:www\.)?([^/]+)')
    match = pattern.search(url)
    
    if match:
        return match.group(1)
    return None

def search_text_between(text, start, end):
    pattern = re.compile(f'{re.escape(start)}(.*?){re.escape(end)}', re.DOTALL)
    match = re.search(pattern, text)
    if match:
        return match.group(1)
    else:
        return None