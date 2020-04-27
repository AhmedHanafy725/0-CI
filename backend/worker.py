import os

from redis import Redis
from rq import Worker, Queue, Connection

listen = ["default"]

if __name__ == "__main__":
    with Connection(Redis()):
        worker = Worker(list(map(Queue, listen)))
        worker.work()
