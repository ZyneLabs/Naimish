import os
from src.get_person_url import find_person_url
from .syphoon.client import SyphoonClient

def test_get_person(api_key):
    data_list = [
        {
            'First Name': 'R Chacon',
            'Last Name': 'Blanca',
            'Mailing Address': '8435 Sw 2nd St',
            'Mailing Address City': 'Miami',
            'Mailing Address State': 'FL',
            'Mailing Address ZIP': 33144,
            'Address': '2420 Nw 9th St',
            'City': 'Miami',
            'State': 'FL',
            'ZIP': 33125
        },
        {
            'First Name': 'Louis',
            'Last Name': 'Sparks',
            'Mailing Address': '1140 Nw 76th St',
            'Mailing City': 'Miami',
            'Mailing State': 'FL',
            'Mailing ZIP': 33150,
            'Address': '1147 Nw 76th St',
            'City': 'Miami',
            'State': 'FL',
            'ZIP': 33150
        }
    ]

    expected_results = [
        "https://www.fastpeoplesearch.com/blanca-chacon_id_G5605642070957508567",
        "https://www.fastpeoplesearch.com/louis-sparks_id_G-8864874387672538158"
    ]

    results = []
    client = SyphoonClient(api_key, retries=10)
    for person_data in data_list:
        person_url = find_person_url(person_data, client)
        if not person_url:
            person_url = find_person_url(person_data, client, True)
        if person_url:
            results.append(person_url)

    if expected_results == results:
        return "Test Succeeded"
    else:
        return "Test Failed"
