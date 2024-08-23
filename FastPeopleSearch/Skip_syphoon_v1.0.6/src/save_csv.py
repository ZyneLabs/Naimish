import os, time
import pandas as pd
from concurrent.futures import ThreadPoolExecutor
import concurrent
from .syphoon.client import SyphoonClient
import csv
from .get_person_url import find_person_url, get_soup_with_vpn
from .get_person_details import extract_person_phones, extract_person_emails
from .read_csv import read_input_csv, create_output_dict
from pathlib import Path

def timeit(func):
    def wrapper(*arg, **kw):
        t1 = time.time()
        res = func(*arg, **kw)
        t2 = time.time()
        print(f"{func.__name__} took {t2 - t1} seconds")
        return res
    return wrapper

@timeit
def fetch_person_details(person_data, client):
    """
    Fetch details for a single person and return the output dictionary.

    Parameters:
    - person_data (dict): A dictionary containing person information.

    Returns:
    - dict: Output dictionary.
    """
    person_url = find_person_url(person_data, client)
    if not person_url:
        person_url = find_person_url(person_data, client, True)

    if person_url:
        soup = get_soup_with_vpn(person_url, client)
        phones_dict = extract_person_phones(soup) if soup else {}
        emails_list = extract_person_emails(soup) if soup else []
        return person_data, person_url, create_output_dict(phones_dict, emails_list)

    return person_data, person_url, {}

@timeit
def fetch_all_person_details(input_csv_path, output_csv_path, api_key, concurrency, retries, progress_callback=None):
    data_list, skipped_list = read_input_csv(input_csv_path)
    total_records = len(data_list)
    current_record = 0

    client = SyphoonClient(api_key, retries=retries)

    header = ["First Name","Last Name","Address","City","State","ZIP","Mailing Address","Mailing City","Mailing State","Mailing ZIP","url","Number 1","Number 1 Type","Number 2","Number 2 Type","Number 3","Number 3 Type","Number 4","Number 4 Type","Number 5","Number 5 Type","Number 6","Number 6 Type","Number 7","Number 7 Type","Number 8","Number 8 Type","Number 9","Number 9 Type","Number 10","Number 10 Type","Wireless Number 1","Wireless Number 2","Wireless Number 3","Email Address 1","Email Address 2","Email Address 3","Email Address 4","Email Address 5"]

    output_csv_name = os.path.join(os.path.dirname(input_csv_path), output_csv_path + '.csv')
    Path(os.path.join(os.path.dirname(input_csv_path), output_csv_path)).parent.mkdir(parents=True, exist_ok=True)

    with ThreadPoolExecutor(max_workers=concurrency) as executor:
        # future_to_data = {executor.submit(fetch_person_details, person_data, client): person_data for person_data in data_list}
        futures = []
        count = 0
        
        for person_data in data_list:
            futures.append(executor.submit(fetch_person_details, person_data, client))

        for future in concurrent.futures.as_completed(futures):
            try:
                person_data, person_url, output_dict = future.result()
                count += 1
                # person_data = future_to_data[future]
                df = pd.DataFrame({**person_data, **output_dict, "url": person_url}, index=[0], columns=header)
                df.to_csv(output_csv_name, mode='a', header=not os.path.exists(output_csv_name), index=False)
            except Exception as e:
                print(f"Error processing person: {e}")
            current_record += 1
            if progress_callback:
                progress_callback(current_record, total_records)
    
    with open(os.path.join(os.path.dirname(input_csv_path), output_csv_path + '.report'), mode='w') as f:
        f.write(f"Successful contacts: {count}\n")
        if len(skipped_list) > 0:
            f.write("Skipped entries:\n")
            writer = csv.DictWriter(f, fieldnames=skipped_list[0].keys(), delimiter='\t')
            writer.writeheader()
            writer.writerows(skipped_list)


            
        
        
