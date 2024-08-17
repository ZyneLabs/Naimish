from common.utils import *
from .AutomalluaeCrawler import crawl_urls
from .AutomalluaeParser_v2 import automalluae_parser,product_collection
import sys

queue = Queue('Automalluae',connection=redis_conn)

def main(type):
    if type == 'crawl':
        job = queue.enqueue(crawl_urls)
        print(f"Queued job with ID: {job.id}")
    else:
        for url in product_collection.find({'scraped':0}).limit(10):
            job = queue.enqueue(automalluae_parser, url['url'])
            print(f"Queued job with ID: {job.id}")

if __name__ == "__main__":
    
    main(sys.argv[1])
