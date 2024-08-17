from common.utils import *
from .Opensooqcrawler import crawl_opensooq
from .OpensooqParser import collect_opensooq_data

import sys

queue = Queue('Opensooq',connection=redis_conn)

def main(type):
    if type == 'crawl':
        job = queue.enqueue(crawl_opensooq)
        print(f"Queued job with ID: {job.id}")
    else:
        job = queue.enqueue(collect_opensooq_data)
        print(f"Queued job with ID: {job.id}")
        
if __name__ == "__main__":
    
    main(sys.argv[1])
