from common import *
from celery_worker import celery_app
from lxml import html


db = client['carswitch']
product_collection = db['urls']
cache_collection = db['cache']
error_collection = db['error']
car_details_collection = db['car_details']

def get_features(soup):
    features = {}
    if soup.find('div',id="driving_ease"):
        features['Driving Ease'] =[item['data-searchable'] for item in soup.find('div',id="driving_ease").find('div',class_="car-overview__features").find_all('div',class_='item') if 'disable' not in item.get('class')]

    if soup.find('div',id="entertainment_feature"):
        entertainment =[item['data-searchable'] for item in soup.find('div',id="entertainment_feature").find('div',class_="car-overview__features").find_all('div',class_='item') if 'disable' not in item.get('class')] 
        features['Entertainment'] = entertainment
    if soup.find('div',id="comfort_convenience_feature"):
        comfort = [item['data-searchable'] for item in soup.find('div',id="comfort_convenience_feature").find('div',class_="car-overview__features").find_all('div',class_='item') if 'disable' not in item.get('class')] 
        features['Comfort & Convenience'] = comfort

    if soup.find('div',id="safety_feature"):
        safety = [item['data-searchable'] for item in soup.find('div',id="safety_feature").find('div',class_="car-overview__features").find_all('div',class_='item') if 'disable' not in item.get('class')]
        features['Safety & Security'] = safety

    return features


def get_inspetion_data(soup):
    
    inspection_history ={}

    # used lxml due to the html structure 
    # text was not captured by beautiful soup 
    # so i moved to lxml
    
    if soup.find('div',class_="inspection-area-holder") is None:
        return inspection_history
    
    inspection_holder =html.fromstring(soup.find('div',class_="inspection-area-holder").prettify())
    inspection_history['Inspeted_At'] =inspection_holder.xpath('//small/text()')[0].replace('Inspected:','').strip()

    for item in inspection_holder.xpath('//div[@class="item"]'):
        header = ''.join(item.xpath('.//div[@class="auto-fr heading"]/span//text()')).strip()

        tests=[]
        if item.xpath('.//ul/li'):
            for li in item.xpath('.//ul/li'):
                if li.xpath('./svg[contains(@class,"success-icon")]'):
                    test = 'Passed'
                else:test = 'Imperfection'
                name = ''.join(li.xpath('./svg/following-sibling::text()')).strip()

                tests.append(f'{name} : {test}')

        elif item.xpath('.//div[@class="scrach-item"]'):
            for li in item.xpath('.//div[@class="scrach-item"]'):
                place = ''.join(li.xpath('.//h5/text()')).strip()
                damage_type = ''.join(li.xpath('.//small/text()')).strip()
                image = ''.join(li.xpath('.//img/@data-src')).strip()
                test = {'place':place,'damage_type':damage_type,'image':image}
                tests.append(test)
        inspection_history[header] = tests


    return inspection_history

@celery_app.task(queue='carswitch')
def carswitch_parser(url):
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
        soup = BeautifulSoup(html, 'lxml')
        
        car_info_holder = soup.find('div',class_="car-info-holder")
        details['car name'] =  car_info_holder.find('h1',class_="title").text

        if soup.select_one('.detail-page.sold'):
            details['is_sold'] = True

        car_details = car_info_holder.find('div',class_="mileage-area").find_all('span',class_="mileage_text")
        details['year'] = car_details[0].text
        details['mileage'] = car_details[1].text
        details['carid'] = car_details[2].text

        details['location'] = car_info_holder.find('span',class_="location_text").text.strip()


        details['highlights'] =[li.text.strip() for li in soup.find('div',class_="deals-badges tags-holder").find_all('div')]
        
        if soup.select_one('div.price-area div.price'):
            details['price'] = soup.select_one('div.price-area div.price').text
        if soup.select_one('div.price-area div.price.show-old-price'):
            details['actual_price'] = soup.select_one('div.price-area div.price.show-old-price').get('data-old-price')
            details['discount'] = int(details['actual_price'].replace('AED','').replace(',','')) - int(details['price'].replace('AED','').replace(',',''))

        if soup.select_one('div#emi-opener span.emi-per-month'):
            details['monthy_emi'] = soup.select_one('div#emi-opener span.emi-per-month').text

        details['images'] = '|'.join([img['data-src'] for img in soup.find('div',class_="preview").find_all('img')])
        

        details['features']= get_features(soup)

        details['specifications']  = [f'{li.find("div",class_="feature-name").text.strip()} : { li.find("div",class_="feature-value").text.strip()}' for li in soup.find('div',id="about-car-modal").find_all('div',class_="feature-list__item")]

        accident_history = {}

        accident_history['Accidents'] = soup.select_one('div#accident-history-modal div.fr-auto div.content-text.accident-value').text.strip()

        if soup.select_one('div#accident-history-modal div.accident-detail-holder .content-text'):
            accident_history['Accident detail'] = soup.select_one('div#accident-history-modal div.accident-detail-holder .content-text').text.strip()

        details['accident history'] = accident_history

        details['inspection history'] = get_inspetion_data(soup)

        for section in soup.select('div.featured-cars'):
            if not section.find('h3').text.strip(): continue
            
            details[f"{section.find('h3').text.strip()}"] = []

            car_info = {}
            for car in section.select('div.pro-item'):
                car_info['car name'] = car.select_one('div.title a').text.strip()
                car_info['url'] = 'https://carswitch.com' + car.select_one('div.title a')['href']
                car_info['price'] = car.select_one('div.title a + span').text.strip()
                car_info['year'] = car.select_one('div.item span').text.strip()
                car_info['mileage'] = car.select('div.item span')[1].text.strip()

                details[f"{section.find('h3').text}"].append(car_info)

        car_details_collection.insert_one(details)
        product_collection.update_one({'url':url},{'$set':{'scraped':1}})

    except Exception as e:
        error_collection.insert_one({'url':url, 'status':req_status, 'error':str(e), 'traceback':traceback.format_exc()})

@celery_app.task(queue='carswitch')
def start_scraper():
    for url in product_collection.find({'scraped':0}):
        print(url['url'])
        carswitch_parser.delay(url['url'])
        

if __name__ == '__main__':
    print('Carswitch Parser Test')
    # print(carswitch_parser('https://carswitch.com/dubai/used-car/mercedes/glc300/2021/522612-526474'))
    # print(carswitch_parser('https://carswitch.com/dubai/used-car/bmw/x2/2021/534033-537895'))
    print(carswitch_parser('https://carswitch.com/sharjah/used-car/lexus/nx300/2021/537771-541633'))




