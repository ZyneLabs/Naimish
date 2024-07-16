from rq import Worker, Queue, Connection
from redis import Redis
import os
from dotenv import load_dotenv

load_dotenv()

listen = ['default','Automalluae','Cars24','Carswitch','Dubaicars','Kavak','Yallamotor']
redis_url = os.getenv('REDIS_URL', 'redis://localhost:6379')

conn = Redis.from_url(redis_url)

if __name__ == '__main__':
    with Connection(conn):
        worker = Worker(map(Queue, listen))
        worker.work()
