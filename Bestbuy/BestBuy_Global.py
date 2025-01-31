import json
import re
import requests
import traceback
from bs4 import BeautifulSoup as bs
import os
import requests

API_KEY = os.getenv('API_KEY')
class MokeRequest:

    def __init__(self,status_code,text):
        self.status_code = status_code
        self.text = json.dumps(text)

    def json(self):
        return json.loads(self.text)
       

def clean_str(input_str, sep="|"):
    if input_str is None:
        return ""

    if type(input_str) is not str:
        return input_str

    input_str = re.sub(r"\s+", " ", input_str).replace("\n", sep).replace("\u200e", '').replace('\u200f','')

    return input_str.strip()

def search_text_between(text, start, end):
    pattern = re.compile(f'{re.escape(start)}(.*?){re.escape(end)}', re.DOTALL)
    match = re.search(pattern, text)
    if match:
        return match.group(1)
    else:
        return None

def bestbuy_scraper(product_url,zipcode='',max_try=3):
    while max_try:
        try:
            headers = {
                'accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7',
                'accept-language': 'en-GB,en-US;q=0.9,en;q=0.8',
                'cache-control': 'max-age=0',
                'cookie': 'intl_splash=false;locStoreId=1028;locDestZip=10001;',
                'priority': 'u=0, i',
                'referer': 'https://www.bestbuy.com/',
                'sec-ch-ua': '"Not/A)Brand";v="8", "Chromium";v="126", "Google Chrome";v="126"',
                'sec-ch-ua-mobile': '?0',
                'sec-ch-ua-platform': '"Linux"',
                'sec-fetch-dest': 'document',
                'sec-fetch-mode': 'navigate',
                'sec-fetch-site': 'same-origin',
                'sec-fetch-user': '?1',
                'upgrade-insecure-requests': '1',
                'user-agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36',
            }
            payload = {
                "key": API_KEY,
                "url": product_url,
                "method": "GET",
            }
            if zipcode:
                payload['zipcode'] = zipcode

            req = requests.post(
                "https://api.syphoon.com", json=payload, headers=headers,
            )
            req.raise_for_status()
        
            return req
        except requests.exceptions.RequestException:
            max_try -= 1

        except Exception as e:
            req = MokeRequest(400,{"message":"This request will not charge you"})

    return req


def bestbuy_parser(product_url, html, offers=None, delivery=None, pickup=None, delivery_text=None, pickup_texts=None):
    '''
    This function will parse the html of the product page and return the details of the product
    
    Args:
    product_url (str): The url of the product page
    html (str): The html of the product page

    if custome solution is used as base request then the following arguments are required
    offers (str): The html of the offers section
    delivery (str): The html of the delivery section    
    pickup (str): The html of the pickup section
    delivery_text (str): The html of the delivery text section
    pickup_texts (list): The html of the pickup text section
    
    Returns:
    dict: The details of the product

    '''
    soup = bs(html,'html.parser')
    
    for a in soup.select('a[href]'):
        if not a['href'].startswith('http'):
            a['href'] = 'https://www.bestbuy.com'+a['href']

    details = {}

    details['url'] = product_url

    product_name_soup = soup.select_one('.sku-title h1')
    if not product_name_soup:
        return {'error':'Product name not found please check product url'}
    
    details['product_name'] = product_name_soup.text.strip()

    maybe_brand= soup.select_one('.shop-product-title a')
    if maybe_brand:
        details['brand_info'] = {
            'name':maybe_brand.text.strip(),
            'link':maybe_brand['href']
        }
    try:
        product_schema = json.loads(soup.select_one('script#product-schema').text)
    except:
        product_schema = {}

    if product_schema and product_schema.get('gtin13'):
        details['gtin13'] = product_schema['gtin13']

    if model_soup :=soup.select_one('.model.product-data span.product-data-value'):
        details['model_number'] = model_soup.text.strip()
    details['sku'] = soup.select_one('.sku.product-data span.product-data-value').text.strip()
    
    try:
        media_json = json.loads(soup.find('script',id=re.compile('shop-media-gallery-')).text)['baseContent']['media']
        
        details['images'] =[media['src'] for media in media_json['product-images']['sources'].values() if media.get('src')] 
        
        if media_json.get('product-videos',''):
            details['videos'] = [media['videoUrl'] for media in media_json['product-videos']['sources'].values()]

        if media_json.get('customer-images',''):
            details['customer_images'] = [media['src'] for media in media_json['customer-images']['sources'].values()]
    except:
        ...
    
    try:
        details['categories'] = [{'name':clean_str(category.text),'link':category['href']} for category in soup.select('.shop-breadcrumb li a')]

        details['categories_flat'] = ' > '.join([category['name'] for category in details['categories']])
    except:
        ...
    try:
        if price_soup:= soup.find('script',id=re.compile('pricing-price-')):
            price_json = json.loads(price_soup.text)['app']['priceDomain']
            # price_info = {}
            if price_json['regularPrice'] and price_json['totalSavings']:
                details['retail_price'] = price_json['customerPrice']
                details['msrp_price'] = price_json['regularPrice']
                details['discount'] = price_json['totalSavings']
                details['discount_percentage'] = price_json['totalSavingsPercent']
            else:
                details['retail_price'] = price_json['customerPrice']

            if price_json.get('hasFinancingOption',''):
                details['finance'] = {
                    'monthly_payment': round(float(price_json['monthlyPayment']),2),
                    'finance_term' : price_json['financeTerm']
                }
            price_json = json.loads(price_soup.text)['app']['data']
            if price_json.get('skuPriceDomain','') and price_json['skuPriceDomain'].get('paymentOptions',''):
                details['payment_options'] = price_json['skuPriceDomain']['paymentOptions']
                for payment_option in details['payment_options']:
                    payment_option.pop('isDisplayable','')

            
            if price_json.get('upgradePlusPaymentOption','') and price_json['upgradePlusPaymentOption']['isDisplayable']:
                details['upgrade_plus'] = price_json['upgradePlusPaymentOption']
                details['upgrade_plus'].pop('isDisplayable')

            # details['price_info'] = price_info
    except:
        print(traceback.format_exc())
        ...

    try:
        variations_soup = soup.find('script',id=re.compile('shop-product-variations-')).text
    except:
        variations_soup=None


    if not variations_soup:
        child_element = soup.find(id=re.compile(r"^shop-product-variations-\d+$"))
        if child_element:
            try:
                match = re.search(r"shop-product-variations-(\d+)", child_element['id'])
                if match:
                    var_id = f"shop-product-variations-{match.group(1)}"
                    check_split='}, "' + var_id + '", "'
                    var_text=html.split(check_split)[1].split('", "en-US', 1)[0]
                    if var_text:
                        variations_soup = var_text.replace('\\\"', '"').replace('\\"', "\"")
            except:
                pass
    try:
        if variations_soup:
            selected_variation = {}
            variations_skus = []    
            variation_types = {}
            variation_json = json.loads(variations_soup)
            if variation_json.get('categories'):
                variations = variation_json['categories']
            elif variation_json.get('app') and variation_json['app'].get('categories'): 
                variations = variation_json['app']['categories']
            else:
                variations = []
            for variation in variations:
                variation_type = variation['displayName']
                variation_types[variation_type] = []
                for option in variation['variations']:
                    if option['displayStatus']=='selected':
                        selected_variation[variation_type] = option['name'].replace('\\u002F', '/')
                    if option['variationSku'] not in variations_skus and option['displayStatus']!='selected':
                        variations_skus.append(option['variationSku'])

                    if option['name'].replace('\\u002F', '/') not in variation_types[variation_type]:
                        variation_types[variation_type].append(option['name'].replace('\\u002F', '/'))

            variant_urls = soup.select('.seo-list.d-none li a[href]')

            if variant_urls:
                variants_sku_url = {}
                for variant_url in variant_urls:
                    for sku in variations_skus:
                        if sku in variant_url.get('href',''):
                            variants_sku_url[sku] = variant_url['href']
                            break
                if variants_sku_url:
                    variations_skus = variants_sku_url

            
            details['selected_variation'] = ' | '.join([f"{key}: {value}" for key, value in selected_variation.items()])
            details['variations_skus'] = variations_skus
            details['variation_types'] = variation_types
    except:
        ...

    if fullfilment_soup:= soup.find('script',id=re.compile('fulfillment-fulfillment-summary-')):

        fullfilment_json = json.loads(fullfilment_soup.text)
        
        if fullfilment_json.get('fulfillment',None):
            details['fulfillment'] = {} 
            try:
                if fullfilment_json['fulfillment']['responseInfos'][0]['pickupEligible']:
                    fullfilment_json['pickup']['responseInfos'][0]['location']['availability'].pop('availabilityToken','')
                    details['fulfillment']['pickup'] = {
                        'availability':fullfilment_json['pickup']['responseInfos'][0]['location']['availability'],
                        'store_location':fullfilment_json['pickup']['responseInfos'][0]['location']['locationDetail']
                    }
            except:
                ...
            try:    
                if fullfilment_json['fulfillment']['responseInfos'][1]['shippingInfo']['shippable']:
                    details['fulfillment']['shipping'] ={'delivery_options':''}

                    details['fulfillment']['shipping']['delivery_options'] = [
                        {
                            'name':option['name'],
                            'price':option['price'],
                            'delivery_time':option['minLineItemMaxDate']
                        }

                        for option in fullfilment_json['fulfillment']['customerLosGroups']
                    ]
                    details['fulfillment']['shipping']['postal_code'] = fullfilment_json['fulfillment']['responseInfos'][0]['postalCode']
                else:
                    details['fulfillment']['shipping'] = 'Not shippable'
            except:
                ...
    try:
        buying_options_soup = soup.find('script',id=re.compile('fulfillment-buying-options-'))

        if buying_options_soup and product_schema:
            buying_options_json = json.loads(buying_options_soup.text)['buyingOptions']
            buying_options = []
            for option in buying_options_json:
                for offer in product_schema['offers']['offers']:
                    if offer['description'] == option['description']:
                        opt = {
                            'name':option['description'],
                            'type':option['type'],
                            'price':offer['price'],
                            'price_currency':offer['priceCurrency'],
                            'item_condition':offer['itemCondition'].replace('http://schema.org/','').replace("Condition",''),
                        }
                        if offer.get('availability',''):
                            opt['in_stock']= True if 'InStock' in offer['availability'] else False
                        if option.get('pdpUrl',''):
                            opt['item_sku'] = option['skuId']
                            opt['url'] = option['pdpUrl']
                        elif opt['item_condition']!='New':
                            opt['url'] = product_url.replace('/site/','/product/').split('.p?')[0]+'/openbox?condition='+opt['type'].lower()
                        else:
                            opt['url'] = product_url

                        buying_options.append(opt)
                        break

            details['buying_options'] = buying_options
    except:
        ...

    if offers and bs(offers,'html.parser').text.strip():
        details['offers'] = clean_str(bs(offers,'html.parser').text)

    if delivery:
        details['delivery_json'] = json.loads(delivery)

    if pickup:
        details['pickup_json'] = json.loads(pickup)

    if delivery_text:
        details['delivery_text'] = clean_str(bs(delivery_text,'html.parser').text)

    if pickup_texts:
        if isinstance(pickup_texts,list):
            for pickup_text in pickup_texts:
                pickup_text['pickup_text'] = clean_str(bs(pickup_text['pickup_text'],'html.parser').text)

        details['pickup_texts'] = pickup_texts

    try:
        description_soup = soup.find('script',id=re.compile('shop-overview-accordion-'))

        if description_soup:
            description_text = description_soup.text
        else:
            overview_accordion_id = soup.select_one('.shop-overview-accordion').parent['id']
            componentVersion = soup.select_one(f'#{overview_accordion_id}[data-version]').get('data-version')
            description_text = search_text_between(html,'getInitializer().then(initializer => initializer.initializeComponent({"creatorNamespace":"shop","componentId":"overview-accordion","contractVersion":"v1","componentVersion":"'+componentVersion+'"}, "'+overview_accordion_id+'", "','", "en-US"));')
            if description_text:
                description_text = description_text.replace('\\\"','"').replace('\\"',"\"")
                

        if description_text:
            description_json = json.loads(description_text)['app']['componentData']
            details['description'] = ' | '.join([ clean_str(description['plainText']) for description in description_json['product-description']['description']['longDescription']['parsedHtmlFragments'] if description.get('plainText','')])
            
            details['features'] = [
                feature["description"] if feature['title'] is None else f"{feature['title']}: {feature['description']}"
                for feature in description_json['product-features']['features']
            ]

            if description_json['disclaimers']:
                details['disclaimers'] = description_json['disclaimers']

            if description_json.get('whats-included','') and description_json['whats-included'].get('includedItems'):
                details['what_included'] = [item['description'] for item in description_json['whats-included']['includedItems']] 
    except:
        ...

    try:
        specification_text = soup.find('script',id=re.compile('shop-specifications-'))
        if not specification_text:
            specification_id = soup.select_one('.shop-specifications').parent['id'] 
            specification_text = search_text_between(html,'getInitializer().then(initializer => initializer.initializeComponent({"creatorNamespace":"shop","componentId":"specifications","contractVersion":"v1","componentVersion":"2.5.55"}, "'+specification_id+'", "','", "en-US"));')
            if specification_text:
                specification_text = bs(specification_text.replace('\\\"','"').replace('\\"',"\""),'html.parser')

        if specification_text:
                specification_json = json.loads(specification_text.text)['specifications']
                details['specifications'] = {}
                details['attributes'] = {}
                
                for category in specification_json['categories']:
                    details['specifications'][category['displayName']] = {}
                    for item in category['specifications']:
                        details['specifications'][category['displayName']][item['displayName']] = item['value']
                        details['attributes'][item['displayName']] = item['value']
    except:
        ...

    qa_soup = soup.find('script',id=re.compile('user-generated-content-question-distillation-'))
    if qa_soup:
        try:
            qa_json = json.loads(qa_soup.text)['app'].get('questions','')

            if qa_json and qa_json.get('results',''):
                qas = []

                for qa in qa_json['results']:
                    qa_info = {
                        'id':qa['questionId'],
                        'title':qa['questionTitle'],
                        'submission_time':qa['submissionTime'],
                        'answer_count':qa['answerCount'],
                        'answers':[
                            {
                                'id':ans['answerId'],
                                'text':ans['answerText'],
                                'user_nickname':ans['userNickname'],
                                'helpful_votes':ans['netHelpfulness'],
                                'positive_feedback_count':ans['positiveFeedbackCount'],
                                'negative_feedback_count':ans['negativeFeedbackCount'],
                                'submission_time':ans['submissionTime']
                            }
                            for ans  in qa['answersForQuestion']
                        ]
                    }

                    qas.append(qa_info)

                details['qas'] = qas
        except:
            ...

    review_soup = soup.find('script',id=re.compile('user-generated-content-ratings-and-reviews-'))

    if not review_soup:
        review_id = soup.select_one('.user-generated-content-ratings-and-reviews').parent['id']
        # review_text = search_text_between(html,'getInitializer().then(initializer => initializer.initializeComponent({"creatorNamespace":"user-generated-content","componentId":"ratings-and-reviews","contractVersion":"v1","componentVersion":"24.41.1"}, "'+review_id+'", "','", "en-US"));')
        review_text = search_text_between(html,'}, "'+review_id+'", "','", "en-US"));')
        if review_text:
            review_soup =bs(review_text.replace('\\\"','"').replace('\\"',"\""),'html.parser')

    if review_soup:
        try:
            review_json = json.loads(review_soup.text)['app']
            
            
            review_info = {}
            if review_json['stats']['averageOverallRating'] or review_json['stats']['totalReviewCount']:
                details['verified_purchase_count'] = review_json['stats']['verifiedPurchaseCount']
                review_info['rating'] = review_json['stats']['averageOverallRating']
                review_info['reviews_count'] = review_json['stats']['totalReviewCount']
                review_info['recommended_percent'] = review_json['stats']['recommendedPercent']
                review_info['rating_breakdown'] = review_json['stats']['ratingDistribution']

                if review_json.get('aggregateSecondaryRatings'):
                    review_info['secondary_ratings'] = [
                        {
                            'name':rating['attributeLabel'],
                            'count':rating['count'],
                            'rating': round(rating['avg'],2)
                        }
                        for rating in review_json['aggregateSecondaryRatings']
                    ]
                
                if review_json.get('distillation','') and (review_json['distillation'].get('positiveFeatures','') or review_json['distillation'].get('negativeFeatures','')):
                    top_mentions ={}
                    if review_json['distillation'].get('positiveFeatures'):
                        top_mentions['positive'] = [
                                                    { 'name':item['name'], 'count':item['totalReviewCount'],
                                                    'url': "https://www.bestbuy.com" + item['standaloneLink'].replace('\\u002F', '/')}
                                                    for item in review_json['distillation']['positiveFeatures']]

                    if review_json['distillation'].get('negativeFeatures'):
                        top_mentions['negative'] = [
                                                    { 'name':item['name'], 'count':item['totalReviewCount'],
                                                    'url': "https://www.bestbuy.com" + item['standaloneLink'].replace('\\u002F', '/')}
                                                    for item in review_json['distillation']['negativeFeatures']]

                    review_info['top_mentions'] = top_mentions
                if review_json.get('expert','') and review_json['expert'].get('reviewSummary') and review_json['expert']['reviewSummary'].get('overallRating'):
                    review_info['expert_review'] = {
                        'avg_rating':review_json['expert']['reviewSummary']['overallRating'].get('actual'),
                        'total_review':review_json['expert']['reviewSummary'].get('totalResults'),
                        'reviews':review_json['expert']['reviews'].get('results')
                    }
                    for review in review_info['expert_review']['reviews']:
                        review.pop('skus','')

                if review_json.get('reviews','') and review_json['reviews'].get('topics',''):
                    review_info['reviews'] = [
                        {
                            'id':review['id'],
                            'link':review['writeCommentUrl'],
                            'badges':[ badge['badgeName'] for badge in review['badges']],
                            'author':review['author'],
                            'title':review['topicType'],
                            'text':review['text'],
                            'rating':review['rating'],
                            'review_submission_time':review['submissionTime'],
                            'positive_feedback':review['positiveFeedbackCount'],
                            'negative_feedback':review['negativeFeedbackCount'],
                            'days_of_ownership':review['daysOfOwnership'],
                            'photos' : [photo['normalUrl'] for photo in review['photos']],
                            'pros' : review['pros'],
                        }

                        for review in review_json['reviews']['topics']
                    ]
                details['reviews'] = review_info
        except:
            ...
    return details
