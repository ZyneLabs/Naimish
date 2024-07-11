from common import *
from celery_worker import celery_app
import json
import traceback

db = client['automalluae']
product_collection = db['product']
cache_collection = db['cache']
error_collection = db['error']
car_details_collection = db['car_details']

def get_specifications(soup):
    specification = {}
    spec_area = soup.find('div',id="prin-spec")
    for item in spec_area.select('div.mb-0.d-flex.card-header.pl-0'):
        spec_header = item.find('p',class_="mediumFontType").text
        specs = {}

        for row in item.parent.next_sibling.select('div.row.border-bottom'):
            title = row.select_one('div.col.p-0.labelField').text
            if row.select('div.col.p-0.valueField li'):
                val =' | '.join([li.text.capitalize() for li in row.select('div.col.p-0.valueField li')])
            else:
                val = row.select_one('div.col.p-0.valueField').text
            specs[title] = val
        specification[spec_header] = specs
    return specification


@celery_app.task(queue='automalluae')
def automalluae_parser(url):

    try:
        cached_data = cache_collection.find_one({'url': url})
        details = {}
        details['url'] = url

        if cached_data:
            html = cached_data['data']
            req_status = 200
        else:
            req = send_req_syphoon(0, 'GET', url)
            req_status = req.status_code
            req.raise_for_status()
            cache_collection.insert_one(
                {'url': url, 'data': req.text, 'status':req_status}
            )
            html = req.text

        soup = BeautifulSoup(html, 'html.parser')

        page_json = json.loads(soup.find('script',id="__NEXT_DATA__").text)

        details['car_name'] = soup.select_one('div.col-lg-4.order-2.order-lg-1 p').text
        
        details['reference_id'] = soup.select_one('div.col-lg-4.order-2.order-lg-1 div.col-6.text-right').text.replace('Reference','').strip()
        
        details['year'] = soup.select_one('div.col-lg-4.order-2.order-lg-1 p').next_sibling.text
        
        details['highlight'] = [li.text.strip() for li in soup.select('div.container-lg.px-0 div.row div.row div.col-12 div[dir="ltr"]')]
        
        details['price'] = soup.find('div',class_='mediumFontType').text.strip()
        
        details['monthly_pay'] = page_json['props']['pageProps']['detailCarInfo']['Price_Monthly']

        details['images'] = ' | '.join(img['src'] for img in soup.select('.photoBoothCarousel li.slide img'))

        details['specification'] = get_specifications(soup)

        details['recommended_cars'] = []

        for recommended_type in page_json['props']['pageProps']['recommendedCars']:
            for car in page_json['props']['pageProps']['recommendedCars'][recommended_type]:
                car_detail = {}
                car_detail['car_name'] = f"{car['make']} {car['gradeName']}"
                car_detail['car_url'] = f'https://www.automalluae.com/en/used-cars-shop/details/{car["id"]}'.lower()
                car_detail['price'] = car.get('Price_From','')
                car_detail['monthly_pay'] = car.get('Price_Monthly','')
                car_detail['modelYear'] = car.get('modelYear','')
                car_detail['odometer'] = car.get('odometer','')
                car_detail['fuelType'] = car.get('fuelType','')
                car_detail['color'] = car.get('exteriorColoursValue','')
                details['recommended_cars'].append(car_detail)

        car_details_collection.insert_one(details)
        product_collection.update_one({'url':url},{'$set':{'scraped':1}})
    
    except Exception as e:
        error_collection.insert_one({'url':url, 'status':req_status, 'error':str(e), 'traceback':traceback.format_exc()})

@celery_app.task(queue='automalluae')    
def start_scraper():
    for url_data in product_collection.find({'scraped':0}):
        url = url_data['url']
        print(url)
        automalluae_parser.delay(url)
       

if __name__ == '__main__':
   
    # print(automalluae_parser('https://www.automalluae.com/en/used-cars-shop/details/jtmabcbj6n4048334/'))
    # print(automalluae_parser('https://www.automalluae.com/en/used-cars-shop/details/w1n0j8bb8ng065843/'))
    # print(automalluae_parser('https://www.automalluae.com/en/used-cars-shop/details/jtmabcbjxn4048868/'))
    print(automalluae_parser('https://www.automalluae.com/en/used-cars-shop/details/1gnsk8kl0pr172146/'))