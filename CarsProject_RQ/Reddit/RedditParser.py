from common.utils import *
from .RedditScraper import reddit_scraper

redis_conn = Redis()
queue = Queue('Reddit',connection=redis_conn)

db = client['reddit']
product_collection = db['urls']
cache_collection = db['cache']
error_collection = db['error']
post_collection = db['posts']

def check_cache_for(data):
    return cache_collection.find_one(data)

def save_cache_for(url,data):
    
    cache_collection.insert_one(
            {
                'url': url,
                'data': data,
                'updated_at': datetime.now(),
                'data_format': 'html',
                'info_type': 'parse',
                'info_subtype': 'product_parse',
            }
        )
    

def reddit_parser(html):
    soup = BeautifulSoup(html, 'html.parser')

    maybe_title = soup.select_one('h1[slot="title"]')

    details = {}
    if not maybe_title:
        return {'message':'Post page not found'}
    
    post_menu = soup.select_one('shreddit-post-overflow-menu')
    if not post_menu:
        return {'message':'Post menu not found'}
    
    details['title'] =  maybe_title.text.strip()
    details['url'] = 'https://reddit.com' + post_menu['permalink']
    details['id'] = post_menu['post-id']
    details['comment_count']  = post_menu['comment-count']
    details['vote_count']  =soup.select_one('shreddit-post')['score']
    details['post_time'] = soup.select_one('faceplate-timeago')['ts']

    maybe_subreddit = soup.select_one('a.subreddit-name')
    if maybe_subreddit:
        details['sub_reddit'] = {
            'name': maybe_subreddit.text.strip(),
            'link': 'https://reddit.com' + maybe_subreddit['href']
        }

    maybe_author = soup.select_one('a.author-name')
    if maybe_author:
        details['author'] = {
            'name': maybe_author.text.strip(),
            'link': 'https://reddit.com' + maybe_author['href']
        }

    post_flair = soup.select_one('[slot="post-flair"] a')
    if post_flair:
        details['flair'] ={
            'name': post_flair.text.strip(),
            'link': 'https://reddit.com' + post_flair['href']
        }
    
    if soup.select_one('.text-neutral-content[slot="text-body"]'):
        details['content'] = clean_str(' | '.join([p.text for p in soup.select('.text-neutral-content p')]))
        details['content_html'] = soup.select_one('.text-neutral-content[slot="text-body"]').prettify()

    if soup.select_one('gallery-carousel img[data-lazy-srcset]'):
        details['images'] = [img['data-lazy-srcset'].split(',')[-1].strip().split()[0] for img in soup.select('gallery-carousel img[data-lazy-srcset]')]
    elif soup.select_one('.rte-media faceplate-img[src]'):
        details['images'] = [img['srcset'].split(',')[-1].strip().split()[0] for img in soup.select('.rte-media faceplate-img[src]')]
    elif soup.select_one('img#post-image'):
        details['images'] = [soup.select_one('img#post-image').get('srcset','').split(',')[-1].strip().split()[0]]

    return details


def collect_reddit_data():
    for product in product_collection.find({'scraped':0}):
        url = product['url']
        try:
            if post_collection.find_one({'url': url}) is not None:
                continue

            cache_data = check_cache_for({'url': url})

            if cache_data is not None:
                html = cache_data['data']
                status = 200
            else:
                req = reddit_scraper(url)
                html = req.text
                status = req.status_code
                save_cache_for(url, html)

            data = reddit_parser(html)
            post_collection.insert_one(data)

            product_collection.update_one({'url': url}, {'$set': {'scraped': 1}})
        except Exception as ex:
            error_collection.insert_one(
                {
                    'url': url,
                    'status': status,
                    'runner': 'Opensooq_product',
                    'error': str(ex),
                    'traceback': traceback.format_exc(),
                }
            )

