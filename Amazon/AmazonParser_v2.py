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
            
            review['body'] = clean_str(review_soup.find('div',attrs={"data-hook":"review-collapsed"}).text)
            review['body_html']  =clean_str(review_soup.find('span',attrs={'data-hook':"review-body"}).prettify())

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
                    "raw" : clean_str(review_soup.find('span',attrs={'data-hook':"review-date"}).text),
                    "date" : datetime.strptime(review_soup.find('span',attrs={'data-hook':"review-date"}).text.split('on')[1].strip(),'%B %d, %Y').strftime('%Y-%m-%d')
                }
                review['review_country'] = review_soup.find('span',attrs={'data-hook':"review-date"}).text.split('Reviewed in')[1].split('on')[0].strip().strip('the ')
                
            if review_soup.find('div',attrs={"data-hook":"genome-widget"}):
                review['profile'] = {
                    'name':clean_str(review_soup.select_one("div[data-hook='genome-widget'] span.a-profile-name").text),
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
            product['price'] = item.select_one('span.a-price span.a-offscreen').text.strip()
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
            product['link'] = item.select_one('a.a-link-normal')['href']
            product['image'] = item.select_one('a img')['src']
            if item.select_one('span.a-price span.a-offscreen'):
                product['price'] = item.select_one('span.a-price span.a-offscreen').text.strip()
            if item.select_one('span.a-icon-alt'):
                product['rating']=item.select_one('span.a-icon-alt').text.split()[0]
                product['ratings_total'] = item.select_one('span.a-size-small').text.strip()
            products.append(product)
        except:
            ...

    return products

def get_shop_by_look(soup):
    products = []
    for item in soup.select('div.shopbylook-btf-items-section div.shopbylook-btf-item-box'):
        try:
            product = {}
            product['asin'] = unquote(item.select_one('a.sbl-image-link')['href']).split('/dp/')[1].split('/')[0]
            product['link'] = item.select_one('a.sbl-image-link')['href']
            product['title'] = item.select_one('a.sbl-image-link img')['alt']
            product['image'] = item.select_one('a.sbl-image-link img')['data-src']
            if item.select_one('div.sbl-item-rating span') and item.select_one('div.sbl-item-rating span').text.strip():
                product['rating'] = item.select_one('div.sbl-item-rating span').text.strip()
                product['ratings_total'] = item.select_one('div.sbl-item-rating span.sbl-review-count').text.strip()
            if item.select_one('div.sbl-item-price span[aria-hidden="true"]'):
                product['price'] = (item.select_one('div.sbl-item-price span[aria-hidden="true"] span.a-price-symbol').text + item.select_one('div.sbl-item-price span[aria-hidden="true"] span.a-price-whole').text +'.'+item.select_one('div.sbl-item-price span[aria-hidden="true"] span.a-price-fraction').text).replace(' ','').strip()
            products.append(product)
        except:
            ...

    if products:
        return {
            'products': products,
            'title': soup.select_one('#sbl-header-title').text.strip()
        }


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
            if soup.select_one('#corePriceDisplay_desktop_feature_div .savingsPercentage'):
                price_info['discount_percentage']  = soup.find(class_="a-section a-spacing-none aok-align-center aok-relative").find(class_='savingsPercentage').text.replace('-','')
                price_info['promo_price']  = soup.find(class_="a-section a-spacing-none aok-align-center aok-relative").find('span',class_='priceToPay').text.replace('₹','').replace('$','').strip()
                price_info['list_price'] = soup.find(class_="basisPrice").find(class_='a-price a-text-price').find(class_='a-offscreen').text.replace('₹','').replace('$','').strip()
            
            elif soup.select_one('span.a-price.reinventPricePriceToPayMargin.priceToPay') and soup.select_one('span.a-price.reinventPricePriceToPayMargin.priceToPay span.a-offscreen').text.strip():
                price_info['list_price'] = soup.select_one('span.a-price.reinventPricePriceToPayMargin.priceToPay span.a-offscreen').text.replace('₹','').replace('$','').strip()
            elif soup.select_one('div#corePriceDisplay_desktop_feature_div span.aok-offscreen'):
                price_info['list_price'] = soup.select_one('div#corePriceDisplay_desktop_feature_div span.aok-offscreen').text.replace('₹','').replace('$','').strip()

        elif soup.find(id="corePrice_desktop"):
            if soup.select('span.a-price.a-text-price.a-size-base[data-a-strike="true"] span.a-offscreen'):
                price_info['list_price'] = soup.select('span.a-price.a-text-price.a-size-base[data-a-strike="true"] span.a-offscreen')[0].text.replace('₹','').replace('$','').strip()
                price_info['promo_price']  = soup.select_one('span.a-price.a-text-price.a-size-medium.apexPriceToPay span.a-offscreen').text.replace('₹','').replace('$','').strip()
                price_info['discount_percentage']  = soup.select_one('td.a-span12.a-color-price.a-size-base span.a-color-price').text.split('(')[1].split(')')[0].strip()
            
            elif soup.select_one('span.a-price.a-text-price.a-size-medium.apexPriceToPay span.a-offscreen') and soup.select_one('span.a-price.a-text-price.a-size-medium.apexPriceToPay span.a-offscreen').text.strip():
                price_info['list_price'] = soup.select_one('span.a-price.a-text-price.a-size-medium.apexPriceToPay span.a-offscreen').text.replace('₹','').replace('$','').strip()
            elif soup.select_one('div#corePrice_desktop span.aok-offscreen'):
                price_info['list_price'] = soup.select_one('div#corePrice_desktop span.aok-offscreen').text.replace('₹','').replace('$','').strip()
        elif soup.find(id="gc-live-preview-amount"):
            price_info['list_price'] = soup.select_one('#gc-live-preview-amount').text.replace('₹','').replace('$','').strip()
    except:
        ...

    return price_info

def get_specifications(soup):

    sepecification = {}
    if soup.select('div#productDetails_feature_div div.a-column.a-span6'):
        for spec in soup.select('div#productDetails_feature_div div.a-column.a-span6'):
            sub_spec = {}
            if not spec.select('table tr'):continue
            if spec.select('table#productDetails_feedback_sections'):
                spec.select_one('table#productDetails_feedback_sections').extract()

            if spec.find('h1') and 'feedback' not in spec.find('h1').text.lower() and 'warranty' not in spec.find('h1').text.lower():
                header = spec.find('h1').text
                for item in spec.find_all('tr'):
                    sub_spec[clean_str(item.find('th').text)] = clean_str(item.find('td').text)
                sepecification[header] = sub_spec

            else:
                for item in spec.find_all('tr'):
                    sepecification[clean_str(item.find('th').text)] = clean_str(item.find('td').text)
    elif soup.select('#technicalSpecifications_feature_div tr'):
        for item in soup.select('#technicalSpecifications_feature_div tr'):
            try:
                sepecification[clean_str(item.find('th').text)] = clean_str(item.find('td').text)
            except:
                ...
    elif soup.select('#rich_product_information li'):
        for item in soup.select('#rich_product_information li'):
            try:
                sepecification[clean_str(item.select_one('div.rpi-attribute-label').text)] = clean_str(item.select_one('div.rpi-attribute-value').text)
            except:
                ...

    elif soup.find('table',id='productDetails_techSpec_section_1'):
        for item in soup.find('table',id='productDetails_techSpec_section_1').find_all('tr'):
            sepecification[clean_str(item.find('th').text)] = clean_str(item.find('td').text)
        
    elif soup.select('div.a-column.a-span6.block-content.block-type-table tr'):
        for item in soup.select('div.a-column.a-span6.block-content.block-type-table tr'):
            sepecification[clean_str(item.find('td').text)] = clean_str(item.find_all('td')[1].text)

    return sepecification


def get_product_details(soup):
    product_details = {}
    
    if soup.select('div#productOverview_feature_div'):
        for row in soup.select('div#productOverview_feature_div tr'):
            try:
                head ,val = row.find_all('td')
                product_details[clean_str(head.text.strip())] = clean_str(val.text.strip())
            except:...

    if soup.find(id="productFactsDesktopExpander"):
        for row in soup.select('div#productFactsDesktopExpander div.product-facts-detail'):
            try:
                head ,val = clean_str(row.find('div',class_='a-fixed-left-grid-col a-col-left').text),clean_str(row.find('div',class_='a-fixed-left-grid-col a-col-right').text)
                product_details[head] = val
            except:
                ...

    if soup.find(id="detailBullets_feature_div"):
        for row in soup.select('div#detailBullets_feature_div li span.a-list-item'):
            if row.find('span'):
                try:
                    spans = row.find_all('span')
                    head ,val = clean_str(spans[0].text.replace(':','')),clean_str(spans[1].text)
                    product_details[head] = val
                except:
                    ...

    if soup.select('div#glance_icons_div'):
        try:
            head = [clean_str(i.text) for i in soup.select('div#glance_icons_div span.a-size-base.handle-overflow.a-text-bold') if i.text]
            val = [clean_str(i.text) for i in soup.select('div#glance_icons_div span.a-size-base.handle-overflow.a-text-bold ~ span') if i.text]

            product_details = product_details | dict(zip(head,val))
        except:
            ...
        
    return product_details

def get_protection_plan(soup):
    plans = []
    for row in soup.select('div#mbb_feature_div  div.abbListItem'):
        try:
            plan = {}
            plan['asin'] = [inp for inp in row.select('input') if 'asin' in inp.get('name')][0]['value']
            plan['title'] = row.find(id='mbbPopoverLink').text
            plan['price'] = row.find('span',class_='a-color-price').text
            plans.append(plan)
        except:
           ...

    return plans

def get_bundles(soup):
    bundles = []
    for row in soup.select('#bundleV2_feature_div li'):
        try:
            bundle = {}
            bundle['asin'] = unquote(row.select_one('a.a-link-normal')['href']).split('/dp/')[1].split('/')[0]
            bundle['title'] = row.select_one('span.pba-lob-bundle-title span.a-truncate-full').text.strip()
            bundle['link'] = row.select_one('a.a-link-normal')['href']
            bundle['image'] = row.select_one('img.pba-lob-bundle-image')['src']

            if row.select('.pba-lob-review-stars'):
                bundle['rating'] = [rating for rating in row.select_one('.pba-lob-review-stars')['class'] if 'a-star-' in rating][0].replace('a-star-','').replace('-','.')

            if row.select('.pba-lob-review-count'):
                bundle['ratings_total'] = row.select_one('.pba-lob-review-count').text.strip()
            if row.select('span.pba-lob-bundle-stp-price span.a-offscreen'):
                bundle['list_price'] = row.select_one('span.pba-lob-bundle-stp-price span.a-offscreen').text.strip()

            if row.select('span.pba-lob-bundle-buy-price span.a-offscreen'):
                if bundle['list_price'] == '':
                    bundle['list_price'] = row.select_one('span.pba-lob-bundle-buy-price span.a-offscreen').text.strip()
                else:
                    bundle['promo_price'] = row.select_one('span.pba-lob-bundle-buy-price span.a-offscreen').text.strip()
            bundles.append(bundle)
        except:
           ...
    return bundles


def  get_bundle_contents(soup):
    bundle_contents = []
    for row in soup.select('div.bundle-components div.a-row'):
        try:
            bundle = {}
            bundle['asin'] =unquote(row.select_one('div.bundle-comp-title a')['href']).split('/dp/')[1].split('/')[0]
            bundle['title'] = row.select_one('div.bundle-comp-title a').text.strip()
            bundle['link'] = row.select_one('div.bundle-comp-title a')['href']
            bundle['image'] = row.select_one('img.a-thumbnail-right')['src']
            if row.select('.bundle-comp-bullets li'):
                bundle['feature_bullets'] = clean_str(' | '.join([i.text.strip() for i in row.select('.bundle-comp-bullets li')]))
            if row.select('.bundle-comp-reviews'):
                bundle['rating'] = [rating for rating in row.select_one('.bundle-comp-reviews .a-icon-star')['class'] if 'a-star-' in rating][0].replace('a-star-','').replace('-','.')
                bundle['ratings_total'] = row.select_one('.bundle-comp-reviews .bundle-comp-reviews-count').text.replace('(','').replace(')','').strip()
            bundle['price'] = row.select_one('.bundle-comp-price').text.strip()
            bundle_contents.append(bundle)
        except:
           ...

    return bundle_contents


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
        details['product_name'] =clean_str(soup.find(id='title').text)
    else:
        page_html = search_text_between(page_html,'<html class="a-no-js" data-19ax5a9jf="dingo">','</html>')
        if page_html:
            soup = BeautifulSoup(page_html, 'lxml')
            if soup.find(id='gc-asin-title'):
                details['product_name'] =clean_str(soup.find(id='gc-asin-title').text)
            else:
                return {'message':f'Product name not found {url}'}
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
        if soup.find('a',id="bylineInfo"):
            details['brand'] = soup.find(id="bylineInfo").text.replace('Brand:','').replace('Visit','').replace('the','').replace('store','').replace('Store','').strip()
            details['sub_title'] = {
                'text' : soup.find(id="bylineInfo").text,
                'url' : soup.find(id="bylineInfo")['href']
            }
        maybe_author =  soup.select('#bylineInfo span.author a')
        if maybe_author:
            authors = []
            for author in maybe_author:
                authors.append({
                'name':clean_str(author.text),
                'link':author['href']
                })
            if len(authors)>1:
                details['authors'] = authors
            else:
                details['author']  =authors[0]
    
    maybe_format = soup.select_one('#tmmSwatches .selected span.slot-title')
    if maybe_format:
        details['format'] = maybe_format.text.strip()
    elif soup.find('span',string=re.compile('Format:')):
        details['format'] = soup.find('span',string=re.compile('Format:')).find_next_sibling('span').text

    maybe_audio_sample = soup.select_one('div[data-audioid="audImgSample"]')
    if maybe_audio_sample:
        details['audio_sample'] = maybe_audio_sample.get('data-audiosource')

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

    additional_videos = get_additional_videos(soup)
    if additional_videos:
        details['addition_videos'] =additional_videos
    
    # coupon
    try:
        if soup.select('span.promoPriceBlockMessage span.a-color-success label'):
            details['has_coupon'] = True
            details['coupon_text'] = soup.select('span.promoPriceBlockMessage span.a-color-success label')[0].text.split('Shop items')[0].strip()
    except:
        details['has_coupon'] = False

    # amazons_choice
    if soup.select_one('div#acBadge_feature_div span.ac-for-text'):
        details['amazons_choice'] = clean_str(soup.select_one('div#acBadge_feature_div span.ac-for-text').text)

    # Rating
    if soup.find('span',attrs={"data-hook":"rating-out-of-text"}):
        details['rating'] = soup.find('span',attrs={"data-hook":"rating-out-of-text"}).text.split('out')[0].strip()
        
    # total ratings
    try:
        details['total_ratings'] = int(soup.find('span',id="acrCustomerReviewText").text.split('rating')[0].strip().replace(',',''))
        if soup.select('table#histogramTable tr'):
            rating_breakdown = []
            for row in soup.select('table#histogramTable tr'):
                tds = row.find_all('td')
                try:
                    if tds:
                        rating_breakdown.append({tds[0].a.text.strip() :{
                            'percentage' : tds[2].text.strip().replace('%',''),
                            'count' :round(details['total_ratings'] * (int(tds[2].text.strip().replace('%','')) / 100)) if int(tds[2].text.strip().replace('%','')) else 0
                        }})
                except:
                    ...
            details['rating_breakdown'] = rating_breakdown
        elif soup.select('ul#histogramTable'):
            rating_breakdown = []
            for row in soup.select('ul#histogramTable li'):
                try:
                    start= [element.strip() for element in row.find('div', class_='a-section a-spacing-none a-text-left aok-nowrap').contents if isinstance(element, str) and element.strip()][0]
                    percentage =  [element.strip() for element in row.find('div', class_='a-section a-spacing-none a-text-right aok-nowrap').contents if isinstance(element, str) and element.strip()][0].replace('%','')
                    if int(percentage) == 0:
                        count = 0
                    else:
                        count =round(details['total_ratings'] * (int(percentage) / 100))
                    
                    rating_breakdown.append({
                        start:{
                            'percentage' : percentage,
                            'count' : count
                        }
                    })
                except:
                    ...
            details['rating_breakdown'] = rating_breakdown
        
    except:
        ...
    
    # rating_breakdown
    
    
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

    
    # Variants    
    variation_info = get_variations(soup)
    if variation_info:
        details['variants'] = variation_info['variants']
        details['current_selection'] = variation_info['current_selection']
        details['variant_asins'] =','.join([asin for asin in variation_info['asins']])
    
    maybe_formats= soup.select('#mediamatrix_feature_div span.format  a')
    if maybe_formats:
        variants = []
        for format in maybe_formats:
            try:
                variants.append(format['href'].split('/dp/')[1].split('/')[0].split('?')[0])
            except:
                ... 
        if variants:
            details['variant_asins'] = ','.join(variants)

    # Color of Variant
    if soup.find(id="variation_color_name"):
        details['color_variant']  = soup.find(id="variation_color_name").find('span',class_='selection').text.strip()
      
    if soup.find(id="legal_feature_div"):
        if 'Proposition 65' in soup.find(id="legal_feature_div").text:
            details['proposition_65_warning'] = True

    # series
    maybe_series_text = search_text_between(page_html,'id="seriesBulletWidget_feature_div"','</div>')
    if maybe_series_text:
        maybe_series_soup = BeautifulSoup('<div'+maybe_series_text,'html.parser').find('a')
        if maybe_series_soup:
            details['series'] = {
                'index': clean_str(maybe_series_soup.text.split(':')[0]),
                'title': clean_str(maybe_series_soup.text),
                'link':maybe_series_soup['href'],
                'asin':maybe_series_soup['href'].split('/dp/')[1].split('/')[0].split('?')[0]

            }
    # Collectible info
    maybe_collectible_soup =soup.select("#collectiblesKeyInformation_feature_div tr")
    if maybe_collectible_soup:
        collectible_info = {}
        try:
            for row in maybe_collectible_soup:
                collectible_info[clean_str(row.find('th').text)] = clean_str(row.find('td').text)
        except:...
        details['collectible_info'] = collectible_info
    # product_details   
    
    product_details = get_product_details(soup)
    if product_details:
        details['product_details'] = product_details

    # additional Details

    if soup.find(id="provenance-certifications"):
        additadditional_details = []
        for item in soup.select('#provenance-certifications div.provenance-certifications-row-description'):
            try:
                additadditional_details.append({
                    'name':clean_str(item.find('div').text),
                    'value': clean_str(item.find('span',class_='a-truncate-full').text)
                      })
            except:...
        details['additional_details'] = additadditional_details

    # Specification
    specifications = get_specifications(soup)
    if specifications:
        details['specifications'] = specifications

    # has_360_view
    if soup.select('div#spin360_feature_div script'):
        details['has_360_view'] = True

    # is_bundle
    details['is_bundle'] = True if soup.find(id="bundle-v2-btf-contains-label") else False
    if details['is_bundle']:
        details['bundle_contents'] = get_bundle_contents(soup)

    #feature_bullets
    if soup.find(id="productFactsDesktopExpander"):
        details['feature_bullets'] = clean_str(' | '.join([i.text.strip() for i in soup.find('h3',string=re.compile('About this item')).find_next_siblings('ul',class_="a-unordered-list a-vertical a-spacing-small")]))
    elif soup.find(id="featurebullets_feature_div"):
        details['feature_bullets'] =clean_str(' | '.join([i.text.strip() for i in soup.select('div#featurebullets_feature_div ul li')]))
    
    if soup.find(id="variation_size_name"):
        if soup.find(id="variation_size_name").find('span',class_='selection'):
            details['size_variant'] = soup.find(id="variation_size_name").find('span',class_='selection').text.strip()
        elif soup.select_one('div#variation_size_name option[selected]'):
            details['size_variant'] = soup.select_one('div#variation_size_name option[selected]').text.strip()

    # ingredients
    if soup.find(id="nic-ingredients-content"):
        details['ingredients'] = clean_str(' | '.join([i.text.strip() for i in soup.find(id='nic-ingredients-content').children]))


    #important_information
    if soup.find(id="important-information"):
        if soup.select("div#important-information div.a-section.content span.a-text-bold"):
            imp_info = []
            for li in soup.select("div#important-information div.a-section.content"):
                header = li.select_one("span.a-text-bold").text.strip()
                vals = ','.join([item.text.strip() for item in li.select_one("span.a-text-bold").next_siblings if item.text.strip()])
                imp_info.append(f"{header} : {vals}")
            details['important_information'] = clean_str(' | '.join(imp_info))
        elif soup.select("div#important-information div.a-section.content h4"):
            imp_info = []
            for li in soup.select("div#important-information div.a-section.content"):
                header = li.select_one("h4").text.strip()
                vals = ','.join([item.text.strip() for item in li.select_one("h4").next_siblings if item.text.strip()])
                imp_info.append(f"{header} : {vals}")
            details['important_information'] = clean_str(' | '.join(imp_info))

        else:
            details['important_information'] = clean_str(soup.find(id="important-information").text.strip())
    
    #nutrition_summary
    if soup.find(id="nic-nutrition-summary-nutrient-content"):
        nutrition = []
        for tr in soup.select('table#nic-nutrition-summary-nutrient-content tr'):
            nutrition.append([val.text.strip() for val in tr.find_all('td')])
        details['nutrients'] = dict(zip(nutrition[1],nutrition[0]))

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

    # book_description
    if soup.select('#bookDescription_feature_div'):
        details['book_description'] = clean_str(soup.select_one('div[data-a-expander-name="book_description_expander"]').text)

    # aplus_content
    if soup.find(id="aplusBrandStory_feature_div"):
        maybe_brand_story_soup = soup.find(class_="apm-brand-story-carousel-container")
        if maybe_brand_story_soup:
            brand_story = {}
            if maybe_brand_story_soup.select('.apm-brand-story-logo-image img'):
                brand_story['brand_logo'] =  maybe_brand_story_soup.select_one('.apm-brand-story-logo-image img')['data-src']
            brand_story['hero_image'] =  maybe_brand_story_soup.select_one('.apm-brand-story-background-image img')['data-src']
            if maybe_brand_story_soup.select_one('.apm-brand-story-slogan-text'):
                brand_story['description'] = clean_str(' | '.join([brand_text.text for brand_text in maybe_brand_story_soup.select_one('.apm-brand-story-slogan-text').children if brand_text.text.strip()]))

            if maybe_brand_story_soup.select('img'):
                images = []
                for img in maybe_brand_story_soup.select('img'):
                    try:
                        images.append(img['data-src'])
                    except:
                        ...
                brand_story['images'] = images
            
            if maybe_brand_story_soup.select('.apm-brand-story-faq-block'):
                faqs  = []
                for faq in maybe_brand_story_soup.select('.apm-brand-story-faq-block'):
                    faqs.append({
                        'title':clean_str(faq.select_one('h4').text),
                        'body':clean_str(' | '.join([faq_text.text for faq_text in faq.select('p')]))
                    })
                brand_story['faqs'] = faqs

            if maybe_brand_story_soup.select('.apm-brand-story-image-cell a'):
                products = []
                for item in maybe_brand_story_soup.select('.apm-brand-story-image-cell a'):
                    try:
                        product = {}

                        product['asin'] = unquote(item['href']).split('/dp/')[1].split('/')[0]
                        product['title'] = item.select_one('img')['alt']
                        product['link'] = item['href']
                        product['image'] = item.select_one('img')['data-src']
                        products.append(product)
                    except:
                        ...
                brand_story['products'] = products

            details['aplus_content'] = brand_story

    details['price_info'] = get_price_info(soup)
    
    # Stock Count
    if soup.find(id="availability"):
        in_stock_text = soup.find(id="availability").text.strip()    
        if get_digit_groups(in_stock_text):
            in_stock = get_digit_groups(in_stock_text)[0]
        else:
            in_stock = 'Yes'
    elif soup.find(id="availability-string"):
        in_stock = 'Yes' if 'In Stock' in soup.find(id="availability-string").text.strip() else 'No'
    else:
        in_stock = 'No'
    details['in_stock'] = in_stock

    # subscribeAndSaveDiscountPercentage
    if soup.select_one('#snsDiscountPill  span.pillLightUp'):
        details['subscribeAndSaveDiscountPercentage'] = soup.select_one('#snsDiscountPill  span.pillLightUp').text.replace('%','').strip()
        details['subscribeAndSaveMaximumDiscountPrice'] = soup.select_one('#sns-tiered-price span.reinventPriceAccordionT2 span.a-offscreen').text.strip()

    if soup.select('#dealBadgeSupportingText'):
        details['deal_badge'] = soup.select('#dealBadgeSupportingText')[0].text.strip()

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
        details['best_seller_rank'] = clean_str(soup.find('th',string=re.compile('Best Sellers Rank')).find_next_sibling('td').text.strip())
    elif soup.find('span',string=re.compile('Best Sellers Rank')):
        details['best_seller_rank'] = clean_str(soup.find('span',string=re.compile('Best Sellers Rank')).parent.text.replace('Best Sellers Rank:','').strip())

    # is prime  
    details['is_prime'] = True if soup.select('.prime-details') else False
    details['is_new'] = False if 'Renewed' in details['product_name'] or 'Refurbished' in details['product_name'] else True
    try:
        details['brand_store'] ={
            'id' : details['sub_title']['url'].split('/page/')[-1].split('?')[0],
            'url': details['sub_title']['url']
        }
    except:
        ...

    if soup.find(id="whatsInTheBoxDeck"):
        details['whats_in_the_box'] = ' | '.join(li.text.strip() for li in soup.find(id="whatsInTheBoxDeck").find_all('li'))


    # Product guides and documents
    if soup.select("#productDocuments_feature_div a"):
        details['product_guides_and_documents'] = [
            {
                'title' : doc.text.strip(),
                'link' : doc['href']
            }
            for doc in soup.select('#productDocuments_feature_div a')
        ]
    # bundles
    bundles = get_bundles(soup)
    if bundles:
        details['bundles'] = bundles

    # newer model
    maybe_new_model_soup = soup.find(id="newer-version")
    if maybe_new_model_soup:
        details['newer_model'] = {}
        details['newer_model']['asin'] = unquote(maybe_new_model_soup.select_one('a.a-link-normal')['href']).split('/dp/')[-1].split('/')[0]
        details['newer_model']['title'] = maybe_new_model_soup.select_one('a.a-link-normal.a-size-base').text.strip()
        details['newer_model']['link'] = maybe_new_model_soup.select_one('a.a-link-normal.a-size-base')['href']
        details['newer_model']['image'] = maybe_new_model_soup.select_one('a img')['src']
        if maybe_new_model_soup.select_one('span.a-color-price'):
            details['newer_model']['price'] = maybe_new_model_soup.select_one('span.a-color-price').text.strip()
        if maybe_new_model_soup.select_one('a.reviewsLink i'):
            details['newer_model']['rating'] = [rating for rating in maybe_new_model_soup.select_one('a.reviewsLink i')['class'] if 'a-star-' in rating][0].replace('a-star-','').replace('-','.')
            details['newer_model']['ratings_total'] = maybe_new_model_soup.select_one('div#newer-version a.reviewsLink ~ a').text.replace('(','').replace(')','').strip()

    # Frequently bought together
    frequently_bought_together = get_frequently_bought_together(soup)

    if frequently_bought_together:
        details['frequently_bought_together'] = frequently_bought_together
    
    # similar_to_consider

    maybe_similar_to_consider_soup = soup.find(id="value-pick-ac")
    if maybe_similar_to_consider_soup:
        details['similar_to_consider'] = {}
        details['similar_to_consider'] = {}
        details['similar_to_consider']['asin'] = unquote(maybe_similar_to_consider_soup.select_one('a.a-link-normal')['href']).split('/dp/')[-1].split('/')[0]
        details['similar_to_consider']['title'] = maybe_similar_to_consider_soup.select_one('a.a-link-normal.a-size-base').text.strip()
        details['similar_to_consider']['link'] = maybe_similar_to_consider_soup.select_one('a.a-link-normal.a-size-base')['href']
        details['similar_to_consider']['image'] = maybe_similar_to_consider_soup.select_one('a img')['src']
        if maybe_similar_to_consider_soup.select_one('span.a-color-price'):
            details['similar_to_consider']['price'] = maybe_similar_to_consider_soup.select_one('span.a-color-price').text.strip()
        if maybe_similar_to_consider_soup.select_one('i.a-icon-star.a-icon'):
            details['similar_to_consider']['rating'] = [rating for rating in maybe_similar_to_consider_soup.select_one('i.a-icon-star.a-icon')['class'] if 'a-star-' in rating][0].replace('a-star-','').replace('-','.')
            details['similar_to_consider']['ratings_total'] = maybe_similar_to_consider_soup.select_one('i.a-icon-star.a-icon ~ a').text.replace('(','').replace(')','').strip()

    # shop_by_look
    shop_by_look = get_shop_by_look(soup)
    if shop_by_look:
        details['shop_by_look'] = shop_by_look
        
    # Also bought
    also_bought = get_also_bought(soup,'div#sims-consolidated-2_feature_div li') or get_also_bought(soup,'div#sp_detail_thematic-highly_rated li') or get_also_bought(soup,'div#similarities_feature_div li')

    if also_bought:
        details['also_bought'] = also_bought

    # related to this item
    releted_product = get_also_bought(soup,'div#anonCarousel2 li') or get_also_bought(soup,'div#sp_detail2 li')
    if releted_product:
        details['releted_product'] = releted_product

    # Top reviews
    top_reviews = get_top_reviews(soup,domain)
    if top_reviews:
        details['top_reviews'] = top_reviews

    return details
