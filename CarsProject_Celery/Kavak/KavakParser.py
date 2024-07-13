from celery_worker import celery_app
from common import *

db = client['kavak']
product_collection = db['urls']
cache_collection = db['cache']
error_collection = db['error']
car_details_collection = db['car_details']


def get_features(car_info_json):
    
    features = {} 

    for section in car_info_json['features']['types']:
        title = section['title']
        values = []
        for item in section['items']:
            values.append(f"{item['name']} : {item['value']}")
        features[title] =' | '.join(values)

    return features

@celery_app.task(queue = 'kavak')
def kavak_parser(url):

    try:
        cached_data = cache_collection.find_one({'url': url})
        details = {}
        details['url'] = url

        if cached_data:
            html = cached_data['data']
            req_status = 200
        else:
            req = send_req_syphoon(PROXY_VENDOR, 'GET', url)
            req_status = req.status_code
            req.raise_for_status()
            cache_collection.insert_one(
                {'url': url, 'data': req.text, 'status':req_status}
            )
            html = req.text

        soup = BeautifulSoup(html, 'html.parser')
        car_info_json = json.loads(soup.find('script',id="serverApp-state").text.replace('&q;','"'))['https://api.kavak.com/drago-vip/init']['vipData']

        details['car_name']  = soup.find('h1',class_="title").text.strip()
        
        if car_info_json['buyBox'].get('messages',''):
            if 'reserved' in car_info_json['buyBox']['messages'][0].get('text',''):
                details['is_sold'] = True
        else:
            details['odometer'] =  soup.find('h1',class_="title").find_next_sibling('p').text.split('•')[0].strip()

            details['price'] = soup.find('div',class_="price-item-footer").text.replace('AED','AED ').strip()
        
            if car_info_json['data']['mainResult'].get('monthly_payment',''):
                details['monthly_emi'] = car_info_json['data']['mainResult']['monthly_payment']

            details['highlights'] = f'Year : {car_info_json["data"]["mainResult"]["car_year"]} | Version : {car_info_json["data"]["mainResult"]["car_trim"]} | Transmission : {car_info_json["data"]["mainResult"]["transmission"]}'
            
            details['images'] = ' | '.join(['https://images.prd.kavak.io/'+x for x in car_info_json['media']['gallery']['images']])

            details['overview'] = ' | '.join([x.find(class_="name").text.strip()+' : '+x.find(class_="description").text.strip() for x in soup.find_all('div',class_="feature-content")])
            
            details['features']  = get_features(car_info_json)

        if car_info_json['lateralNavigation']:
            details['Other Cars'] = []

            for item in car_info_json['lateralNavigation'][0]['cars']:
                car_info = {}
                car_info['car_name'] = item['title']
                car_info['url'] = item['url']
                car_info['year'] = item['year']
                car_info['odometer'] = item.get('mileage','0 km')
                car_info['price'] = item['plainPrice']
                car_info['monthly_emi'] = item['plainMonthlyPayment']

                details['Other Cars'].append(car_info)

        car_details_collection.insert_one(details)
        product_collection.update_one({'url':url},{'$set':{'scraped':1}})

    except Exception as e:
        error_collection.insert_one({'url':url, 'status':req_status,'date_time': datetime.now(), 'error':str(e), 'traceback':traceback.format_exc()})

@celery_app.task(queue = 'kavak')
def start_scraper():
    for url in product_collection.find({'scraped':0}):
        print(url['url'])
        kavak_parser.delay(url['url'])
        
if __name__ == "__main__":

    # print(kavak_parser("https://www.kavak.com/ae/cars-for-sale/jac-j7-intelligent-sedan-2023"))
    # print(kavak_parser("https://www.kavak.com/ae/cars-for-sale/toyota-corolla-xli_executive_hybrid-sedan-2020"))
    # print(kavak_parser("https://www.kavak.com/ae/cars-for-sale/ford-taurus-trend-sedan-2021"))
    print(kavak_parser("https://www.kavak.com/ae/cars-for-sale/volkswagen-passat-highline-sedan-2020"))




    