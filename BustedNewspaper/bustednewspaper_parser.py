from bustednewspaper_scraper import bustednewspaper_scraper
from bs4 import BeautifulSoup
from pymongo import MongoClient
from datetime import datetime
import pandas as pd


client = MongoClient("localhost", 27017)
db = client["bustednewspaper"]
data_details = db["crime_details"]
cache_data = db["cache_data"]
urls_collection = db["urls"]


def bustednewspaper_parser(url_data):

    try:
        details  = {}

        url = details['Booking Page Url'] =url_data['url']
        details['State'] = url_data['state']
        details['State Url'] = url_data['state_url']
        details['County'] = url_data['county'].replace('County','').strip()
        details['County Url'] = url_data['county_url']

        cache = cache_data.find_one({'url': url})
        if cache:
            html  = cache['html']
        else:
            response = bustednewspaper_scraper('YV749KjNlvgdbjsVWkW3','get',url)
            response.raise_for_status()
            cache_data.insert_one({'url': url, 'html': response.text,'timestamp': datetime.now()})
            html = response.text
        soup = BeautifulSoup(html, 'html.parser')

        if soup.select_one('span.dtreviewed time'):
            details['Registered Datetime'] = soup.select_one('span.dtreviewed time').text

        if soup.select_one('span.cats a'):
            details['Area'] = soup.select_one('span.cats a').text

        if soup.select_one('div.featured img'):
            details['Image'] = soup.select_one('div.featured img')['srcset'].split(',')[-1].strip().split(' ')[0]
            details['Image Name'] = details['Image'].split('/')[-1]

        # booking details
        for tr in soup.select_one('h2.post-title.item ~ table').find_all('tr'):
            header = tr.find('th').text.strip().capitalize()
            details[header] = tr.find('td').text.strip()

        # charges
        charges = []
        if soup.select_one('h2#booking-charges-header ~ table'):
            for table in soup.select('h2#booking-charges-header ~ table'):
                charge_details = []
                for tr in table.find_all('tr'):
                    header = tr.find('th').text.strip().capitalize()
                    val = tr.find('td').text.strip() or 'N/A'
                    charge_details.append(f'{header}: {val}')
                charges.append(', '.join(charge_details))
            charges = ' | '.join(charges)

        elif soup.select_one('h2#booking-charges-header ~ p'):
            charges = soup.select_one('h2#booking-charges-header ~ p').text.strip()

        details['Charges'] = charges        
        details['Timestamp'] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        details['Data']  = details['Name'].upper()
        return details
    
    except Exception as e:
        return {'error': 'Error scraping Busted Newspaper','exception': str(e)}
    

if __name__ == "__main__":
    
    # urls = [
    # {'url':'https://bustednewspaper.com/alabama/jenna-danielle-groome/20240105-174500/','state':'Alabama'},
    # {'url':'https://bustednewspaper.com/alabama/barefield-jacob-dylan/20240716-234600/','state':'Alabama'},
    # {'url':'https://bustednewspaper.com/alabama/brown-hallie-marion/20240717-143000/','state':'Alabama'},
    # {'url':'https://bustednewspaper.com/alabama/johnny-whitehead/20240717-022000/','state':'Alabama'},
    # {'url':'https://bustednewspaper.com/alabama/bone-ozmondiaz-lajuan/20240716/','state':'Alabama'},
    # {'url':'https://bustednewspaper.com/alabama/kirkland-eric-clayton/20240717/','state':'Alabama'},
    # {'url':'https://bustednewspaper.com/alabama/warner-corey-kneith/20240716/','state':'Alabama'},
    # {'url':'https://bustednewspaper.com/alabama/audra-croft/20240715-201500/','state':'Alabama'},
    # {'url':'https://bustednewspaper.com/alabama/houston-lovie-lindaria/20240712/','state':'Alabama'},
    # {'url':'https://bustednewspaper.com/alabama/warren-sean/20240717-033100/','state':'Alabama'},
    # {'url':'https://bustednewspaper.com/alabama/jermika-kennedy/20200106-223000/','state':'Alabama'},
    # {'url':'https://bustednewspaper.com/alabama/roberson-brian-todd/20240711-233800/','state':'Alabama'},
    # {'url':'https://bustednewspaper.com/alabama/chatham-danny-earl/20240716-120800/','state':'Alabama'},
    # {'url':'https://bustednewspaper.com/alabama/willard-lowery/20220714-003400/','state':'Alabama'},
    # {'url':'https://bustednewspaper.com/arkansas/gina-marie-esumi-lowrie/20240716-182600/','state':'Arkansas'},
    # {'url':'https://bustednewspaper.com/arkansas/gina-marie-esumi-lowrie/20240716-182600/','state':'Arkansas'},
    # {'url':'https://bustednewspaper.com/arkansas/williams-rufus-b-j/20240716-141200/','state':'Arkansas'},
    # {'url':'https://bustednewspaper.com/arkansas/cody-roberts/20180103-223100/','state':'Arkansas'},
    # {'url':'https://bustednewspaper.com/arkansas/karen-shehane/20180103-213900/','state':'Arkansas'},
    # {'url':'https://bustednewspaper.com/arkansas/taylor-justan-michael/20240716-023500/','state':'Arkansas'},
    # {'url':'https://bustednewspaper.com/arkansas/darius-dewayne-jamerson/20240715-183700/','state':'Arkansas'},
    # {'url':'https://bustednewspaper.com/arkansas/jason-bullock/20180102-154400/','state':'Arkansas'},
    # {'url':'https://bustednewspaper.com/arkansas/mills-rasheed-jaquan/20240717-012400/','state':'Arkansas'},
    # {'url':'https://bustednewspaper.com/arkansas/young-dontray/20240717-133700/','state':'Arkansas'},
    # ]
    
    urls = urls_collection.aggregate([
        {'$match':{'scraped':0}},
        {'$sample':{'size':1000}},
        {'$limit':150}
    ])
    data = []
    for url in urls:
        details = bustednewspaper_parser(url)
        if details:
            data.append(details)
            data_details.insert_one(details)
            urls_collection.update_one({'url':url['url']},{'$set':{'scraped':1}})
        # df1 = pd.DataFrame(data)
        # df = pd.concat([df,df1])
    
    df = pd.DataFrame(data)
    available_columns = list(df.columns)
    index_positions = ['Registered Datetime','Area','Name','Age','Race','Sex','Arrested by','Booked','Height','Weight','Image','Image Name','Hair','Eye','Dob','State','County','Data','County Url','Booking Page Url','Charges','Timestamp']

    # append remain columns before Timestamp
    for i in available_columns:
        if i not in index_positions:
            index_positions.insert(-1,i)

    df = df.reindex(columns=index_positions)
    df.to_excel('bustednewspaper_sample_data_2.xlsx',index=False)
        