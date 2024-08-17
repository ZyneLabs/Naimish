from bs4 import BeautifulSoup as bs
import requests
from rq import Queue
from redis import Redis
from pymongo import MongoClient
from os import getenv
from datetime import datetime

redis_conn = Redis()
q = Queue('AmazonCrawler',connection=redis_conn, default_timeout=3600000)


MONGO_URI = getenv('MONGODB_URI')
PROXY_VENDOR = getenv('XHEAD_KEY')

client = MongoClient(MONGO_URI)
db = client['amazon_app']
product_collection = db['product']
category_collection = db['category']
cache_collection = db['cache']
error_collection = db['error']

def fetch_product_details(url,total_retries=3):
    headers = {
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.9',
        'User-Agent': 'Amazon.com/28.11.2.100 (Android/12/M2101K6P)',
        'X-Requested-With': 'com.amazon.mShop.android.shopping',
        'Cookie': 'lc-acbin=en_IN; mobile-device-info=dpi:420.0|w:1080|h:2181; amzn-app-id=Amazon.com/28.11.2.100/18.0.392664.0; ; i18n-prefs=INR; lc-acbin=en_IN;'
        }
     
    retry_count = 0
    payload = {
        'key':PROXY_VENDOR,
        'headers':headers,
        'url':url,
        'method':'get',
        'country_code':'in'
    }

    while retry_count < total_retries:
        try:
            return requests.post('https://api.syphoon.com',json=payload)
        except Exception as ex:
            retry_count += 1

def parse_product(product_soup):
    products = []
    for item in product_soup:
        product_info = {
            'asin': item['data-asin'],
            'url': 'https://www.amazon.in' + item.select_one('a.a-link-normal').get('href'),
            'image': item.select_one('img[data-image-latency="s-product-image"]').get('src'),
            'title': item.select_one('h2 .a-text-normal').text,
            'is_promoted' : True if item.select_one('.puis-sponsored-label-text') else False,
        }
        brand_soup = item.select_one('span.puis-medium-weight-text')
        if brand_soup:
            product_info['brand'] = brand_soup.text
        price_soup = item.select_one('div[data-cy="price-recipe"] .a-price .a-offscreen')
        if price_soup:
            product_info['price'] = price_soup.text

        msrp_soup = item.select_one('div[data-cy="price-recipe"] .a-section.aok-inline-block')
        if msrp_soup:
            product_info['msrp'] = msrp_soup.select_one('.a-price .a-offscreen').text
            product_info['discount'] = msrp_soup.find_next_sibling('span',class_='puis-light-weight-text').text.replace('off','').replace('(','').replace(')','').strip()

        
        rating_soup = item.select_one('div[data-cy="reviews-block"]')
        if rating_soup:
            rating_ = rating_soup.select_one('span.a-size-mini')
            if rating_:
                product_info['rating'] = rating_.text
            
            review_count = rating_soup.select_one('span.puis-light-weight-text')
            if review_count:
                product_info['total_rating_count'] = review_count.text.replace('(','').replace(')','').strip()

            if rating_soup.select_one('span.a-color-secondary'):
                product_info['bought_history'] = rating_soup.select_one('span.a-color-secondary').text

        color_soup = item.select_one('div.s-color-swatch-link')
        if color_soup:
            product_info['no_of_colors'] = color_soup.text.replace('colours','').strip()
        

        products.append(product_info)
    return products


def crawl_products(url):
    cache = cache_collection.find_one({'url':url})

    if cache:
        html = cache['data']
    else:
        resp = fetch_product_details(url)
        html = resp.text
        cache_collection.insert_one({
            'url':url,
            'data':html,
            'datetime':datetime.now()
        })

    soup = bs(html,'lxml')

    maybe_products = soup.select('div[data-component-type="s-search-result"]')
    if maybe_products:
        products = parse_product(maybe_products)
        product_collection.insert_many(products)

    next_page = soup.select_one('li.a-last a')

    if next_page:
        q.enqueue(crawl_products, 'https://www.amazon.in' + next_page['href'])

    return soup

def get_leaf_categories(url,category_name):

    cache = cache_collection.find_one({'url':url})

    if cache:
        html = cache['data']
    else:
        resp = fetch_product_details(url)
        html = resp.text
        cache_collection.insert_one({
            'url':url,
            'data':html,
            'datetime':datetime.now()
        })
        
    soup = bs(html,'lxml')
    
    maybe_sub_categories = soup.select('div.apb-default-category-drilldown span.a-list-item a')
    categories = []
    if maybe_sub_categories:
        for sub_category in maybe_sub_categories:
            cat_name = sub_category.text
            q.enqueue(get_leaf_categories, 'https://www.amazon.in' + sub_category['href'])
            categories.append(cat_name)

        category_collection.insert_many({
                'category_name':category_name,
                'category_url':url,
                'sub_categories':categories
            })
    else:
        maybe_products = soup.select('div[data-component-type="s-search-result"]')
        if maybe_products:
            products = parse_product(maybe_products)
            product_collection.insert_many(products)

        next_page = soup.select_one('li.a-last a')

        if next_page:
            q.enqueue(crawl_products, 'https://www.amazon.in' + next_page['href'])

