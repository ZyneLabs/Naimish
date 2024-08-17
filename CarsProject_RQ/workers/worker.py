from rq import Worker, Queue, Connection
from redis import Redis
import os
import subprocess

redis_url = os.getenv('REDIS_URI')

subprocess.Popen(['rq-dashboard', '--redis-url',redis_url])

listen = ['default','Automalluae','Cars24','Carswitch','Dubaicars','Kavak','Yallamotor','Dubizzle','Opensooq','Reddit']

conn = Redis.from_url(redis_url)

if __name__ == '__main__':
    with Connection(conn):
        worker = Worker(map(Queue, listen))
        worker.work()
