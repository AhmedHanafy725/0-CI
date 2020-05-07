from datetime import datetime
from pathlib import Path

from redis import Redis

from Jumpscale import j


def remove(type, days=30):
    r = Redis()
    bcdb = j.data.bcdb.get("zeroci")
    model = bcdb.model_get(f"zeroci.{type}")
    for obj in model.find():
        run_time = datetime.fromtimestamp(obj.timestamp)
        now_time = datetime.now()
        time_diff = now_time - run_time
        if time_diff.days > days:
            obj.delete()
            r.delete(obj.id)


def get_size_in_giga_bytes(path):
    root = Path(path)
    size_in_bytes = sum(f.stat().st_size for f in root.rglob("*") if f.is_file())
    size_in_giga_bytes = size_in_bytes / (1024 ** 3)
    return size_in_giga_bytes


def get_total_size():
    bcdb_data_size = get_size_in_giga_bytes("/sandbox/var")
    redis_data_size = get_size_in_giga_bytes("/var/lib/redis")
    return bcdb_data_size + redis_data_size


def check():
    # Remove data if it is more than 30 GB
    for day in range(60, 1, -1):
        if get_total_size() > 30:
            remove("trigger", days=day)
            remove("schedule", days=day)
        else:
            break


if __name__ == "__main__":
    check()
