from rq import Queue
from redis import Redis
from common.utils import *
from .RedditCrawler import crawl_reddit_posts
from .RedditParser import collect_reddit_data
import sys

queue = Queue('Reddit',connection=redis_conn)

def main(type):
    if type == 'crawl':
        job = queue.enqueue(crawl_reddit_posts)
        print(f"Queued job with ID: {job.id}")
    else:
    
        job = queue.enqueue(collect_reddit_data)
        print(f"Queued job with ID: {job.id}")

if __name__ == "__main__":
    
    main(sys.argv[1])
