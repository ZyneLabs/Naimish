from common.utils import *
from .KavakCrawler import crawl_main_page
from .KavakParser import kavak_parser,product_collection
import sys

redis_conn = Redis()
queue = Queue('Kavak',connection=redis_conn)

def main(type):
    if type == 'crawl':
        job = queue.enqueue(crawl_main_page)
        print(f"Queued job with ID: {job.id}")
    else:
        for url in product_collection.find({'scraped':0}).limit(10):
            job = queue.enqueue(kavak_parser, url['url'])
            print(f"Queued job with ID: {job.id}")

if __name__ == "__main__":
    
    main(sys.argv[1])
