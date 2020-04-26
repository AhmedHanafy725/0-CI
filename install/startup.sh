set -ex
ssh-keygen -t rsa -N "" -f ~/.ssh/id_rsa -q -P ""
cp /root/.ssh/id_rsa.pub /sandbox/.ssh/authorized_keys
source /sandbox/env.sh
cd /sandbox/code/github/threefoldtech/zeroCI/backend
redis-server /etc/redis/redis.conf
for i in {1..5}; do python3 worker.py &> worker_$i.log & done
rqscheduler &> schedule.log &
service nginx start
python3 zeroci.py
