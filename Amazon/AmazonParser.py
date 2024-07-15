from common import *

def get_reviews(review_url):
    
    review_req = send_req_syphoon(1, 'POST', review_url)

    reviews= 0
    
    if review_req.status_code != 200:
        return reviews
    review_html = review_req.text
    
    review_Soup = BeautifulSoup(review_html, 'lxml')
    try:
        reviews = review_Soup.find(attrs={"data-hook":"cr-filter-info-review-rating-count"}).text.split('ratings,')[1].split('with')[0].strip()
    except:pass

    return reviews
    
def get_variations(soup):
    variations_info = {}
    if soup.find('script',string=re.compile('dataToReturn')):
        varaition_text = search_text_between(soup.find('script',string=re.compile('dataToReturn')).text,'dataToReturn = ',';')
        if not varaition_text:
            return {}
        
        variations_detail = json.loads(varaition_text.replace(''',
                ]''',']').replace(',]',']'))
        
        if not variations_detail.get('dimensionValuesDisplayData',''):
            return {}
       
        avilable_variations = variations_detail['dimensionValuesDisplayData']

        if len(avilable_variations)<=1:
            return {}

        variations_info['asins'] = avilable_variations
        variations_info['variants'] = variations_detail['variationValues']
        variations_info['color_grouping'] = variations_detail['variationValues'].get('color_name','')
        variations_info['current_selection'] =' | '.join([ f'{variations_detail["variationDisplayLabels"][k]} : {v}' for k,v in variations_detail['selected_variations'].items()])
    
    return variations_info
    

def parse_amazon_page(url,domain,asin=None):

    details = {}


    details['asin'] = asin 
    details['url'] = url 

    try:
       
        req = send_req_syphoon(1, 'GET', url)
        req.raise_for_status()
        soup = BeautifulSoup(req.text, 'lxml')

    except Exception as ex:
        print(traceback.print_exc())
        return {'message':f'Error in sending request {url}'},{}

    # Product Name
    if soup.find(id='title'):
        details['product_name'] = soup.find(id='title').get_text().strip()
    else:
        return {'message':f'Product name not found {url}'},{}
    
    # Brand
    try:
        details['brand'] = soup.find(id="amznStoresBylineLogoTextContainer").get_text().split('\n')[0].split('Visit')[0].strip()
    except:
        details['brand'] = soup.find(id="bylineInfo").text.replace('Brand:','').replace('Visit','').replace('the','').replace('store','').replace('Store','').strip()

    # Images
    try:
        image_text = search_text_between(req.text,"'colorImages': ",""",
                'colorToAsin'""")
        if image_text:
            image_json = json.loads(image_text.replace("'initial'",'"initial"'))['initial']
            details['images'] = " | ".join([img['large'] for img in image_json])

    except:
        pass
    
    # Discount
    list_price = None
    if soup.find(class_='savingsPercentage'):
        details['discount_percentage']  = soup.find(class_="a-section a-spacing-none aok-align-center aok-relative").find(class_='savingsPercentage').text.replace('-','')
        details['promo_price']  = soup.find(class_="a-section a-spacing-none aok-align-center aok-relative").find('span',class_='priceToPay').text.replace('₹','').replace('$','').strip()
        list_price = soup.find(class_="basisPrice").find(class_='a-price a-text-price').find(class_='a-offscreen').text.replace('₹','').replace('$','').strip()
    elif soup.select_one('span.a-price.reinventPricePriceToPayMargin.priceToPay'):
        list_price = soup.select_one('span.a-price.reinventPricePriceToPayMargin.priceToPay').text.replace('₹','').replace('$','').strip()
    details['list_price'] = list_price


    # Variants    
    variation_info = get_variations(soup)
    if variation_info:
        details['variants'] = variation_info['variants']
        details['color_grouping'] = variation_info['color_grouping']
        details['current_selection'] = variation_info['current_selection']
           
    # Rating
    if soup.find(id="acrCustomerReviewLink"):
        details['rating'] = soup.find(id="acrCustomerReviewLink").span.text.replace('ratings','').strip()
        
    # Color of Variant
    if soup.find(id="variation_color_name"):
        details['color_variant']  = soup.find(id="variation_color_name").find('span',class_='selection').text.strip()
      
    # Specification

    if soup.find_all('div',id="productDetails_feature_div"):
        sepecification = {}

        for spec in soup.select('div#productDetails_feature_div div.a-column.a-span6'):
            if not spec.select('table'):continue
            if (spec.find('h1') and not spec.find(id="productDetails_feedback_sections")) or spec.find(id='productDetails_detailBullets_sections1'):
                header = spec.find('h1').text
                val = []
                for item in spec.find_all('tr'):
                    val.append(f"{item.find('th').text.strip()} : {item.find('td').text.strip()}")
                sepecification[header] =clean_str(' | '.join(val).strip())
            else:
                val = []
                for item in spec.find_all('tr'):
                    val.append(f"{item.find('th').text.strip()} : {item.find('td').text.strip()}")
                
                sepecification = clean_str(' | '.join(val).strip())
        details['specification'] = sepecification


    elif soup.find('table',id='productDetails_techSpec_section_1'):
        val = []
        for item in soup.find('table',id='productDetails_techSpec_section_1').find_all('tr'):
            val.append(f"{item.find('th').text.strip()} : {item.find('td').text.strip()}")
        details['specification'] = clean_str(' | '.join(val).strip())

    elif soup.select('div.a-column.a-span6.block-content.block-type-table tr'):
        val = []
        for item in soup.select('div.a-column.a-span6.block-content.block-type-table tr'):
            val.append(f"{item.find('td').text.strip()} : {item.find_all('td')[1].text.strip()}")
        details['specification'] = clean_str(' | '.join(val).strip())
   
    # product_details
    product_details = {}
    
    if soup.select('div#productOverview_feature_div'):
        for row in soup.select('div#productOverview_feature_div tr'):
            head ,val = row.find_all('td')
            product_details[head.text.strip()] = val.text.strip()

    if soup.find(id="productFactsDesktopExpander"):
        for row in soup.select('div#productFactsDesktopExpander div.product-facts-detail'):
            head ,val = row.find('div',class_='a-fixed-left-grid-col a-col-left').text.strip(),row.find('div',class_='a-fixed-left-grid-col a-col-right').text.strip()
            product_details[head] = val

    if soup.find(id="detailBullets_feature_div"):
        for row in soup.select('div#detailBullets_feature_div li span.a-list-item'):
            if row.find('span'):
                spans = row.find_all('span')
                head ,val = spans[0].text.strip(),spans[1].text.strip()
                product_details[head] = val

    details['product_details'] =clean_str(' | '.join([f"{i} : {product_details[i]}" for i in product_details]))


    # about this item
    
    if soup.find(id="productFactsDesktopExpander"):
        details['about_this_item'] = clean_str(' | '.join([i.text.strip() for i in soup.find('h3',string=re.compile('About this item')).find_next_siblings('ul',class_="a-unordered-list a-vertical a-spacing-small")]))
    elif soup.find(id="featurebullets_feature_div"):
        details['about_this_item'] =clean_str(' | '.join([i.text.strip() for i in soup.select('div#featurebullets_feature_div ul li')]))

    # additional info
    try:
        info_text = []
        for i in soup.find('h3',string=re.compile('Additional Information')).find_next_siblings('div',class_='a-fixed-left-grid product-facts-detail'):
            head ,val = i.find('div',class_='a-fixed-left-grid-col a-col-left').text.strip(),i.find('div',class_='a-fixed-left-grid-col a-col-right').text.strip()
            info_text.append(f"{head} : {val}")
        details['additional_info'] = clean_str(' | '.join(info_text))
       
    except:pass

    # Description
    details['description']=''
    if soup.find(id="productDescription"):
        details['description'] =clean_str(soup.find(id="productDescription").text.strip())
    
    elif soup.find('div',id="productDescription_feature_div"):
        details['description'] = clean_str(soup.find('div',id="productDescription_feature_div").text.replace('Description',''))
    
    else:
        try:
            details['description'] = clean_str('|'.join([i.text.strip() for i in soup.find('h2',string=re.compile('Product Description')).next_siblings if i.text.strip()]).replace('\n','').strip())
        except:
            pass

    # Stock Count
    if soup.find(id="availability"):
        in_stock_text = soup.find(id="availability").text.strip()    
        if get_digit_groups(in_stock_text):
            in_stock = get_digit_groups(in_stock_text)[0]
        else:
            in_stock = 'Yes'
    else:
        in_stock = 'No'
    details['in_stock'] = in_stock

    # Seller Name

    if soup.find('div',attrs={"tabular-attribute-name":"Sold by"},class_="tabular-buybox-text"):
        details['seller_name'] = soup.find('div',attrs={"tabular-attribute-name":"Sold by"},class_="tabular-buybox-text").text.strip()
       
    if soup.find(id="reviews-medley-footer"):
        review_url =f'https://www.{domain}'+soup.find(id="reviews-medley-footer").find('a',attrs={"data-hook":"see-all-reviews-link-foot"})['href']
        details['reviews'] = get_reviews(review_url)

    return details,variation_info


def amazon_parser(url,variation_info=False,limit=10):

    domain = get_domain_name(url)

    data = []

    req_asin = url.split('/dp/')[1].split('/')[0].split('?')[0]

    if '?' in url:
        url+='&th=1&psc=1'
    else:
        url += '?th=1&psc=1'

    resp_data ,variations = parse_amazon_page(url, domain, req_asin)
    if limit==-1:
        limit = len(variations['asins'])

    if variation_info and variations:

        data.append(resp_data)
        cnt = 1
        for asin in variations['asins']:
            try:
                url = f'https://{domain}/dp/{asin}/?th=1&psc=1'
                resp_data,_ = parse_amazon_page(url,domain,asin)
                data.append(resp_data)
                cnt+=1
            except Exception as e:
                print(e)
                print(url)
            
            if cnt == limit:
                break

    else:
        data = resp_data

    return data

if __name__=='__main__':
    print(amazon_parser('https://www.amazon.com/Photography-Autofocus-Vlogging-Anti-Shake-Batteries/dp/B0CZLHHKZM/ref=sr_1_8?dib=eyJ2IjoiMSJ9.sGppl5gZH5B0tzEduBJH1hAUUMJNobCjuUP8srB4KmHbAeKedRYeKWvUNFq8StbM5knKmWdXKfo-b38J_pSqVytY2rotxcuNppxmlsY8MLjES2x5DWp-XQ69khaYQSTOrtv9Dj24rOjArBdWNcW7tpQFx6D90wSoQ24uPpHyAZZQsWCWdRNiWiCVuitWfq5I8o_QwkT9n0oguCxSp9Ze775ta9Kj80WRxJS5iZAyAqE.fvyLc9Ahb35fvUUdIxs1OcJBlxPA5DwMxdD0UaHOMuw&dib_tag=se&keywords=Camera+%26&qid=1721029901&sr=8-8',False))
    # please remove unwanted file writing if it is not needed
    