from common import *
from celery_worker import celery_app



db = client['dubaicars']
product_collection = db['urls']
cache_collection = db['cache']
error_collection = db['error']
car_details_collection = db['car_details']

def get_specifications(soup):
    specifications  = {}
    for section in soup.find('section',id="services-seller").find_all('li',class_='faq__item'):
        info_header = section.h4.text
        info_value = [f'{li.span.text.strip()} : {li.span.find_next_sibling().text.strip()}' if li.span.find_next_sibling() else li.span.text for li in section.find_all('li')]
        specifications[info_header] = info_value

    return specifications

def get_description(soup):
    description =[]
    for line in soup.find('section',id="card-description").find(id="car-description").strings:
        description.append(line.strip())
    description = ' | '.join(description)
    return description

@celery_app.task(queue = 'dubaicars')
def dubaicars_parser(url):
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
        soup = BeautifulSoup(html, 'lxml')

        details = {}
        details['url'] = url

        details['car_name'] = soup.find('span',class_="car-title fw-700").text
        try:warranty_info = soup.find('section',id="badge-warranty-description").find(class_='popup-body').text
        except: warranty_info = 'Not Available'
        details['warranty_info'] = warranty_info

        details['updated_on'] = soup.find('span',class_="icon-back-in-time time fs-14 text-dark").text.replace('Updated:','').strip()
        details['price_info'] = soup.find('div',class_="price fs-24 fw-600 text-primary currency-price-field").text
        details['images'] =  ' | '.join(['https:'+img.find('source')['srcset'] for img in soup.find('section',id="car-images-slider").find_all('li',class_="carImageItem")])
        details['seller_name'] = soup.find('section',id="seller-info").find('div',class_="seller-intro").text.replace('Posted by','').strip()
        details['highlights'] = [f'{li.span.text.strip()} : {li.span.find_next_sibling().text}' for li in soup.find('section',id="highlights").find_all('li')]
        details['specifications'] = get_specifications(soup)
        details['description'] = get_description(soup)



        for section in soup.select('section.similar-cars'):
            details[section.find('h2').text.strip()] = []

            for li in section.select('ul.car-cards-list li.car-card'):
                car_info = {}
                car_info['car_name'] = li.select_one('div.title').text
                car_info['url']  = li.select_one('a')['href']
                car_info['price'] = li.select_one('span.price').text
                car_info['location'] = li.select_one('div.location').text
                car_info['highlights'] = '|'.join([ i.text for i in li.select('ul.car-card-footer li')])

                details[section.find('h2').text.strip()].append(car_info)


        car_details_collection.insert_one(details)
        product_collection.update_one({'url':url},{'$set':{'scraped':1}})

    except Exception as e:
        error_collection.insert_one({'url':url, 'status':req_status,'date_time': datetime.now(), 'error':str(e), 'traceback':traceback.format_exc()})

@celery_app.task(queue = 'dubaicars')
def start_scraper():
    for url in product_collection.find({'scraped':0}).limit(10):
        print(url['url'])
        dubaicars_parser.delay(url['url'])
  
if __name__ == '__main__':
    print('DubaiCarsParser Test')
    print(dubaicars_parser('https://www.dubicars.com/2024-bmw-ix3-bmw-ix3-create-version-m-sport-2024-model-700923.html'))