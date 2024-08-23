import os
import re
import time
import requests
from bs4 import BeautifulSoup
import json

def timeit(func):
    def wrapper(*arg, **kw):
        t1 = time.time()
        res = func(*arg, **kw)
        t2 = time.time()
        print(f"{func.__name__} took {t2 - t1} seconds")
        return res
    return wrapper

@timeit
def get_soup_with_vpn(url, client):
    """
    Retrieve the BeautifulSoup object for a webpage using a VPN.

    Parameters:
    - url (str): The URL of the webpage.

    Returns:
    - BeautifulSoup: The BeautifulSoup object.
    """
    response = client.get(url)
    if response.status_code == 200:
        soup = BeautifulSoup(response.text, 'html.parser')
        try:
            with open(f"htmls/{url.split('/')[-1]}-{time.time()}.html") as f:
                f.write(response.text)
        except:
            pass
        print("Fetched Link")
    else:
        soup = None
        print("Failed to fetch Link with code:", response.status_code)
    return soup

@timeit
def find_person_url(person_data, client, use_property=False):
    """
    Find the URL of a person based on their data.

    Parameters:
    - person_data (dict): A dictionary containing person information.

    Returns:
    - str: The URL of the person.

    Raises:
    - Exception: If the person is not found.
    """
    try:
        first_name = person_data["First Name"].lower()
        last_name = person_data["Last Name"].lower()
        if not use_property:
            address = person_data["Mailing Address"].split("#")[0].strip().lower()
            city = person_data["Mailing City"].lower()
            state = person_data["Mailing State"].lower()
        else:
            address = person_data["Address"].split("#")[0].strip().lower()
            city = person_data["City"].lower()
            state = person_data["State"].lower()
    except Exception as error:
        return

    # Construct URL based on person information
    address_slash = address.replace(' ', '-')
    city = city.replace(' ', '-')
    url = f"https://www.fastpeoplesearch.com/address/{address_slash}_{city}-{state}"

    # Get BeautifulSoup object using VPN
    maybe_person_url = search_person_in_url(url, person_data=person_data, client=client)

    if isinstance(maybe_person_url, str):
        return maybe_person_url
    
    # has_next_page = maybe_person_url
    # if has_next_page:
    #     maybe_person_url = search_person_in_url(f"{url}/page/2", person_data=person_data, client=client)
    #     if isinstance(maybe_person_url, str):
    #         return maybe_person_url
    
    # has_next_page = maybe_person_url
    # if has_next_page:
    #     maybe_person_url = search_person_in_url(f"{url}/page/3", person_data=person_data, client=client)
    #     if isinstance(maybe_person_url, str):
    #         return maybe_person_url

    return None

@timeit
def search_person_in_url(url, person_data, client):
    first_name = person_data['First Name'].strip().lower()
    last_name = person_data['Last Name'].strip().lower()

    full_name = f"{first_name} {last_name}"
    first_name_longest_part = max(first_name.split(), key=len)
    last_name_longest_part = max(last_name.split(), key=len)

    soup = get_soup_with_vpn(url, client)

    json_soups = soup.find_all("script", {"type": "application/ld+json"})

    page_data = None

    for entry in json_soups:
        try:
            data = json.loads(entry.text.strip().strip(";"))
            if isinstance(data, list) and len(data) > 0 and data[0].get("@type") == "Person":
                page_data = data
        except Exception as e:
            print(entry.text)
            print(e)

    if page_data is None:
        return None
    
    for entry in page_data:
        title = entry['name'].lower()
        scraped_first_name, scraped_last_name = title.split()[0], " ".join(title.split()[1:])
        try:

            if (first_name_longest_part in scraped_first_name and last_name_longest_part in scraped_last_name) or (first_name_longest_part in scraped_last_name and last_name_longest_part in scraped_first_name) or (full_name in title) or (last_name + " " + first_name in title):
                return entry['url']
        
        except:
            pass
        
        try:
            if any([(first_name_longest_part in alias and last_name_longest_part in alias) or (first_name_longest_part in alias and last_name_longest_part in alias) or (first_name + " " + last_name in alias) or (last_name + " " + first_name in alias) for alias in entry['additionalName']]):
                return entry['url']
        
        except:
            pass

    second_page_link = soup.find("a", {"title": "Next page of search results"})
    return second_page_link != None