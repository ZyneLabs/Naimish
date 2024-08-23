from bs4 import BeautifulSoup
import re
import time
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
def extract_person_phones(soup):
    """
    Extracts phone details from a BeautifulSoup object.

    Parameters:
    - soup (BeautifulSoup): The BeautifulSoup object of the webpage.

    Returns:
    - dict: A dictionary containing phone details.
    """
    phones = {}
    try:
        phone_section = soup.find('div', class_='detail-box-phone')
        for phone_detail in phone_section.find_all('dl'):
            label = phone_detail.dt.text.replace(' (Primary Phone)', '').strip()
            phones[label] = phone_detail.dd.text
    except AttributeError:
        return {}

    return phones

@timeit
def extract_person_emails(soup):
    """
    Extracts email addresses from a BeautifulSoup object.

    Parameters:
    - soup (BeautifulSoup): The BeautifulSoup object of the webpage.

    Returns:
    - list: A list containing email addresses.
    """
    emails = []
    try:
        email_section = soup.find('div', id='email_section')
        for email in email_section.findAll('h3'):
            emails.append(email.text)
        
        if len(email) > 0:
            # Find all script tags with type 'application/ld+json'
            script_tags = soup.find_all('script', {'type': 'application/ld+json'})

            # Define a regular expression pattern for the desired question
            question_pattern = re.compile(r'\bWhat email addresses have been used by\b', re.IGNORECASE)

            # Iterate through each script tag
            for script_tag in script_tags:
                # Extract the content of the script tag
                script_content = script_tag.string
    
                # Skip if the content is empty
                if not script_content:
                    continue

                # Search for the question pattern in the script content
                match = question_pattern.search(script_content)

                # If a match is found, extract the relevant information
                if match:
                    # Extract the text content from HTML tags
                    answer_text = BeautifulSoup(script_content, 'html.parser').get_text()
                    answer_text = json.loads(answer_text[:-2])
                    question_prefix = "What email addresses have been used by"
                    for entity in answer_text.get("mainEntity", []):
                        if entity.get("@type") == "Question" and entity.get("name", "").startswith(question_prefix):
                            answer_text = entity.get("acceptedAnswer", {}).get("text", "")

                            # Extract email addresses using a regular expression
                            email_addresses = re.findall(r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b', answer_text)
                            emails = email_addresses
                    break
    except AttributeError:
        return []

    return emails
