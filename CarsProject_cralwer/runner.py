from Albacars import AlbacarsCrawler
from Altayermotors import AltayermotorsCrawler
from Automalluae import AutomalluaeCrawler
from Carnab import CarnabCrawler
from Cars24 import Cars24Crawler
from Carswitch import CarswitchCrawler
from Dubaicars import DubaiCarsCrawler
from Dubizzle import DubizzleCrawler
from Kavak import KavakCrawler
from Firstchoicecars import FirstchoicecarsCrawler
from save_crawled_data import save_data

import os
import signal
import time
from multiprocessing import Process,cpu_count   
from rq import Worker, Queue
from redis import Redis

queue_dict= {
    AlbacarsCrawler:'Albacars',
    AutomalluaeCrawler:'Automalluae',
    AltayermotorsCrawler:'Altayermotors',
    CarnabCrawler:'Carnab',
    Cars24Crawler:'Cars24',
    CarswitchCrawler:'Carswitch',
    DubaiCarsCrawler:'Dubaicars',
    DubizzleCrawler:'Dubizzle',
    KavakCrawler:'Kavak',
    FirstchoicecarsCrawler:'Firstchoicecars'
}
redis_conn = Redis()

def start_worker(queue_name,dequeue_timeout=60):
    queue = Queue(queue_name, connection=redis_conn)
    worker = Worker([queue],connection=redis_conn)
    while True:
        if queue.count == 0:
            print(f"Queue {queue_name} is empty. Waiting for new jobs...")
            time.sleep(dequeue_timeout)
            if queue.count == 0:  
                print(f"No jobs found in queue {queue_name}. Shutting down worker.")
                break
        worker.work(burst=True)

def kill_workers(worker):
    os.kill(worker.pid, signal.SIGTERM)

def run_crawler_and_worker(crawler, queue_name):
    crawler.crawl_urls()
    queue = Queue(queue_name, connection=redis_conn)
    
    if queue.count > 0:
        start_worker(queue_name)

def start_crawler():
    worker_processes = []
    crawlers = [AlbacarsCrawler, AutomalluaeCrawler, AltayermotorsCrawler, CarnabCrawler, Cars24Crawler, CarswitchCrawler, DubaiCarsCrawler, DubizzleCrawler, KavakCrawler, FirstchoicecarsCrawler]
    
    for crawler in crawlers:
        p = Process(target=run_crawler_and_worker, args=(crawler, queue_dict[crawler]))
        p.start()
        worker_processes.append(p)

    for worker in worker_processes:
        worker.join()  # 

if __name__ == '__main__':
    start_crawler()
    # save_data()
