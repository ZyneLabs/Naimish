import re
import requests
from bs4 import BeautifulSoup
from urllib.parse import urlencode
import re
import json
# import os 
# from dotenv import load_dotenv

# load_dotenv()

# API_KEYS = os.getenv("API_KEYS").split(",")
API_KEYS = ['YV749KjNlvgdbjsVWkW3','YV749KjNlvgdbjsVWkW4','YV749KjNlvgdbjsVWkW5','YV749KjNlvgdbjsVWkW6','YV749KjNlvgdbjsVWkW7']

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



def clean_str(input_str, sep="|"):
    if input_str is None:
        return ""

    if type(input_str) is not str:
        return input_str

    input_str = re.sub(r"\s+", " ", input_str).replace("\n", sep)

    return input_str.strip()


def get_digit_groups(input_str):
    if input_str is None:
        return []
    return re.findall(r'\d+', input_str)


def extract_value_if_exists(data, key_array, default=None):
    current_value = data
    try:
        for k in key_array:
            if callable(k):
                current_value = k(current_value)
            else:
                current_value = current_value[k]
        return current_value
    except (KeyError, TypeError, IndexError):
        return default
    

def search_text_between(text, start, end):
    pattern = re.compile(f'{re.escape(start)}(.*?){re.escape(end)}', re.DOTALL)
    match = re.search(pattern, text)
    if match:
        return match.group(1)
    else:
        return None