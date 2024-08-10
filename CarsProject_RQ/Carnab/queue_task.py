from common.utils import *
from .Carnabcrawler import crawl_carnab
from .CarnabParser import collect_carnab_data

import sys

queue = Queue('Carnab',connection=redis_conn)

def main(type):
    if type == 'crawl':
        job = queue.enqueue(crawl_carnab)
        print(f"Queued job with ID: {job.id}")
    else:
        job = queue.enqueue(collect_carnab_data)
        print(f"Queued job with ID: {job.id}")
        
if __name__ == "__main__":
    
    main(sys.argv[1])
