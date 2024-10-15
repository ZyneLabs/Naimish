
from bs4 import BeautifulSoup
import re

def clean_str(input_str, sep="|"):
    if input_str is None:
        return ""

    if type(input_str) is not str:
        return input_str

    input_str = re.sub(r"\s+", " ", input_str).replace("\n", sep)

    return input_str.strip()

def decode_cfemail(encoded_string):
    r = int(encoded_string[:2], 16)
    email = ''.join([chr(int(encoded_string[i:i+2], 16) ^ r) for i in range(2, len(encoded_string), 2)])
    return email

def person_detail_parser(soup : BeautifulSoup):    
    details = {}
    details['url'] = soup.select_one('base')['href']
    details['page_title'] = clean_str(soup.select_one('h1#details-header').text)


    if address_soup := soup.select_one('#current_address_section a'):
        details['address'] = address_soup.get('title').replace('Search people living at','')
        details['address_link']  = address_soup.get('href')
       

    person_info = {}
    full_name = soup.select_one('#full_name_section .fullname').text
    person_info['full_name'] = full_name
    person_info['age'] = clean_str(soup.select_one('h2#age-header').text)
   
    if current_address := soup.select_one('#current_address_section .detail-box-content a'):
        person_info['current_address'] =clean_str(current_address.text)
        person_info['current_address_link'] = current_address.get('href')
    
    property_details = None
    if property_details_soup := soup.select('#current-addresses-property .detail-box-content dl'):
        property_details = {}
        for dl in property_details_soup:
            property_details[clean_str(dl.find('dt').text)] = clean_str(dl.find('dd').text)

    person_info['property_details'] = property_details

    phone_numbers = []
    if phone_soup := soup.select('#phone_number_section .detail-box-phone .col-sm-12.col-md-6'):
        
        for phone in phone_soup:
            phone_detail = {}
            if phone_link := phone.find('a'):
                phone_detail['number'] = phone_link.get_text(strip=True).replace('\n','').replace('\t','')
                phone_detail['search_link'] = phone_link.get('href')
                dds = phone.find_all('dd')
                phone_detail['type'] = dds[0].get_text(strip=True)
                phone_detail['provider'] = dds[1].get_text(strip=True)
                phone_detail['recorded_date'] = dds[2].get_text(strip=True).replace('First reported','')
                phone_numbers.append(phone_detail)

        person_info['phone_numbers'] = phone_numbers

    
    person_info['emails'] = None
    if emails_soup := soup.select('#email_section .detail-box-email .col-sm-12.col-md-6'):
        person_info['emails'] = [decode_cfemail(email.find('a', class_='__cf_email__')['data-cfemail']) for email in emails_soup]

    person_info['aka_names']  = None
    if aka_soup := soup.select('#aka-links .detail-box-email .col-sm-12.col-md-6'):
        person_info['aka_names'] = [aka.get_text(strip=True) for aka in aka_soup]
    


    address_details = []
    if previous_addresses_soup := soup.select('#previous-addresses .detail-box-address .col-sm-12.col-md-6'):
        for address in previous_addresses_soup:
            if address_link := address.find('a'):
                address_detail = {}
                address_detail['address'] = address_link.get_text(strip=True)
                address_detail['search_link'] = address_link.get('href')
            
            dds = address.find_all('dd')
            address_detail['type'] = dds[0].get_text(strip=True)
            address_detail['recorded_date'] = dds[1].get_text(strip=True).replace('Recorded','').strip()
            address_details.append(address_detail)

    person_info['previous_addresses'] = address_details


    relatives = []
    if relative_soup := soup.select('#relative-links .detail-box-content .col-sm-12.col-md-4'):
        for relative in relative_soup:
            relative_detail = {}
            if relative_link := relative.find('a'):
                relative_detail['name'] = relative_link.get_text(strip=True)
                relative_detail['search_link'] = relative_link.get('href')

            dds = relative.find_all('dd')
            relative_detail['age'] = dds[0].get_text(strip=True)
            if len(dds) > 1:
                relative_detail['relation'] = dds[1].get_text(strip=True)
            relatives.append(relative_detail)

    person_info['relatives'] = relatives

    associates = []
    if associates_soup := soup.select('#associate-links .detail-box-content .col-sm-6.col-md-4'):
        if collapsed_associates := soup.select('#collapsed-associates .col-sm-6.col-md-4'):
            associates_soup.extend(collapsed_associates)
        for associate in associates_soup:
            associate_detail = {}
            if associate_link := associate.find('a'):
                associate_detail['name'] = associate_link.get_text(strip=True)
                associate_detail['search_link'] = associate_link.get('href')

            dds = associate.find_all('dd')
            associate_detail['age'] = dds[0].get_text(strip=True)
        
            associates.append(associate_detail)

    person_info['associates'] = associates

    neighbors = []
    if neighbors_soup := soup.select('#neighbors_section .detail-box-neighbors .col-sm-12.col-md-6'):
        for neighbor in neighbors_soup:
            neighbor_detail = {}
            if neighbor_link := neighbor.select_one('dt a'):
                neighbor_detail['name'] = clean_str(neighbor_link.text)
                neighbor_detail['name_search_link'] = neighbor_link.get('href')
            
            dds = neighbor.find_all('dd')
            
            if dds[0].find('a') and 'phone' in dds[0].find('a').get('title'):
                neighbor_detail['phone'] = dds[0].find('a').get_text(strip=True)
                neighbor_detail['phone_search_link'] = dds[0].find('a').get('href')
            
            if dds[1].find('a') and 'live' in dds[1].find('a').get('title'):
                neighbor_detail['address'] =clean_str(dds[1].find('a').text)
                neighbor_detail['address_search_link'] = dds[1].find('a').get('href')

            neighbors.append(neighbor_detail)

    person_info['neighbors'] = neighbors

    marital_status = False
    if soup.select('#marital_status_section a'):
        marital_status = True

    person_info['marital_status'] = marital_status

    businesses = []
    if business_soup := soup.select('#business_section .detail-box-business .col-sm-12.col-md-6'):
        for business in business_soup:
            business_detail = {}
            if business_link := business.find('dt'):
                business_detail['name'] = business_link.get_text(strip=True)
            
            dds = business.find_all('dd')
            business_detail['address'] = clean_str(dds[0].text)
            business_detail['address'] = clean_str(dds[1].text)
            business_detail['type'] = clean_str(dds[2].text)
            business_detail['register'] = clean_str(dds[3].text)
            businesses.append(business_detail)


    person_info['businesses'] = businesses


    background_report = None
    if background_report_soup := soup.select_one('#background_report_section'):
        if background_report_soup.find('h2'):
            background_report_soup.find('h2').extract()
        for email in background_report_soup.select('.__cf_email__'):
            email.string = decode_cfemail(email['data-cfemail'])


        background_report = clean_str(background_report_soup.text)

    person_info['background_report'] = background_report

    faqs = []
    if faq_soup := soup.select('#faq_section .faq-container'):
        for faq in faq_soup:
            faq_detail = {}
            faq_detail['question'] = clean_str(faq.select_one('h3').text)
            for email in faq.select('.__cf_email__'):
                email.string = decode_cfemail(email['data-cfemail'])
            faq_detail['answer'] = clean_str(faq.select_one('p').text)
            faqs.append(faq_detail)

    person_info['faqs'] = faqs
    details['person_info'] = person_info
    return details


def listing_parser(soup : BeautifulSoup):
    
    details = {}
    details['url'] = soup.select_one('base')['href']
    details['page_title'] = clean_str(soup.select_one('h1.list-results-header').text)

    details['no_of_records'] = soup.select_one('h2').text.split(' ')[0]

    property_details = None
    if property_details_soup := soup.select('#current-addresses-property .detail-box-content dl'):
        property_details = {}
        for dl in property_details_soup:
            property_details[clean_str(dl.find('dt').text)] = clean_str(dl.find('dd').text)

    details['property_details'] = property_details

    people_records = []

    if people_records_soup := soup.select('.people-list .card'):
        for card in people_records_soup:

            people_record = {}
            if people_record_link := card.select_one('h2 a'):
                people_record['title'] = clean_str(people_record_link.text)
                people_record['search_link'] = people_record_link.get('href')
            
            if age_element := card.find('h3',string='Age:'):
                people_record['age'] = clean_str(age_element.find_next_sibling(string=True).text)
            
            if full_name_element := card.find('h3',string='Full Name:'):
                people_record['full_name'] = clean_str(full_name_element.find_next_sibling(string=True).text)
            
            if current_address_element := card.find('h3',string='Current Home Address:'):
                people_record['current_home_address'] = clean_str(current_address_element.find_next_sibling('div').text)
                people_record['current_home_address_search_link'] = current_address_element.find_next_sibling('div').find('a').get('href')
            
            
            if addresses := card.find_all('a',attrs={'title':re.compile('who live at')}):
                people_record['past_addresses'] = [
                    {'address':clean_str(address.text),'address_search_link':address.get('href')} for address in addresses
                ]
            
            if akas_element := card.find('strong',string='AKA:'):
                if akas_element:=akas_element.parent.find_next_siblings('span',class_='nowrap'):
                    people_record['aka_names'] = [clean_str(aka.text) for aka in akas_element]
                

            if phone_numbers := card.find_all('a',attrs={'title':re.compile('phone number')}):
                people_record['phone_numbers'] = []
                for phone_number in phone_numbers:
                    people_record['phone_numbers'].append(clean_str(phone_number.text))
                    if phone_number.parent.name == 'strong' and phone_number.parent.find_next_sibling(string=True)  and 'current' in phone_number.parent.find_next_sibling(string=True).text:
                        people_record['current_phone_number'] = clean_str(phone_number.text)

            if relatives_element := card.find('strong',string='Relatives:'):
                if relatives_element:=relatives_element.parent.find_next_siblings('a',attrs={'title':re.compile('People Search')}):
                    people_record['relatives'] = [{'name':clean_str(aka.text),'search_link':aka.get('href')} for aka in relatives_element]
            people_records.append(people_record)

    details['people_records'] = people_records

    if faq_soup := soup.select('.detail-box-faq  h3'):
        details['faq'] = [
            {'question':clean_str(faq.text),'answer':clean_str(faq.find_next_sibling('p').text)} for faq in faq_soup]
        
    if next_page := soup.find('a',attrs={'title':'Next page of search results'}):
        details['next_page'] = next_page.get('href')

    return details


def fastpeople_parser(html):
    soup = BeautifulSoup(html, 'html.parser')

    if soup.select_one('h1.list-results-header'):
        return listing_parser(soup)
    else:
        return person_detail_parser(soup)
    