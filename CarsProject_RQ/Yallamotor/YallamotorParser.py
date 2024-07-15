from common.utils import *

db = client['yallamotor']
product_collection = db['urls']
cache_collection = db['cache']
error_collection = db['error']
car_details_collection = db['car_details']

def yallamotor_parser(url):
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
        details['car_name'] = soup.find('h1').text.strip()

        if soup.select_one('h1 h2'):
            details['car_name'] +=' | '+soup.select_one('h1 h2').text
        
        try:
            price = soup.find('div',class_="col is-4 p0 p16l linehight-normal").find('div',class_="font18 m8t").text.strip()
        except:
            price=''

        details['price'] = price

        details['images']  = ' | '.join([img['src'] for img in soup.find('div',class_="slider slider-single display-grid").find_all('img')])
        

        details['location'] = soup.find('div',string='Location:').find_next_sibling('div').text.strip()

        if soup.find('div',string=re.compile('Updated')):
            details['updated_at'] = soup.find('div',string=re.compile('Updated')).find_next_sibling('div').text.strip()
        

        details['highlights'] =' | '.join([item.find('div',class_="font10 color-gray text-center").text.strip()+' : '+item.find('div',class_="font10 color-gray text-center").find_next_sibling('div').text for item in soup.find('div',id="highlightsnav").find_all('div',class_='box1')])

        details['car_details'] =' | '.join([item.find('div',class_="col is-7 p0").text.strip() +' : '+item.find('div',class_="col is-5 p0 font-b").text.strip() for item in soup.find('label',class_="accordion-title p0t border-unset font24 font-b").find_next_sibling('div',class_="linehight-normal").find_all('div',class_="row is-m is-compact")])

        features = {}

        if soup.select('div#featuresnav label + div div.col.is-6.display-flex'):
            for feature in soup.select('div#featuresnav label'):
                key = feature.text.strip()
                val =' | '.join([li.text.strip() for li in feature.find_next_sibling('div').select('div.col.is-6.display-flex')])
                features[key] = val
        else:
            features = ' | '.join([li.text.strip() for li in soup.select('div#featuresnav div.col.is-6')])

        details['features'] = features
        try:
            details['description'] =re.sub('\s+',' ', ' | '.join([child.text.strip() for child in soup.find('div',id="descriptionnav").find('div',id="whyText").children if child.text.strip()]))
        except:
            pass

        if soup.find('div',class_='singleCard font14 linehight-normal position-rel lineheight-20'):
            details['Related Used Cars'] = []

            for item in soup.find_all('div',class_='singleCard font14 linehight-normal position-rel lineheight-20'):
                car_info = {}
                car_info['car_name'] = item.select_one('div.p12.p8t a').text
                car_info['car_url'] = 'https://uae.yallamotor.com'+item.select_one('div.p12.p8t a')['href']
                car_info['price'] = item.select_one('div.color-ym-blue').text.replace('From','').strip()
                car_info['location'] = item.select_one('div.color-gray').text
                car_info['highlights'] = item.select_one('div.color-gray.align-items-center').text.replace('\n',' ').strip()
                details['Related Used Cars'].append(car_info)
        car_details_collection.insert_one(details)
        product_collection.update_one({'url':url},{'$set':{'scraped':1}})

    except Exception as e:
        error_collection.insert_one({'url':url, 'status':req_status,'date_time': datetime.now(), 'error':str(e), 'traceback':traceback.format_exc()})
