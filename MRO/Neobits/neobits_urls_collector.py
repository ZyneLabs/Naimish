import requests
import random
from bs4 import BeautifulSoup
import json

def crawl_base_category():
    req = requests.get('https://www.neobits.com/')
    soup = BeautifulSoup(req.content, 'html.parser')
    urls = []
    categories = ['https://www.neobits.com'+li['href'] for li in soup.select('ul.list-unstyled li a')]
    categories.extend(['https://www.neobits.com'+li['href'] for li in soup.select('ul.multi-column-dropdown li a')])
    while categories:
        category = categories.pop()
        random.shuffle(categories)
        for cat_url in crawl_products(category):
            urls.extend(cat_url)
        urls = list(set(urls))
        if len(urls) >= 100:
            break

    json.dump(urls, open('neobits_urls.json', 'w'), indent=4, ensure_ascii=False)

def crawl_products(cat_url):
    req = requests.get(cat_url)
    soup = BeautifulSoup(req.content, 'html.parser')

    products = ['https://www.neobits.com'+li['href'] for li in soup.select('div.products-item-inner.row a.item-link')]
    try:
        total_product = int(soup.select_one('.pagination.pagination-sm li:last-child a')['href'].split('=')[-1])

        if len(products) > 5:
            yield random.sample(products, 5)
        else:
            yield products

        selection = len(range(33, total_product,32))
        for page in random.sample(selection,min(len(selection),10)):
            req = requests.get(f'{cat_url}?rows=32&per_page={page}')
            soup = BeautifulSoup(req.content, 'html.parser')
            products = ['https://www.neobits.com'+li['href'] for li in soup.select('div.products-item-inner.row a.item-link')]
            if len(products) > 5:
                yield random.sample(products, 5)
            else:
                yield products
    except:
        yield products    

crawl_base_category()