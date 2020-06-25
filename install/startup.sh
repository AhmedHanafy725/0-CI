set -ex
cd /sandbox/code/github/threefoldtech/zeroCI/backend
cp ../install/cron /var/spool/cron/crontabs/root
cp ../install/nginx.conf /etc/nginx/sites-available/default
cp ../installredis.conf /etc/redis/redis.conf
redis-server /etc/redis/redis.conf
for i in {1..5}; do cp worker.py worker$i.py; python3 worker$i.py &> worker_$i.log & done
rqscheduler &> schedule.log &
service nginx start
service cron start
python3 zeroci.py
