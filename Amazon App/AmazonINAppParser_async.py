import asyncio
import aiofiles
from aiohttp import ClientSession
from bs4 import BeautifulSoup
import os
import json
import re
import time


#  This code is under testing for async mode


PROXY_VENDOR = os.getenv('PROXY_VENDOR')

def get_digit_groups(input_str):
    if input_str is None:
        return []
    return re.findall(r'\d+', input_str)

def clean_str(input_str, sep="|"):
    if input_str is None:
        return ""

    if type(input_str) is not str:
        return input_str

    input_str = re.sub(r"\s+", " ", input_str).replace("\n", sep)

    return input_str.strip()


def get_reviews(review_Soup):
    try:
        reviews = review_Soup.find(attrs={"data-hook":"cr-filter-info-review-rating-count"}).text.split('ratings,')[1].split('with')[0].strip()
    except:reviews = 0

    return reviews


def create_asin_mapping(asin_codes, options, pattern):
    attribute_keys = pattern['key']
    asin_mapping = {}

    for key, asin in asin_codes.items():
        indices = list(map(int, key.split(':')))
        
        attributes = {}
        for attr_key, index in zip(attribute_keys, indices):
            attributes[attr_key] = options[attr_key][index]

        asin_mapping[asin] = attributes

    return asin_mapping

def get_stock_condition(variation_info, soup, response_data):
    current_selection = json.loads(soup.find('script',attrs={'data-a-state':'{"key":"twister-plus-mobile-inline-twister"}'}).text)  
    
    stock_condition = {}
    if current_selection['selectedDimensions'].get('size_name','') or current_selection['selectedDimensions'].get('size_name','')==0:    
        selected_color = variation_info['variants']['color_name'][current_selection['selectedDimensions']['color_name']]
        available_sizes = [variation_info['asin_mapping'][x]['size_name'] for x in variation_info['asin_mapping'] if variation_info['asin_mapping'][x]['color_name'] == selected_color ]
        for i in range(len(variation_info['variants']['size_name'])):
            stock_condition[variation_info['variants']['size_name'][i]] = '1' if variation_info['variants']['size_name'][i] in available_sizes else 'OOS'
        
        response_data['Variants'] = variation_info['variants']['size_name'][current_selection['selectedDimensions']['size_name']]

    response_data['Stock Condition'] = ' | '.join([ f"{key} : {value}" for key, value in stock_condition.items()])
    # response_data['Current Variant'] = [ f"{current_selection['dimensionDisplayText'][key]} : {value}" for key, value in variation_info['asin_mapping'][response_data['RPC']].items()]
    return response_data

def parse_amazon_page(soup,url=None,asin=None,variation_info=None):

    response_data = {}

    response_data['RPC'] = asin 
    response_data['url'] = url 

    response_data['Product Name'] = soup.find(id='title').get_text().strip()

    # Brand
    try:
        response_data['Brand'] = soup.find(id="amznStoresBylineLogoTextContainer").get_text().split('\n')[0].split('Visit')[0].strip()
    except:
        response_data['Brand'] = soup.find(id="bylineInfo").text.replace('Brand:','').strip()

    response_data['Brand'] = response_data['Brand'].replace('Visit the','').replace('store','')

    # Images
    response_data['Images'] = " | ".join([img.find('img')['src'] if img.find('img') else img.find('div',attrs={"data-a-image-name":"altImage"}).get('data-a-image-source') for img in soup.find_all('li',attrs={'data-csa-c-media-type':'IMAGE'})])

    # Discount
    if soup.find(class_='savingsPercentage'):
        discount_percentage = soup.find(class_="a-section a-spacing-none aok-align-center aok-relative").find(class_='savingsPercentage').text.replace('-','')
        promo_price = soup.find(class_="a-section a-spacing-none aok-align-center aok-relative").find('span',class_='priceToPay').text.replace('₹','').strip()
    else:
        discount_percentage = None
        promo_price = None

    response_data['Discount'] = discount_percentage
    response_data['Promo Price'] = promo_price

    
    # List Price
    list_price = None
    if soup.find(class_="basisPrice"):
        list_price = soup.find(class_="basisPrice").find(class_='a-price a-text-price').find(class_='a-offscreen').text.replace('₹','').strip()
    response_data['List Price'] = list_price

    if not response_data['RPC'] :
        response_data['RPC'] = soup.find(id="mediaBlockEntities").get('data-asin')
    
    # Variants and Stock Condition
    if variation_info:
        response_data= get_stock_condition(variation_info, soup, response_data)
        response_data['Color Grouping'] = ' | '.join(variation_info['color_grouping'])

    # Color of Variant
    if soup.find(id="inline-twister-expanded-dimension-text-color_name"):
        response_data['Color of Variant']  = soup.find(id="inline-twister-expanded-dimension-text-color_name").text.strip()
      
        
    maybe_rating = soup.select_one('span[data-hook="average-stars-rating-text"]')
    if maybe_rating:
        response_data['Rating'] = maybe_rating.text.split('out')[0].strip()
     
    elif soup.select_one("#acrCustomerReviewLink i"):
        response_data['Rating'] = [rating for rating in soup.select_one("#acrCustomerReviewLink i").attrs['class'] if rating.startswith('a-star-small-')][0].replace('a-star-small-','').replace('-','.').strip()

    # Specification

    sepecification = {}
    if soup.find_all('table',class_='productOverviewBtf_feature_div_table'):

        for spec in soup.find_all('table',class_='productOverviewBtf_feature_div_table'):
            header = spec.find('h4').text
            val = {}
            for item in spec.find_all('tr'):
                val[item.find('th').text.strip()] = item.find('td').text.strip()
            sepecification[header] = val
        
        response_data['Specification'] = sepecification

    elif soup.find('table',id='productDetails_techSpec_section_1'):
        for item in soup.find('table',id='productDetails_techSpec_section_1').find_all('tr'):
            sepecification [item.find('th').text.strip()]= item.find('td').text.strip()
    else:
        
        # product_details
        if soup.find(id="productFactsExpanderContentUx"):
            sepecification = {
                                i.find(class_="a-row").text.strip() : i.find_all(class_="a-row")[1].text.strip() 
                                for i in soup.select("#productFactsExpanderContentUx .a-column.a-span5.a-spacing-top-small")
                            }

        # additional info
        # try:

        #     info_lst = [i.text.strip() for i in soup.find('h3',string=re.compile('Additional Information')).find_parent('div',id="productFactsExpander").find_all('div',class_="a-row") if 'See less' not in i.text.strip()]
        #     for i in range(0,len(info_lst),2):
        #         sepecification[info_lst[i]] = info_lst[i+1]
        # except:pass

    if sepecification:
        response_data['Specification'] = ' | '.join([f"{k} : {v}" for k,v in sepecification.items()])

    # about this item
    if soup.find(id="productFactsExpanderWrapper"):
        about_this_item = ' | '.join([i.text.strip() for i in soup.find('h3',string=re.compile('About this item')).find_parent('div',id="productFactsExpander").find_all('ul',class_="a-unordered-list a-vertical a-spacing-small")])
        response_data['About this item'] = about_this_item
    
    # Description
    response_data['Description']=''
    if soup.find(id="productDescription_fullView"):
        response_data['Description'] =clean_str(soup.find(id="productDescription_fullView").text.strip())
    elif soup.find('div',id="productDescription") and soup.find('div',id="productDescription").text.strip():
        response_data['Description'] = clean_str(soup.find('div',id="productDescription").text.replace('Description',''))
    try:
        response_data['Description'] = clean_str('|'.join([i.text.strip() for i in soup.find('h3',string=re.compile('Product Description')).next_siblings if i.text.strip()]).replace('\n','').strip())
    except:
        ...

    # Stock Count
    if soup.find(id="availabilityInsideBuyBox_feature_div"):
        in_stock_text = soup.find(id="availabilityInsideBuyBox_feature_div").text.strip()    
        if get_digit_groups(in_stock_text):
            in_stock = get_digit_groups(in_stock_text)[0]
        else:
            in_stock = 'Yes'
    else:
        in_stock = 'No'
    response_data['In Stock'] = in_stock

    # Seller Name
    seller_name = ''
    if soup.find('div',attrs={"tabular-attribute-name":"Sold by"},class_="tabular-buybox-text a-spacing-mini"):
        seller_name = soup.find('div',attrs={"tabular-attribute-name":"Sold by"},class_="tabular-buybox-text a-spacing-mini").text.strip()
    response_data['Seller Name'] = seller_name

    return response_data

async def fetch_product_details(session, url, total_retries=3):
    headers = {
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.9',
        'User-Agent': 'Amazon.com/28.11.2.100 (Android/12/M2101K6P)',
        'X-Requested-With': 'com.amazon.mShop.android.shopping',
        'Cookie': 'lc-acbin=en_IN; mobile-device-info=dpi:420.0|w:1080|h:2181; amzn-app-id=Amazon.com/28.11.2.100/18.0.392664.0; i18n-prefs=INR; lc-acbin=en_IN;'
    }
     
    retry_count = 0
    payload = {
        'key': PROXY_VENDOR,
        'headers': headers,
        'url': url,
        'method': 'get',
        'country_code': 'in'
    }

    while retry_count < total_retries:
        try:
            async with session.post('https://api.syphoon.com', json=payload) as response:
                return await response.text()
        except Exception as ex:
            retry_count += 1
            if retry_count >= total_retries:
                raise ex



def get_variations(soup):
    variations_info = {}
    if soup.find('script',attrs={'data-a-state':'{"key":"twister-plus-mobile-inline-twister-dim-val-list"}'}):
        avilable_variations = json.loads(soup.find('script',attrs={'data-a-state':'{"key":"twister-plus-mobile-inline-twister-dims-to-asin-list"}'}).text)
        
        if len(avilable_variations)<=1:
            return {}

        variation_values = json.loads(soup.find('script',attrs={'data-a-state':'{"key":"twister-plus-mobile-inline-twister-dim-val-list"}'}).text)

        variations_info['asins'] = avilable_variations
        variations_info['variants'] = variation_values
        variations_info['color_grouping'] = variation_values.get('color_name','')
        variations_info['current_selection'] = json.loads(soup.find('script',attrs={'data-a-state':'{"key":"twister-plus-mobile-inline-twister"}'}).text)  
        
        variations_key = json.loads(soup.find('script',attrs={'data-a-state':'{"key":"twister-plus-mobile-inline-twister-dim-list"}'}).text)

        variations_info['asin_mapping'] = create_asin_mapping(avilable_variations,variation_values,variations_key)
    
    return variations_info


def get_other_sellers(soup):
    sellers = []
    for seller in soup.select('#aod-offer-list .aod-other-offer-block'):
        seller_info = {
            'Price' : seller.select_one('.a-price .a-offscreen').text.replace('₹','').strip(),
            'Sold By' : clean_str(seller.select_one('#aod-offer-soldBy .a-col-right .a-size-small').text)
        }
        
        maybe_condition = seller.select_one('#aod-offer-heading')
        if maybe_condition:
            seller_info['Condition'] = clean_str(maybe_condition.text)
        
        if seller.select_one('#aod-offer-shipsFrom .a-color-base'):
            seller_info['Ships From'] = clean_str(seller.select_one('#aod-offer-shipsFrom .a-color-base').text)
      

        sellers.append(', '.join(f'{k} : {v}' for k,v in seller_info.items()))
        
    return ' | '.join(sellers)


async def save_html(filename, content):
    async with aiofiles.open(filename, 'w', encoding='utf-8') as f:
        await f.write(content)

async def load_html(filename):
    async with aiofiles.open(filename, 'r', encoding='utf-8') as f:
        return await f.read()

async def main(url, session):
    
    data = []
    req_asin = url.split('/dp/')[1].split('/')[0].split('?')[0]
    os.makedirs(req_asin, exist_ok=True)

    try:
        html = await load_html(f'{req_asin}/{req_asin}.html')
    except:
        html = await fetch_product_details(session, url+'?th=1&psc=1')
        print(html)
        await save_html(f'{req_asin}/{req_asin}.html', html)

    soup = BeautifulSoup(html, 'lxml')

    variation_info = get_variations(soup)
    async with aiofiles.open(f'{req_asin}/varints.json', 'w') as f:
        await f.write(json.dumps(variation_info, indent=4))

    response_data = parse_amazon_page(soup, url=url, variation_info=variation_info)

    if variation_info:
        data.append(response_data)
        print(variation_info['asin_mapping'].pop(req_asin))

        for asin in variation_info['asin_mapping']:
            try:
                product_url = 'https://www.amazon.in/dp/' + asin + '?th=1&psc=1'
                
                try:
                    html = await load_html(f'{req_asin}/{asin}.html')
                except:
                    html = await fetch_product_details(session, product_url)
                    await save_html(f'{req_asin}/{asin}.html', html)

                soup = BeautifulSoup(html, 'lxml')
                response_data = parse_amazon_page(soup, product_url, asin, variation_info)

                data.append(response_data)
            except:
                pass
    else:
        data = response_data

    async with aiofiles.open(f'{req_asin}/{req_asin}.json', 'w') as f:
        await f.write(json.dumps(data, indent=4))
    
    return data

async def main_wrapper(asins):
    async with ClientSession() as session:
        tasks = [main(f'https://www.amazon.in/dp/{asin}', session) for asin in asins]
        results = await asyncio.gather(*tasks)
        for result in results:
            print(result)

if __name__ == '__main__':
    # asins = ['B0C1NDB4B9', 'B0BPGSJM53', 'B0BSRSLJ77', 'B08D3PQ8Z6', 'B08R51FFSX', 'B08VGSPZFY', 'B09VDDMGX7']
    asins = [ 'B0BPGSJM53', 'B0BSRSLJ77']
    start_time = time.time()
    asyncio.run(main_wrapper(asins))
    print("--- %s seconds ---" % (time.time() - start_time))