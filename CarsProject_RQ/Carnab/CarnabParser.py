from common.utils import *
from .Carnabscraper import carnab_product_scraper
import xmltodict

db = client['carnab']
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



def carnab_parser(product_json):
   
    details = {}

    details['name'] =  product_json['name']
    details['year'] =  product_json['year']
    details['make'] =  product_json['make']['name']
    details['model'] =  product_json['model']['name']
    details['specs'] = product_json['specs']['name']
    details['engine_size'] = product_json['engine']['name']

    details['price'] = product_json['price']
    details['currency'] = product_json['currency']
    details['location'] = product_json['city_name']
    details['images'] = [img['image'] for img in product_json['media']['item'] if img.get('image')]

    details['specification'] = {
        'Trim' : product_json['interiorTrim']['name'],
        'Specs': product_json['specs']['name'],
        'Kilometers': product_json['km'],
        'Body Type': product_json['bodyType']['name'],
        'Fuel Type': product_json['fuelType']['name'],
        'Drive Type': product_json['drive']['name'],
        'Engine Size': product_json['engine']['name'],
        'Exterior Color': product_json['carColor']['name'],
        'Seat Color': product_json['seatColor']['name'],
        'Transmission': product_json['transmission']['name'],
        'Warranty': "Yes" if not product_json['is_warranty_eligible'] else "No",
        'Service History': product_json['service_history'],
    }


    if product_json.get('inspectionReport','') and product_json['inspectionReport'].get('mainSummary',''):
       
        details['inspection_report'] = {
            'summary': {item['heading'] : item['result'] for item in product_json['inspectionReport']['mainSummary']['item']}
        }

        if product_json['inspectionReport'].get('sections',''):
            
            details['inspection_report']['detailed_report'] = {
                    item['title']: {
                        field['fieldLabel'] if field.get('fieldLabel') else '' : field['fieldValue']  for field in item['fields']['item'] 
                         }
                    for item in product_json['inspectionReport']['sections']['item'] if isinstance(item.get('fields', {}).get('item'), list)
                }
           
    if product_json['emiOptions']['optionDownPayment']:
        details['finance']={'price':product_json['emiPerMonth'],
                            'downpayment':round(int(product_json['price']) * (int(product_json['emiOptions']['optionDownPayment']['min_perc'])/100)),
                            'duration':product_json['emiOptions']['optionLoanTenure']['preselected']
                            }

    
    if product_json.get('purchaseOptions',''):
        details['purchase_options'] = [
            {'name':option['name'],
             'description':option['description'],
            'price':option['price']}

            for option in product_json['purchaseOptions']['item']
        ]

    return details

def collect_carnab_data():
    for product in product_collection.find({'scraped':0}):
        url = product['url']
        try:
            if car_details_collection.find_one({'url': url}) is not None:
                continue

            cache_data = check_cache_for({'url': url})

            if cache_data is not None:
                product_json =cache_data['data']
                status = 200
            else:
                req = carnab_product_scraper(url)
                product_json = xmltodict.parse(req.text)
                status = req.status_code
                save_cache_for(url, product_json)

          
            data = carnab_parser(product_json['response'])
            data = {'url': url, **data}
            car_details_collection.insert_one(data)

            product_collection.update_one({'url': url}, {'$set': {'scraped': 1}})
            
        except Exception as ex:
            error_collection.insert_one(
                {
                    'url': url,
                    'status': status,
                    'runner': 'carnab_product',
                    'error': str(ex),
                    'traceback': traceback.format_exc(),
                }
            )

