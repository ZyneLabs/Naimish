from .RedditScraper import reddit_scraper
from common.utils import *

db = client['reddit']
product_collection = db['urls']
cache_collection = db['cache']
error_collection = db['error']

def check_cache_for(data):
    return cache_collection.find_one(data)

def save_cache_for(url,data):
    
    cache_collection.insert_one(
            {
               
                'url': url,
                'data': data,
                'updated_at': datetime.now(),
                'data_format': 'html',
                'info_type': 'crawl',
                'info_subtype': 'url_crawl',
            }
        )
    
def crawl_reddit_posts():
    page_url = 'https://www.reddit.com/r/DubaiPetrolHeads/?f=flair_name%3A%22%F0%9F%93%88%20Selling%22'

    while True:
        try:
            cache_data = check_cache_for({'url': page_url})

            if cache_data is not None:
                html = cache_data['data']
                status = 200

            else:
                req = reddit_scraper(page_url)
                html = req.text
                status = req.status_code
                save_cache_for(page_url, html)

            soup = BeautifulSoup(html, 'html.parser')
            post_urls = [
               {'url':'https://www.reddit.com' + a.get('href'),
                'scraped':0}
                for a in soup.select('a[slot="full-post-link"]')
                if product_collection.find_one({'url': 'https://www.reddit.com' + a.get('href')}) is None
            ]

            if len(post_urls) != 0:
                product_collection.insert_many(post_urls)
            
            next_page = soup.select_one('[slot="load-after"][src]')

            if next_page is not None:
                page_url = 'https://www.reddit.com' + next_page.get('src')
            else:
                break
            
        except Exception as ex:
            error_collection.insert_one(
                {
                    'url': page_url,
                    'status': status,
                    'error': str(ex),
                    'traceback': traceback.format_exc(),
                }
            )


