from common import *
from celery_worker import celery_app


db = client['cars24']
product_collection = db['urls']
cache_collection = db['cache']
error_collection = db['error']
car_details_collection = db['car_details']


def get_inspection_report(car_json):
    inspection_report={}
    for i in car_json['inspectionReport']:
        
        cat_title = i['title']
        cat_values = {}
        
        for sub_item in i['child']:
            sub_cat_title = sub_item['title']
            
            if sub_item.get('child'):
                sub_cat_values = {}
                for sub_sub_item in sub_item['child']:
                    sub_sub_cat_title = sub_sub_item['title']
                    if sub_sub_item.get('value'):
                        sub_sub_cat_value = sub_sub_item['value']
                    else:
                        sub_sub_cat_value = 'Passed' if sub_sub_item['status']==1 else 'Imperfections'        
                    sub_cat_values[sub_sub_cat_title] = sub_sub_cat_value
                cat_values[sub_cat_title] = sub_cat_values

            else:
                sub_cat_value = 'Passed' if sub_item['status']==1 else 'Imperfections'
                cat_values[sub_cat_title] = sub_cat_value
                
        inspection_report[cat_title] = cat_values

    return inspection_report

@celery_app.task(queue='cars24')
def cars24_parser(url):
    try:
        cached_data = cache_collection.find_one({'url': url})
        details = {}
        details['url'] = url

        if cached_data:
            html = cached_data['data']
            req_status = 200
        else:
            req = send_req_syphoon(1, 'GET', url)
            req_status = req.status_code
            req.raise_for_status()
            cache_collection.insert_one(
                {'url': url, 'data': req.text, 'status':req_status}
            )
            html = req.text
        soup = BeautifulSoup(html, 'html.parser')

        details ={}

        car_json = json.loads(soup.find('script',string=re.compile('window.__PRELOADED_STATE__ ')).text.replace('window.__PRELOADED_STATE__ = ','').replace('}}};','}}}'))['carDetails']
        details['url'] = url
        details['car_name'] = soup.find('h1').text

        details['price'] = car_json['content']['price']

        if car_json['content'].get('discounted',''):
            details['discount'] = car_json['content'].get('discountAmount','')
            details['actual_price'] = car_json['content']['targetPrice']

        details['is_booked']  = car_json['content']['booked']

        details['images'] = ' | '.join([image['src'] for image in soup.find('div',id="horizontalSliderContainer").find_all('img')])

        details['highlight'] =' | '.join(i.text.strip() for i in soup.find('div',class_="gBinz").find('p').contents if i.text.strip())
        
        details['car_details']  =' | '.join([f'{item["name"]} : {item["value"]}' for item in car_json['content']['basicDetails'] if item['name'] != 'VIN number'])



        features = {}

        for item in car_json['content']['allFeatures']:
            feature_name = item['categoryName']
            feature_value =' | '.join([i['name'] for i in item['specs']])
            features[feature_name] = feature_value

        details['features'] = features
        
        details['inspection_report'] = get_inspection_report(car_json['content'])

        details['service_history'] = car_json['content']['serviceHistory']

        details['emi_info'] = car_json['content']['emiDetails']

        details['similarCars'] = []
        for item in car_json['similarCars']:
            car_info = {}
            car_info['car_name'] = f"{item['year']} {item['make']} {item['model']}"
            car_info['car_url'] = item['shareUrl']
            car_info['car_price'] = item.get('price','')

            if car_info.get('discounted',''):
                car_info['discount_amount'] = item['discountAmount']
                car_info['actual_price'] = item['targetPrice']
            
            car_info['odometer'] = item.get('odometerReading','')
            car_info['transmission_Type'] = item.get('transmissionType','')
            car_info['fuel_type'] = item.get('fuelType','')

            details['similarCars'].append(car_info)

        car_details_collection.insert_one(details)
        product_collection.update_one({'url':url},{'$set':{'scraped':1}})
    
    except Exception as e:
        error_collection.insert_one({'url':url, 'status':req_status,'date_time': datetime.now(), 'error':str(e), 'traceback':traceback.format_exc()})
    
@celery_app.task(queue='cars24')
def start_scraper():
    for url in product_collection.find({'scraped':0}):
        print(url['url'])
        cars24_parser.delay(url['url'])
        
if __name__ == '__main__':
    # print(cars24_parser('https://www.cars24.ae/buy-used-hyundai-tucson-2022-cars-dubai-9716628590/'))
    # print(cars24_parser('https://www.cars24.ae/buy-used-hyundai-tucson-2020-cars-dubai-9714828290/'))
    # print(cars24_parser('https://www.cars24.ae/buy-used-chevrolet-captiva-2023-cars-dubai-9716147589/'))
    print(cars24_parser('https://www.cars24.ae/buy-used-bmw-318i-2018-cars-dubai-9714826293/'))