from common.utils import *
from .Dubizzlecrawler import crawl_duizle
import sys

queue = Queue('Dubizzle',connection=redis_conn)

def main(type):
    if type == 'crawl':
        job = queue.enqueue(crawl_duizle)
        print(f"Queued job with ID: {job.id}")
  
if __name__ == "__main__":
    
    main(sys.argv[1])
