set -ex
source /sandbox/env.sh
cd /sandbox/code/github/threefoldtech/zeroCI/backend
redis-server /etc/redis/redis.conf
for i in {1..5}; do python3 worker.py &> worker_$i.log & done
rqscheduler &> schedule.log &
service nginx start
python3 zeroci.py
