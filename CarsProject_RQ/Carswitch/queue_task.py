from common.utils import *
from .CarswitchCrawler import crawl_category
from .CarswitchParser import carswitch_parser,product_collection
import sys

redis_conn = Redis()
queue = Queue('Carswitch',connection=redis_conn)

def main(type):
    if type == 'crawl':
        job = queue.enqueue(crawl_category)
        print(f"Queued job with ID: {job.id}")
    else:
        for url in product_collection.find({'scraped':0}).limit(10):
            job = queue.enqueue(carswitch_parser, url['url'])
            print(f"Queued job with ID: {job.id}")

if __name__ == "__main__":
    
    main(sys.argv[1])
