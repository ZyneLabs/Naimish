from rq import Queue
from redis import Redis
from common.utils import *
from .YallamotorCrawler import crawl_from_brands
from .YallamotorParser import yallamotor_parser,product_collection
import sys

redis_conn = Redis()
queue = Queue('Yallamotor',connection=redis_conn)

def main(type):
    if type == 'crawl':
        job = queue.enqueue(crawl_from_brands)
        print(f"Queued job with ID: {job.id}")
    else:
        for url in product_collection.find({'scraped':0}).limit(10):
            job = queue.enqueue(yallamotor_parser, url['url'])
            print(f"Queued job with ID: {job.id}")

if __name__ == "__main__":
    
    main(sys.argv[1])
