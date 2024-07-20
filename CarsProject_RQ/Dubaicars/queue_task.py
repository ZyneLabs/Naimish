from common.utils import *
from .DubaiCarscrawler import crawl_makers
from .DubaiCarsParser import  dubaicars_parser,product_collection
import sys

queue = Queue('Dubaicars',connection=redis_conn)

def main(type):
    if type == 'crawl':
        job = queue.enqueue(crawl_makers)
        print(f"Queued job with ID: {job.id}")
    else:
        for url in product_collection.find({'scraped':0}).limit(10):
            job = queue.enqueue(dubaicars_parser, url['url'])
            print(f"Queued job with ID: {job.id}")

if __name__ == "__main__":
    
    main(sys.argv[1])
