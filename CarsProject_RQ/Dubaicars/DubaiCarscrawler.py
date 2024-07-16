from common.utils import *

redis_conn = Redis()
queue = Queue('Dubaicars',connection=redis_conn)


db = client['dubaicars']
product_collection = db['urls']
cache_collection = db['cache']
error_collection = db['error']

def check_cache_for(data):
    return cache_collection.find_one(data)

def save_cache_for(maker_id,data, page=1):
    
    cache_collection.insert_one(
            {
               
                'maker_id': maker_id,
                'page': page,
                'data': data,
                'updated_at': datetime.now(),
                'data_format': 'html',
                'info_type': 'crawl',
                'info_subtype': 'url_crawl',
            }
        )

def crawl_makers():
    res = send_req_syphoon(PROXY_VENDOR,'get','https://www.dubicars.com/')
    main_soup = BeautifulSoup(res.content, 'html.parser')
    makers = main_soup.find('input',attrs={"name":"ma"}).parent.find_all('li')

    for i in makers[1:]:
        queue.enqueue(check_makers_fesibility,i.get("data-value"))

        

def check_makers_fesibility(maker_id):

    req = send_req_syphoon(PROXY_VENDOR,'get',f'https://www.dubicars.com/search-count?c=new-and-used&ma={maker_id}&mo=0&b=&set=&eo=export-only&stsd=&cr=USD&cy=&co=&s=&gi=&f=&g=&l=&st=')
    if int(req.text) > 0:
        cached_data = check_cache_for({'maker_id': maker_id,'page':1})
        if cached_data is not None:
            html = cached_data['data']
        else:
            res = send_req_syphoon(PROXY_VENDOR,'get',f'https://www.dubicars.com/search?c=new-and-used&ma={maker_id}&mo=0&b=&set=&eo=export-only&stsd=&cr=USD&cy=&co=&s=&gi=&f=&g=&l=&st=')
            html = res.text
            save_cache_for(maker_id,html,1)

        cat_soup = BeautifulSoup(html, 'html.parser')
        if cat_soup.select('section li.serp-list-item a.title'):
            if cat_soup.find('a',attrs={"rel":"next"}):
                total_pages = int(cat_soup.find('a',attrs={"rel":"next"}).parent.find_previous('li').find('a').text)

                for page in range(1,total_pages+1):
                    queue.enqueue(crawl_products, maker_id,page)
            else:   
                product_urls = [
                    {"url": a['href'], "title": a.text,'page':1,'maker_id':maker_id,"scraped":0}
                    for a in cat_soup.select('section li.serp-list-item a.title')
                    if product_collection.find_one({"url": a['href']}) is None
                ]

                if len(product_urls) != 0:
                    product_collection.insert_many(product_urls)


def crawl_products(maker_id,page):
    try:
        main_url= f'https://www.dubicars.com/search?c=new-and-used&ma={maker_id}&mo=0&b=&set=&eo=export-only&stsd=&cr=USD&cy=&co=&s=&gi=&f=&g=&l=&st='
        cache_data = check_cache_for({'maker_id': maker_id, 'page': page})

        if cache_data is not None:
            data = cache_data['data']
            status  = 200
        else:
            res = send_req_syphoon(PROXY_VENDOR,'get',main_url+f'&page={page}')
            status = res.status_code
            res.raise_for_status()
            data = res.text
            save_cache_for(maker_id,page,data)

        soup = BeautifulSoup(data, 'html.parser')

        product_urls = [
            {"url": a['href'], "title": a.text,'page':page,maker_id:maker_id,"scraped":0}
            for a in soup.select('section li.serp-list-item a.title')
            if product_collection.find_one({"url": a['href']}) is None
        ]

        if len(product_urls) != 0:
            product_collection.insert_many(product_urls)

    except Exception as ex:
        error_collection.insert_one(
            {
                'url': main_url,
                'page': page,
                'status': status,
                'date_time': datetime.now(),
                'error': str(ex),
                'traceback': traceback.format_exc(),
            }
        )
