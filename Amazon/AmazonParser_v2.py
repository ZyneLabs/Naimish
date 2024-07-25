from common import *
from urllib.parse import unquote

def get_top_reviews(soup,domain):
    reviews = []
    for review_soup in soup.select('div[data-hook="review"].a-section.review.aok-relative'):
        try:
            review = {}
            review['id'] = review_soup['id']

            if review_soup.find('a',attrs={"data-hook":"review-title"}):
                review['title'] = review_soup.find('a',attrs={"data-hook":"review-title"}).find('span',class_=False).text.strip()
            else:
                review['title'] = review_soup.find('span',attrs={"data-hook":"review-title"}).text.strip()
            
            review['body'] = review_soup.find('div',attrs={"data-hook":"review-collapsed"}).text.strip()
            review['body_html']  = review_soup.find('span',attrs={'data-hook':"review-body"}).prettify()

            if review_soup.find('a',attrs={"data-hook":"review-title"}):
                review['link'] ='https://'+domain+review_soup.find('a',attrs={"data-hook":"review-title"})['href']
            
            if review_soup.find('i',attrs={'data-hook':"review-star-rating"}):
                review['rating'] = review_soup.find('i',attrs={'data-hook':"review-star-rating"}).text.split('out')[0].strip()
            else:
                review['rating'] = review_soup.find('i',attrs={'data-hook':"cmps-review-star-rating"}).text.split('out')[0].strip()

            if review_soup.find('span',attrs={'data-hook':"helpful-vote-statement"}):
                review['helpful_votes'] = review_soup.find('span',attrs={'data-hook':"helpful-vote-statement"}).text.split()[0]
            
            if review_soup.find('span',attrs={'data-hook':"review-date"}):
                review['date'] ={
                    "raw" : review_soup.find('span',attrs={'data-hook':"review-date"}).text.strip(),
                    "date" : datetime.strptime(review_soup.find('span',attrs={'data-hook':"review-date"}).text.split('on')[1].strip(),'%B %d, %Y').strftime('%Y-%m-%d')
                }
                review['review_country'] = review_soup.find('span',attrs={'data-hook':"review-date"}).text.split('Reviewed in')[1].split('on')[0].strip().strip('the ')
                
            if review_soup.find('div',attrs={"data-hook":"genome-widget"}):
                review['profile'] = {
                    'name':review_soup.select_one("div[data-hook='genome-widget'] span.a-profile-name").text.strip(),
                }
                if review_soup.select_one("div[data-hook='genome-widget'] a.a-profile"):
                    review['profile']['link'] = 'https://'+domain+review_soup.select_one("div[data-hook='genome-widget'] a.a-profile")['href']
                    review['profile']['id'] = review_soup.select_one("div[data-hook='genome-widget'] a.a-profile")['href'].split('amzn1.account.')[1].split('/')[0]
            
            images = search_text_between(str(soup),'imagePopoverController.initImagePopover("'+review["id"]+'", "[', ']", data)')
        
            if images:
                review['images'] = [
                    {'link':img}
                    for img in images.split(',')
                ]

            review['verified_purchase'] = True if review_soup.select_one('div.a-row.a-spacing-mini.review-data.review-format-strip a') else False
            review['is_global_review']  = True if review_soup.find_parent('div',class_='global-reviews-content') else False
            reviews.append(review)
        except Exception as e:
            ...

    return reviews

def get_additional_videos(soup):
    videos = []
    for li in soup.select('div#vse-vw-dp-vse-related-videos li'):
        try:
            video_soup = li.find('div')
            video_details = {}
            video_details['id'] = video_soup['data-csa-c-item-id']
            video_details['product_asin'] = video_soup['data-product-asin']
            video_details['parent_asin'] = video_soup['data-parent-asin']
            video_details['related_products'] = video_soup['data-related-products-asins']
            video_details['title'] = video_soup['data-title']
            video_details['profile_image_url'] = video_soup['data-profile-image-url']
            video_details['profile_link'] = video_soup['data-profile-link']
            video_details['public_name'] = video_soup['data-public-name']
            video_details['creator_type'] = video_soup['data-creator-type']
            video_details['vendor_code'] = video_soup['data-vendor-code']
            video_details['vendor_name'] = video_soup['data-vendor-name']
            video_details['vendor_tracking_id'] = video_soup['data-vendor-tracking-id']
            video_details['video_image_id'] = video_soup['data-video-image-physical-id']
            video_details['video_image_url'] = video_soup['data-video-image-url']
            video_details['video_image_url_unchanged'] = video_soup['data-video-image-url-unchanged']
            video_details['video_image_width'] = video_soup['data-video-image-width']
            video_details['video_image_height'] = video_soup['data-video-image-height']
            video_details['video_image_extension'] = video_soup['data-video-image-extension']
            video_details['video_url'] = video_soup['data-video-url']
            video_details['video_previews'] = video_soup['data-video-previews']
            video_details['video_mime_type'] = video_soup['data-video-mime-type']
            video_details['duration'] = video_soup['data-formatted-duration']
            video_details['closed_captions'] = video_soup['data-closed-captions']
            videos.append(video_details)
        except:pass
    return videos

def get_frequently_bought_together(soup):
    products = []
    for item in soup.select('div#similarities_feature_div div.cardRoot.bucket div.a-cardui div.a-cardui div.a-cardui'):
        try:
            if item.find('span',class_='a-size-base a-text-bold'):continue
            product = {}
            
            product['asin'] = unquote(item.select_one('div.a-cardui div.a-section.a-spacing-none a')['href']).split('/dp/')[1].split('/')[0]
            product['title'] = item.select('div.a-cardui div.a-section.a-spacing-none a')[1].text
            product['link'] = item.select_one('div.a-cardui div.a-section.a-spacing-none a')['href']
            product['image'] = item.select_one('div.a-cardui div.a-section.a-spacing-none a img')['src']
            product['price'] = item.select_one('span.a-price span.a-offscreen').text.replace('$','')
            products.append(product)
        except:
            ...
    if products:
        try:
            maybe_price_bucket = soup.select_one('div#similarities_feature_div div.cardRoot.bucket')
            if maybe_price_bucket:
                total_products = ''.join([str(c) for c in range(1,int(maybe_price_bucket['data-count'].replace(',',''))+1)])
                return {
                    'total_price': json.loads(soup.select_one('div#similarities_feature_div div.cardRoot.bucket')['data-price-totals'])[total_products],
                    'products': products
                }
        except:
            ...

    return products

def get_also_bought(soup,selector):
    products = []
    for item in soup.select(selector):
        try:
            product = {}
            product['asin'] = unquote(item.select_one('a.a-link-normal')['href']).split('/dp/')[1].split('/')[0]
            product['title'] = item.select_one('a.a-link-normal div[aria-hidden="true"]').text.strip()
            product['link'] = item.select_one('a')['href']
            product['image'] = item.select_one('a img')['src']
            product['price'] = item.select_one('span.a-price span.a-offscreen').text.replace('$','')
            if item.select_one('span.a-icon-alt'):
                product['rating']=item.select_one('span.a-icon-alt').text.split()[0]
                product['ratings_total'] = item.select_one('span.a-size-small').text.strip()
            products.append(product)
        except:
            ...

    return products

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

def get_price_info(soup):
    price_info = {}
    try:
        if soup.find(id="corePriceDisplay_desktop_feature_div"):
            if soup.find(class_='savingsPercentage'):
                price_info['discount_percentage']  = soup.find(class_="a-section a-spacing-none aok-align-center aok-relative").find(class_='savingsPercentage').text.replace('-','')
                price_info['promo_price']  = soup.find(class_="a-section a-spacing-none aok-align-center aok-relative").find('span',class_='priceToPay').text.replace('₹','').replace('$','').strip()
                price_info['list_price'] = soup.find(class_="basisPrice").find(class_='a-price a-text-price').find(class_='a-offscreen').text.replace('₹','').replace('$','').strip()
            
            elif soup.select_one('span.a-price.reinventPricePriceToPayMargin.priceToPay'):
                price_info['list_price'] = soup.select_one('span.a-price.reinventPricePriceToPayMargin.priceToPay').text.replace('₹','').replace('$','').strip()

        elif soup.find(id="corePrice_desktop"):
            if soup.select('span.a-price.a-text-price.a-size-base[data-a-strike="true"] span.a-offscreen'):
                price_info['list_price'] = soup.select('span.a-price.a-text-price.a-size-base[data-a-strike="true"] span.a-offscreen')[0].text.replace('₹','').replace('$','').strip()
                price_info['promo_price']  = soup.select_one('span.a-price.a-text-price.a-size-medium.apexPriceToPay span.a-offscreen').text.replace('₹','').replace('$','').strip()
                price_info['discount_percentage']  = soup.select_one('td.a-span12.a-color-price.a-size-base span.a-color-price').text.split('(')[1].split(')')[0].strip()
            
            else:
                price_info['list_price'] = soup.select_one('span.a-price.a-text-price.a-size-medium.apexPriceToPay span.a-offscreen').text.replace('₹','').replace('$','').strip()
    except:
        ...

    return price_info

def get_specifications(soup):
    sepecification = ''
    if soup.select('div#productDetails_feature_div div.a-column.a-span6'):
        sepecification = {}
       
        for spec in soup.select('div#productDetails_feature_div div.a-column.a-span6'):
            if not spec.select('table') or spec.select('table#productDetails_feedback_sections'):continue
            if spec.find('h1') and 'Feedback' not in spec.find('h1').text and 'Warranty' not in spec.find('h1').text:
                header = spec.find('h1').text
                print(header)
                val = []
                for item in spec.find_all('tr'):
                    val.append(f"{item.find('th').text.strip()} : {item.find('td').text.strip()}")
                sepecification[header] =clean_str(' | '.join(val).strip())
            
            else:
                val = []
                for item in spec.find_all('tr'):
                    val.append(f"{item.find('th').text.strip()} : {item.find('td').text.strip()}")

                sepecification = clean_str(' | '.join(val).strip())
        
       


    elif soup.find('table',id='productDetails_techSpec_section_1'):
        val = []
        for item in soup.find('table',id='productDetails_techSpec_section_1').find_all('tr'):
            val.append(f"{item.find('th').text.strip()} : {item.find('td').text.strip()}")
        sepecification = clean_str(' | '.join(val).strip())
   
    elif soup.select('div.a-column.a-span6.block-content.block-type-table tr'):
        val = []
        for item in soup.select('div.a-column.a-span6.block-content.block-type-table tr'):
            val.append(f"{item.find('td').text.strip()} : {item.find_all('td')[1].text.strip()}")
        sepecification = clean_str(' | '.join(val).strip())
    
    return sepecification


def get_product_details(soup):
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

    return clean_str(' | '.join([f"{i} : {product_details[i]}" for i in product_details])).replace(' :  : ',' : ')

def get_protection_plan(soup):
    plans = []
    cnt=1
    for row in soup.select('div#abbWrapper  div.abbListItem'):
        try:
            plan = {}
            plan['asin'] = row.select_one(f'input[name="asin.{cnt}"]')['value']
            plan['title'] = row.find(id='mbbPopoverLink').text
            plan['price'] = row.find('span',class_='a-color-price').text
            plans.append(plan)
        except:
           ...

        cnt+=1
    return plans

def amazon_parser(url,domain,page_html,asin=None):

    details = {}

    details['asin'] = asin 
    details['url'] = url 

    parent_asin = search_text_between(page_html,'data-parent-asin="','"')
    if parent_asin:
        details['parent_asin'] = parent_asin

    soup = BeautifulSoup(page_html, 'lxml')
    
    maybe_search_alias = soup.select_one('form#nav-search-bar-form option[selected]')
    if maybe_search_alias:
        details['search_alias'] = {
            'text' : maybe_search_alias.text.strip(),
            'value' : maybe_search_alias['value'].split('=')[1]
        }
    # Product Name
    if soup.find(id='title'):
        details['product_name'] = soup.find(id='title').get_text().strip()
    else:
        return {'message':f'Product name not found {url}'}
    
    # Brand
    try:
        details['brand'] = soup.find(id="amznStoresBylineLogoTextContainer").get_text().split('\n')[0].split('Visit')[0].strip()
        details['sub_title'] = {
            'text' : soup.find(id="amznStoresBylineLogoTextContainer").get_text().replace('\n',''),
            'url' : soup.find(id="amznStoresBylineLogoTextContainer").find('a')['href']
        }
    except:
        details['brand'] = soup.find(id="bylineInfo").text.replace('Brand:','').replace('Visit','').replace('the','').replace('store','').replace('Store','').strip()
        details['sub_title'] = {
            'text' : soup.find(id="bylineInfo").text,
            'url' : soup.find(id="bylineInfo")['href']
        }

    # protection_plans 
    protections = get_protection_plan(soup)
    if protections:
        details['protection_plans'] = protections

    # main_image
    try:
        details['main_image'] = soup.find(id="landingImage").get('src')
    except:
        ...
    
    # Images
    try:
        image_text = search_text_between(page_html,"'colorImages': ","""'colorToAsin'""")
        if image_text:
            image_text = image_text.replace("'initial'",'"initial"').strip().strip(',')
            image_json = json.loads(image_text)['initial']
            details['images'] = [
                {'link':img['hiRes'] or img['large'],'variant':img['variant']} 
                for img in image_json]

            details['images_flat'] = ' | '.join([img['link'] for img in details['images']])
            details['image_count'] = len(details['images'])
    except Exception as e:
        ...

    # videos 
    try:
        video_text = search_text_between(page_html,"var obj = A.$.parseJSON('","');")
        if video_text:
            video_json = json.loads(video_text)
            details['videos'] = [
                {'duration_seconds':video['durationSeconds'],
                'width':video['videoWidth'],
                'height':video['videoHeight'],
                'link':video['url'],
                'thumbnail':video['thumb'],
                'is_hero_video':video['isHeroVideo'],
                'variant':video['variant'],
                'group_type':video['groupType'],
                'title':video['title']
                }
            for video in video_json['videos']
            ]
            details['video_count'] = len(details['videos'])
            details['videos_flat'] = ' | '.join([video['url'] for video in video_json['videos']])
    except Exception as e:
        ...

    
    details['addition_videos'] = get_additional_videos(soup)
    
    # coupon
    try:
        if soup.select('span.promoPriceBlockMessage span.a-color-success label'):
            details['has_coupon'] = True
            details['coupon_text'] = soup.select('span.promoPriceBlockMessage span.a-color-success label')[0].text.split('Shop items')[0].strip()
    except:
        details['has_coupon'] = False

    # total ratings
    try:
        details['total_ratings'] = int(soup.find('span',id="acrCustomerReviewText").text.split('ratings')[0].strip().replace(',',''))
    except:
        ...
    
    # rating_breakdown
    try:
        rating_breakdown = []
        for row in soup.select('table#histogramTable tr'):
            tds = row.find_all('td')
            if tds:
                rating_breakdown.append({tds[0].a.text.strip() :{
                    'percentage' : tds[2].text.strip().replace('%',''),
                    'count' :round(details['total_ratings'] * (int(tds[2].text.strip().replace('%','')) / 100))
                }})

        details['rating_breakdown'] = rating_breakdown
    except Exception as ex:
        ...

    # MarketPlace ID
    try:
        details['marketplace_id'] = soup.find(attrs={"data-asin": asin, "data-marketplace": True})['data-marketplace']
    except:
        ...

    # categories
    if soup.find(id='wayfinding-breadcrumbs_feature_div'):
        details['categories'] = [
            {'name':c.text.strip(),
            'url':f'https://{domain}{c["href"]}',
            'category_id':c['href'].split('node=')[1].split('&')[0]
            }

            for c in soup.find(id='wayfinding-breadcrumbs_feature_div').find_all('a') if c.text.strip()
            ]
        details['categories_flat'] = " > ".join([c['name'] for c in details['categories']])

    details['price_info'] = get_price_info(soup)
    
    # Variants    
    variation_info = get_variations(soup)
    if variation_info:
        details['variants'] = variation_info['variants']
        details['color_grouping'] = variation_info['color_grouping']
        details['current_selection'] = variation_info['current_selection']
        details['variant_asins'] =','.join([asin for asin in variation_info['asins']])

    # Rating
    if soup.find('span',attrs={"data-hook":"rating-out-of-text"}):
        details['rating'] = soup.find('span',attrs={"data-hook":"rating-out-of-text"}).text.split('out')[0].strip()
        
    # Color of Variant
    if soup.find(id="variation_color_name"):
        details['color_variant']  = soup.find(id="variation_color_name").find('span',class_='selection').text.strip()
      
    if soup.find(id="legal_feature_div"):
        if 'Proposition 65' in soup.find(id="legal_feature_div").text:
            details['proposition_65_warning'] = True
    
    # Specification
    specifications = get_specifications(soup)
    if specifications:
        details['specifications'] = specifications

    # product_details
    
    product_details = get_product_details(soup)
    if product_details:
        details['product_details'] = product_details

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

    if soup.find(id="mir-layout-DELIVERY_BLOCK-slot-PRIMARY_DELIVERY_MESSAGE_LARGE"):
        delivery_soup =soup.find(id="mir-layout-DELIVERY_BLOCK-slot-PRIMARY_DELIVERY_MESSAGE_LARGE").find('span')

        details['standard_delivery'] = {
        'name' : delivery_soup['data-csa-c-delivery-price'],
        'date' : delivery_soup['data-csa-c-delivery-time']
            }
        
    if soup.find(attrs={'data-csa-c-delivery-price':"fastest"}):
        if 'Order within' in soup.find(attrs={'data-csa-c-delivery-price':"fastest"}).text.strip():
            details['fastest_delivery'] = {
            'name' : soup.find(attrs={'data-csa-c-delivery-price':"fastest"}).text.strip(),
            'date' : soup.find(attrs={'data-csa-c-delivery-price':"fastest"})['data-csa-c-delivery-time']
                }
            
    # Seller Name
    details['is_sold_by_amazon'] = False
    if soup.find('div',attrs={"tabular-attribute-name":"Sold by"},class_="tabular-buybox-text"):
        details['seller_info'] = {'name' :  soup.find('div',attrs={"tabular-attribute-name":"Sold by"},class_="tabular-buybox-text").text.strip()}
       
        if soup.find('a'):
            details['seller_info']['link'] = soup.find('a')['href']
            details['seller_info']['id'] = soup.find('a')['href'].split('seller=')[-1].split('&')[0]
    
    elif soup.find(id="sellerProfileTriggerId"):
        details['seller_info'] = {'name' :soup.find(id="sellerProfileTriggerId").text.strip()}
        if soup.find(id="sellerProfileTriggerId").get('href',''):
            details['seller_info']['link'] = soup.find(id="sellerProfileTriggerId").get('href')
            details['seller_info']['id'] = soup.find(id="sellerProfileTriggerId").get('href').split('seller=')[-1].split('&')[0]
    else:
        details['is_sold_by_amazon'] = True

    # Best Sellers Rank
    if soup.find('th',string=re.compile('Best Sellers Rank')):
        details['best_seller_rank'] = soup.find('th',string=re.compile('Best Sellers Rank')).find_next_sibling('td').text.strip()
    elif soup.find('span',string=re.compile('Best Sellers Rank')):
        details['best_seller_rank'] = soup.find('span',string=re.compile('Best Sellers Rank')).parent.text.replace('Best Sellers Rank:','').strip()

    # is prime  
    details['is_prime'] = True if soup.select('.prime-details') else False
    details['is_new'] = False if 'Renewed' in details['product_name'] or 'Refurbished' in details['product_name'] else True

    if soup.find(id="whatsInTheBoxDeck"):
        details['whats_in_the_box'] = ' | '.join(li.text.strip() for li in soup.find(id="whatsInTheBoxDeck").find_all('li'))

    # Top reviews
    top_reviews = get_top_reviews(soup,domain)
    if top_reviews:
        details['top_reviews'] = top_reviews

    # Frequently bought together
    frequently_bought_together = get_frequently_bought_together(soup)

    if frequently_bought_together:
        details['frequently_bought_together'] = frequently_bought_together
    
    # Also bought
    also_bought = get_also_bought(soup,'div#sims-consolidated-2_feature_div li')

    if also_bought:
        details['also_bought'] = also_bought

    # related to this item
    releted_product = get_also_bought(soup,'div#anonCarousel2 li')
    if releted_product:
        details['releted_product'] = releted_product

    return details
