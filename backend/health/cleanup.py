import sys

sys.path.append("/sandbox/code/github/threefoldtech/zeroCI/backend")

from datetime import datetime
from pathlib import Path

from models.base import StoredFactory
from models.scheduler_run import SchedulerRun
from models.trigger_run import TriggerRun
from redis import Redis

REDIS_PATH = "/var/lib/redis"
WHOOSH_PATH = "/root/.config/jumpscale/whoosh_indexes/"


def remove(factory, days=30):
    redis = Redis()
    names = factory.list_all()
    for name in names:
        obj = factory.get(name)
        run_time = datetime.fromtimestamp(obj.timestamp)
        now_time = datetime.now()
        time_diff = now_time - run_time
        if time_diff.days > days:
            factory.delete(name)
            redis.delete(obj.run_id)


def get_size_in_giga_bytes(path):
    root = Path(path)
    size_in_bytes = sum(f.stat().st_size for f in root.rglob("*") if f.is_file())
    size_in_giga_bytes = size_in_bytes / (1024 ** 3)
    return size_in_giga_bytes


def get_total_size():
    whoosh_data_size = get_size_in_giga_bytes(WHOOSH_PATH)
    redis_data_size = get_size_in_giga_bytes(REDIS_PATH)
    return whoosh_data_size + redis_data_size


def check():
    # Remove data if it is more than 10 GB
    for day in range(60, 1, -1):
        if get_total_size() > 10:
            remove(TriggerRun, days=day)
            remove(SchedulerRun, days=day)
        else:
            break


if __name__ == "__main__":
    check()
