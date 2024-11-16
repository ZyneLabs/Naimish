import re
import json
from bs4 import BeautifulSoup

def clean_str(input_str: str, sep="|"):
    if input_str is None:
        return ""

    if type(input_str) is not str:
        return input_str

    input_str = re.sub(r"\s+", " ", input_str).replace("\n", sep)

    return input_str.strip()

def get_delivery_info(soup: BeautifulSoup, response_json: dict) ->  dict|None :
    
    maybe_standard_delivery = soup.select_one('#mir-layout-DELIVERY_BLOCK-slot-PRIMARY_DELIVERY_MESSAGE_LARGE span')
    response_json['standard_delivery'] = '-'
    response_json['delivery_information'] = '-'
    response_json['fast_delivery'] = '-'
    if maybe_standard_delivery:
        response_json['standard_delivery'] = maybe_standard_delivery.get('data-csa-c-delivery-time','')
        response_json['delivery_information'] = maybe_standard_delivery.find('span').find_previous_sibling(text=True).strip() if maybe_standard_delivery.find('span') else '-'
        if not response_json['delivery_information'] and  maybe_standard_delivery.find('a'):
            response_json['delivery_information'] = maybe_standard_delivery.find('a').text
    maybe_fast_delivery = soup.select_one('#mir-layout-DELIVERY_BLOCK-slot-SECONDARY_DELIVERY_MESSAGE_LARGE span')
    if maybe_fast_delivery:
        response_json['fast_delivery'] = maybe_fast_delivery.get('data-csa-c-delivery-time','')
    
    maybe_countdown = soup.select_one('#ftCountdown')
    if maybe_countdown:
        response_json['countdown'] = maybe_countdown.text
    return response_json

def get_other_sellers(soup:BeautifulSoup) -> list|None:
    sellers = []
    for seller in soup.select('#aod-sticky-pinned-offer ,#aod-offer'):
        retail_price = seller.select_one('.a-price .a-offscreen')
        if retail_price and len(clean_str(retail_price.text)):
            retail_price = retail_price.text.strip()
        elif retail_price and retail_price.next_sibling:
            retail_price = retail_price.next_sibling.text.strip()
            
        else:
            continue

        if seller_rank := seller.find(id=re.compile('aod-price-[0-9]+')):
            rank = int(re.findall(r"\d+",seller_rank.get('id'))[0])
            
        seller_info = {
            'rank' : rank,
            'condition' : '-',
            'retail_price' : retail_price,
            'msrp_price': "-",
            'discount' : '-',
            'condition_text' : '-',
            'seller_name' : clean_str(seller.select_one('#aod-offer-soldBy .a-col-right .a-size-small').text),
            'seller_id' : clean_str(seller.select_one('#aod-offer-soldBy .a-col-right .a-size-small').get('href').split('&seller=')[-1].split('&')[0]) if seller.select_one('#aod-offer-soldBy .a-col-right .a-size-small').get('href') else '-',
            'seller_ratings' :'-',
            'offer_id':'-',
            'min_quantity' : '-',
            'max_quantity' : '-',
            'shipped_by' : '-',
            'standard_delivery':'-',
            'fast_delivery':'-',
            'delivery_information':''
        }
        maybe_condition = seller.select_one('#aod-offer-heading')
        if maybe_condition:
            seller_info['condition'] = clean_str(maybe_condition.text)
        
        maybe_msrp_price = seller.select_one('.centralizedApexBasisPriceCSS .a-price .a-offscreen')
        if maybe_msrp_price:
            seller_info['msrp_price'] = maybe_msrp_price.text.replace('₹','').strip()
            seller_info['discount'] = seller.select_one('.centralizedApexPriceSavingsPercentageMargin').text.replace('%','').replace('-','')

        maybe_rating = seller.select_one('#aod-offer-seller-rating i')
        if maybe_rating:
            seller_info['seller_ratings'] = [rating.replace('a-star-mini-','').replace('-','.') for rating in maybe_rating.attrs['class'] if 'a-star-mini-' in rating][0]

        maybe_offer = seller.find(attrs = {'data-csa-c-func-deps':"aui-da-aod-atc-action"})
        if maybe_offer:
            offer_json  = json.loads(maybe_offer.get('data-aod-atc-action'))
            seller_info['offer_id'] = offer_json.get('oid')
            seller_info['min_quantity'] = offer_json.get('minQty')
            seller_info['max_quantity'] = offer_json.get('maxQty')

        seller_info = get_delivery_info(seller,seller_info)
        
        if seller.select_one('#aod-offer-shipsFrom .a-color-base'):
            seller_info['shipped_by'] = clean_str(seller.select_one('#aod-offer-shipsFrom .a-color-base').text)

        maybe_condition_text = seller.select_one('#condition-text-block-title .expandable-expanded-text')
        if maybe_condition_text:
            seller_info['condition_text'] = clean_str(maybe_condition_text.text)

        sellers.append(seller_info)
        
    return sellers

def get_offer_info(page_html: str) -> dict:
    soup = BeautifulSoup(page_html, 'lxml')

    page = 1
    if seller_rank :=soup.find(id=re.compile('aod-price-[0-9]+')):
        rank = int(re.findall(r"\d+",seller_rank.get('id'))[0])
        page = rank // 10 + 1

    product = {}
    sellers = get_other_sellers(soup)
    if soup.select_one('#aod-asin-title-text'):
        product = {
            'name' : clean_str(soup.select_one('#aod-asin-title-text').text),
            'image' : clean_str(soup.select_one('#aod-asin-image-id')['src']),
        }
    if soup.find(attrs = {'data-csa-c-func-deps':"aui-da-aod-atc-action"}):
        product['asin'] = json.loads(soup.find(attrs = {'data-csa-c-func-deps':"aui-da-aod-atc-action"}).get('data-aod-atc-action')).get('asin')
    maybe_rating = soup.select_one('#aod-asin-reviews-star')
    if maybe_rating:
        product['rating'] = [rating.replace('a-star-','').replace('-','.') for rating in maybe_rating.attrs['class'] if 'a-star-' in rating][0]

    maybe_total_rating = soup.select_one('.aod-asin-reviews-block-class')
    if maybe_total_rating:
        product['rating_count'] = clean_str(maybe_total_rating.text.replace('ratings',''))

    available_filters_soup = soup.select('#aod-filter-swatch-container-top div.aod-filter-swatch')
    available_filters = {filter.get('id').replace('aod-swatch-id-',''):True for filter in available_filters_soup}

    no_of_offers = len(sellers)
    max_page = None
    if no_of_offers_soup:= soup.select_one('#aod-filter-offer-count-string') :
        offer_text = no_of_offers_soup.text.split()[0].strip()
        if offer_text.isdigit():
            no_of_offers = int(offer_text)
            max_page = no_of_offers // 10 + 1

    return {   
        'product' : product,
        'current_page' : page,
        'sellers' : sellers,
        'available_filters' : available_filters,
        'no_of_pages': max_page,
        'no_of_offers' : no_of_offers,
    }