import os

from redis import Redis
from rq import Worker, Queue, Connection

listen = ["zeroci"]

if __name__ == "__main__":
    with Connection(Redis()):
        worker = Worker(list(map(Queue, listen)))
        worker.work()
