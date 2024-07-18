from bustednewspaper_scraper import bustednewspaper_scraper
from bs4 import BeautifulSoup
from pymongo import MongoClient
from datetime import datetime
from redis import Redis
from rq import Queue

q = Queue(connection=Redis())

client = MongoClient("localhost", 27017)
db = client["bustednewspaper"]
urls_collection = db["urls"]
cache_data = db["cache_data"]


def crawl_County():
    res  = bustednewspaper_scraper('YV749KjNlvgdbjsVWkW3','get','https://bustednewspaper.com/')
    soup = BeautifulSoup(res.text, 'html.parser')
    states_data = []
    state_details = {}
    for div in soup.select('div.main-content.home-mugshots-list')[1:]:
        for element in div.children:
            if element.name == 'h2':
                if state_details:
                    states_data.append(state_details)
                    state_details = {}
                state_details['url'] = element.a['href']
                state_details['state'] = element.text
                state_details['county'] =[]
            if element.name == 'a':
                state_details['county'].append({'name':element.text,'url':element['href']})
    else:
        states_data.append(state_details)

    for state in states_data:
        for county in state['county']:
            q.enqueue(crawl_records,{'url':county['url'],'state':state['state'],'state_url':state['url'],'county':county['name']})


def crawl_records(url_data,page=1):
    if page == 1:
        url = url_data['url']
    else:
        url = f"{url_data['url']}/page/{page}"

    cache = cache_data.find_one({'url': url})
    if cache:
        html = cache['html']
    else:
        res = bustednewspaper_scraper('YV749KjNlvgdbjsVWkW3','get',url)
        res.raise_for_status()
        cache_data.insert_one({'url': url, 'html': res.text,'timestamp': datetime.now()})
        html = res.text

    soup = BeautifulSoup(html, 'html.parser')
    
    urls = []

    for selector in ['div.wppsac-carousel-slides h2 a','article.post.type-post.status-publish h2 a']:

        if soup.select(selector):
            urls.extend([
                {'url':a['href'],
                'title':a.text,
                'scraped':0,
                'state':url_data['state'],
                'state_url':url_data['state_url'],
                'county':url_data['county'],
                'county_url':url_data['url']
                } 
                for a in soup.select(selector) if not urls_collection.find_one({'url':a['href']})
                ]
                )

    if len(urls) >= 1:
        urls_collection.insert_many(
            urls
        )
    # if page == 1 and soup.select_one('a.page-numbers:nth-last-child(2)') and 'Next' in soup.select_one('a.page-numbers:last-child span').text:
    #     total_pages = int(soup.select_one('a.page-numbers:nth-last-child(2)').text.replace(',',''))
    #     for i in range(2,total_pages+1):
    #         q.enqueue(crawl_records,{'url':url,'state':url_data['state']},i)
