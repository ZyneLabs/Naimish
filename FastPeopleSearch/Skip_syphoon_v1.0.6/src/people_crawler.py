from bs4 import BeautifulSoup
from syphoon.client import SyphoonClient
from get_person_url import get_soup_with_vpn
import string
import os
import json
from get_person_details import extract_person_emails
from multiprocessing import Pool, cpu_count
from faker import Faker
import pandas as pd

fake = Faker('en_US')

client = SyphoonClient(os.environ.get("SYPHON_API_KEY"), retries=2)

visited_person_urls = set()
visited_address_urls = set()
glob_person_urls = set()
glob_new_urls = set()
seen_names = set()


def unique_first_names():
    while True:
        first_name = fake.first_name()
        if first_name not in seen_names:
            seen_names.add(first_name)
            yield first_name


def crawl_address(url):
    person_urls = []
    address_urls = []

    
    print("Address_url",url)
    soup = get_soup_with_vpn(url, client)
    json_soups = soup.find_all("script", {"type": "application/ld+json"})

    page_data = None

    for entry in json_soups:
        try:
            data = json.loads(entry.text.strip().strip(";"))
            if isinstance(data, list) and len(data) > 0 and data[0].get("@type") == "Person":
                page_data = data
                break
        except Exception as e:
            print(entry.text)
            print(e)

    if page_data:
        for person in page_data:
            try:
                person_url = person['url']
                if person_url not in visited_person_urls:
                    if person['HomeLocation'][0]['address']['addressLocality'] == 'Lakewood' and person['HomeLocation'][0]['address']['addressRegion'] == 'NJ':
                        person_urls.append(person_url)
                    address_urls.extend([address['url'] for address in person['HomeLocation'] if 'lakewood-nj' in address.get('url','')])
            except:
                pass

    second_page_link = soup.find("a", {"title": "Next page of search results"})
    if second_page_link:
        second_page_url = second_page_link.get("href")
        address_urls.append(second_page_url)

    return person_urls, address_urls

def get_person_info(person_url):
    address_urls = []
    person_urls = []
    print("Person_url",person_url)
    soup = get_soup_with_vpn(person_url, client)
    try:
    
        current_address = soup.select_one('.detail-box-content h3 a')
        if '08701' not in current_address.text:
            raise 'Not same address'
        
        address_urls.append('https://www.fastpeoplesearch.com' + current_address.get('href'))
        person_info = {
            "URL": person_url,
            "Full Name": soup.select_one('.fullname').text.strip(),
            "Address": current_address.text.replace('\n', ',').strip(),
        }
        emails = extract_person_emails(soup)
        for indx, email in enumerate(emails):
            person_info[f'Email {indx+1}'] = email
    except Exception as e:
        person_info = {}

    maybe_neighborhood_soup = soup.select('#neighbors_section .detail-box-neighbors .col-sm-12.col-md-6')
    if maybe_neighborhood_soup:
        for entry in maybe_neighborhood_soup:
            for a in entry.find_all('a'):
                if 'Fast People Search' in a.get('title',''):
                    person_url = 'https://www.fastpeoplesearch.com' + a.get('href')
                    if person_url not in visited_person_urls:
                        person_urls.append(person_url)
                elif 'Search people who' in a.get('title',''):
                    address_url = 'https://www.fastpeoplesearch.com' + a.get('href')
                    if address_url not in visited_address_urls:
                        address_urls.append(address_url)
                
    return person_info, person_urls, address_urls

if __name__ == '__main__':
    # Initial seed URLs
    max_record_limit  = 10

    name_generator = unique_first_names()
    initial_urls = [f'https://www.fastpeoplesearch.com/name/{next(name_generator).lower()}_lakewood-nj-08701' for _ in range(max_record_limit//10)]
    

    to_visit_person_urls = set()  # Correctly set the initial URLs
    to_visit_address_urls = set(initial_urls)
    all_person_data = []

    try:
        
        while to_visit_person_urls or to_visit_address_urls:
            new_person_urls = set()
            new_address_urls = set()
            print(f"Remaining: {len(to_visit_person_urls) + len(to_visit_address_urls)}")
            # Crawl person URLs
            if to_visit_address_urls:
                # make a chunk of URLs to visit only 10 at a time
                for i in range(0, len(to_visit_address_urls), 10):
                    to_visit_address_urls_chunk = list(to_visit_address_urls)[i:i+10]
 
                    with Pool(cpu_count()) as p:
                        address_result = p.map(crawl_address, list(to_visit_address_urls_chunk))

                    for person_urls, address_urls in address_result:
                        new_person_urls.update(person_urls)
                        new_address_urls.update(address_urls)


                    # Mark these URLs as visited
                    visited_address_urls.update(to_visit_address_urls_chunk)
                    to_visit_person_urls = new_person_urls - visited_person_urls
                    
                    if len(to_visit_person_urls)>max_record_limit:
                        break

            # Crawl address URLs
            if to_visit_person_urls:
                # make a chunk of URLs to visit only 10 at a time
                for i in range(0, len(to_visit_person_urls), 10):
                    to_visit_person_urls_chunk = list(to_visit_person_urls)[i:i+10]
                    with Pool(cpu_count()) as p:
                        person_results = p.map(get_person_info, to_visit_person_urls_chunk)

                    for person_info, person_urls, address_urls in person_results:
                        new_person_urls.update(person_urls)
                        new_address_urls.update(address_urls)

                        if person_info and person_info.get('Email 1',''):
                            all_person_data.append(person_info)

                    # Mark these URLs as visited
                    visited_person_urls.update(to_visit_person_urls_chunk)
                    if len(all_person_data)>max_record_limit:
                        break 

            to_visit_person_urls = new_person_urls - visited_person_urls
            to_visit_address_urls = new_address_urls - visited_address_urls

            if len(all_person_data)>max_record_limit:
                break

    except Exception as e:
        print(e)
    with open('new_person_urls.txt', 'a') as outfile:
        outfile.write('\n'.join(new_person_urls))
    with open('new_address_urls.txt', 'a') as outfile:
        outfile.write('\n'.join(new_address_urls))
    with open('person_urls.txt', 'a') as outfile:
        outfile.write('\n'.join(to_visit_person_urls))
    with open('address_urls.txt', 'a') as outfile:
        outfile.write('\n'.join(to_visit_address_urls))

    df = pd.DataFrame(all_person_data)
    df.to_excel('Lakewood_3.xlsx', index=False)    
    # print(get_person_info('https://www.fastpeoplesearch.com/brian-batchelor_id_G-5730214724156860164'))