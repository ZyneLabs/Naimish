from common.utils import *
from .Albacarscrawler import crawl_albacars
from .AlbacarsParser import collect_albacars_data

import sys

queue = Queue('Albacars',connection=redis_conn)

def main(type):
    if type == 'crawl':
        job = queue.enqueue(crawl_albacars)
        print(f"Queued job with ID: {job.id}")
    else:
        job = queue.enqueue(collect_albacars_data)
        print(f"Queued job with ID: {job.id}")
        
if __name__ == "__main__":
    
    main(sys.argv[1])
