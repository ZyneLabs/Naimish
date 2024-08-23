import pandas as pd
import os, time

def timeit(func):
    def wrapper(*arg, **kw):
        t1 = time.time()
        res = func(*arg, **kw)
        t2 = time.time()
        print(f"{func.__name__} took {t2 - t1} seconds")
        return res
    return wrapper

@timeit
def read_input_csv(input_csv_path):
    """
    Read input CSV file and return a list of dictionaries.

    Parameters:
    - input_csv_path (str): Path to the input CSV file.

    Returns:
    - list of dict: List of dictionaries representing the data.
    """
    df = pd.read_csv(input_csv_path)
    selected_columns = [
        "First Name",
        "Last Name",
        "Address",
        "City",
        "State",
        "ZIP",
        "Mailing Address",
        "Mailing City",
        "Mailing State",
        "Mailing ZIP"
    ]

    df_selected = df[selected_columns]
    df_filtered = df_selected.dropna(subset=['First Name', 'Last Name'])
    data_list = df_filtered.to_dict(orient='records')
    df_skipped = df_selected[df['First Name'].isna() | df['Last Name'].isna()]
    skipped_list = df_skipped.to_dict(orient='records')
    skipped_list = [{**entry, "First Name": ""} if str(entry["First Name"]) == 'nan' else entry for entry in skipped_list ]
    skipped_list = [{**entry, "Last Name": ""} if str(entry["Last Name"]) == 'nan' else entry for entry in skipped_list ]
    return [data_list, skipped_list]

@timeit
def create_output_dict(phones_dict, emails_list):
    """
    Create an output dictionary based on phones and emails.

    Parameters:
    - phones_dict (dict): Dictionary containing phone numbers and types.
    - emails_list (list): List of email addresses.

    Returns:
    - dict: Output dictionary.
    """
    output_dict = {}

    max_phones = min(10, len(phones_dict))
    max_wireless = min(3, sum(phone_type == 'Wireless' for phone_type in phones_dict.values()))
    max_emails = min(5, len(emails_list))

    for i, (phone, phone_type) in enumerate(phones_dict.items(), start=1):
        if i <= max_phones:
            output_dict[f'Number {i}'] = phone
            output_dict[f'Number {i} Type'] = phone_type

    for i in range(len(phones_dict) + 1, 11):
        output_dict[f'Number {i}'] = ''
        output_dict[f'Number {i} Type'] = ''

    wireless_columns = []
    for i, (phone, phone_type) in enumerate(phones_dict.items(), start=1):
        if phone_type == 'Wireless' and len(wireless_columns) < max_wireless:
            output_dict[f'Wireless Number {len(wireless_columns) + 1}'] = phone
            wireless_columns.append(f'Wireless Number {len(wireless_columns) + 1}')

    for i in range(len(wireless_columns) + 1, 4):
        output_dict[f'Wireless Number {i}'] = ''

    for i, email in enumerate(emails_list, start=1):
        if i <= max_emails:
            output_dict[f'Email Address {i}'] = email

    for i in range(len(emails_list) + 1, 6):
        output_dict[f'Email Address {i}'] = ''

    return output_dict
