from common.utils import *
from .Albacarsscraper import albacars_scraper

db = client['albacars']
product_collection = db['urls']
cache_collection = db['cache']
error_collection = db['error']
car_details_collection = db['car_details']

def check_cache_for(data):
    return cache_collection.find_one(data)

def save_cache_for(url,data):
    
    cache_collection.insert_one(
            {
                'url': url,
                'data': data,
                'updated_at': datetime.now(),
                'data_format': 'html',
                'info_type': 'parse',
                'info_subtype': 'product_parse',
            }
        )



def albacars_parser(html):
    soup = BeautifulSoup(html, 'html.parser')

    details = {}

    maybe_title = soup.select_one('h1')

    if not maybe_title:
        return {'message':'Post page not found'}

    details['name'] =  maybe_title.text.replace('\n', ' ').strip()
    details['year'] = soup.select_one('.carmodelrow h4 span').text.strip()
    details['price'] = soup.select_one('.aedbgrw').text.replace('\n', ' ').strip()
    
    maybe_finance_soup = soup.select_one('.downpaymentbox desktop_version')

    if maybe_finance_soup:
        details['finance'] = {
            "payment": maybe_finance_soup.select_one('.pricebxes').text.strip(),
            'downpayment': maybe_finance_soup.select_one('.percentage').text.split('Downpayment')[0].strip(),
            'duration': maybe_finance_soup.select_one('.percentage').text.split('Downpayment')[1].strip()
        }

    details['images'] = [img['src'] for img in soup.select('#slider img')]

    specification_soup = soup.select('.specificationdividebx .optionnm')
    if specification_soup:
        details['specification'] = {
            item.select_one('.lftt').text.replace(':','').strip(): item.select_one('.rttt').text.strip()
            for item in specification_soup
        }
    
    description_soup = soup.select('#description p')
    if description_soup:
        details['description'] = ' | '.join([item.text.strip() for item in description_soup])

    documents = {}

    for h3 in soup.select('#documents h3'):
        category = h3.get_text(strip=True).replace(':', '')
        documents[category] = []
        for sibling in h3.find_next_siblings():
            if sibling.name == "h3":
                break
            if sibling.name == "p":
                text = sibling.get_text(strip=True)
                if not text.startswith("( Note:"):
                    documents[category].append(text)
    if documents:
        details['documents'] = documents

    similar_cars = []
    for car in soup.select('.listviews a'):
        similar_cars.append({
            'name': car.select_one('.carnm').text.split('AED')[0].strip(),
            'url': car['href'],
            'price': car.select_one('.titlenm').text.strip(),
            'year': car.select_one('.modelyr').text.strip(),
            'odometer': car.select_one('.kms').text.strip(),
            'image': car.select_one('img')['src'],
            'finance': {
                'payment': car.select_one('.aedprice').text.strip(),
                'downpayment': car.select_one('.downpayment').text.split('Downpayment')[0].strip(),
                'duration': car.select_one('.downpayment').text.split('Downpayment')[1].strip()
            }
        })
    if similar_cars:
        details['similar_cars'] = similar_cars

    return details

def collect_albacars_data():
    for product in product_collection.find({'scraped':0}):
        url = product['url']
        try:
            if car_details_collection.find_one({'url': url}) is not None:
                continue

            cache_data = check_cache_for({'url': url})

            if cache_data is not None:
                html = cache_data['data']
                status = 200
            else:
                req = albacars_scraper(url)
                html = req.text
                status = req.status_code
                save_cache_for(url, html)

            data = albacars_parser(html)
            data = {'url': url, **data}
            car_details_collection.insert_one(data)

            product_collection.update_one({'url': url}, {'$set': {'scraped': 1}})
        except Exception as ex:
            error_collection.insert_one(
                {
                    'url': url,
                    'status': status,
                    'runner': 'Opensooq_product',
                    'error': str(ex),
                    'traceback': traceback.format_exc(),
                }
            )

