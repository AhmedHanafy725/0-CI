import os

PATH = "/sandbox/code/github/threefoldtech/zeroCI/backend/"
os.chdir(PATH)

from redis import Redis

from health_recover import Recover
from utils.utils import Utils

recover = Recover()


class Health(Utils):
    def get_process_pid(self, name):
        cmd = f"ps -aux | grep -v grep | grep '{name}' | awk '{{print $2}}'"
        response = self.execute_cmd(cmd=cmd, timeout=5)
        pids = response.stdout.split()
        return pids

    def test_redis(self):
        """Check redis is still working.
        """
        pid = self.get_process_pid("redis")
        if not pid:
            recover.redis()
        try:
            r = Redis()
            r.set("test_redis", "test")
            value = r.get("test_redis")
        except:
            recover.redis()

    def test_workers(self):
        """Check rq workers are up.
        """
        pids = self.get_process_pid("python3 worker")
        workers = len(pids)
        if workers < 5:
            for i in range(1, 6):
                pid = self.get_process_pid(f"python3 worker{i}")
                if not pid:
                    recover.worker(i)

    def test_schedule(self):
        """Check rq schedule is up.
        """
        pid = self.get_process_pid("rqscheduler")
        if not pid:
            recover.scheduler()


if __name__ == "__main__":
    health = Health()
    health.test_redis()
    health.test_workers()
    health.test_schedule()
