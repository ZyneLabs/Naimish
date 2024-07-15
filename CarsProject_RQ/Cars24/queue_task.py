from common.utils import *
from .Cars24Crawler import crawl_urls
from .Cars24Parser import cars24_parser,product_collection
import sys

redis_conn = Redis()
queue = Queue('Cars24',connection=redis_conn)

def main(type):
    if type == 'crawl':
        job = queue.enqueue(crawl_urls)
        print(f"Queued job with ID: {job.id}")
    else:
        for url in product_collection.find({'scraped':0}).limit(10):
            job = queue.enqueue(cars24_parser, url['url'])
            print(f"Queued job with ID: {job.id}")

if __name__ == "__main__":
    
    main(sys.argv[1])
