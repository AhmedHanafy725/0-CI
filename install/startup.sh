set -ex
mkdir /var/zeroci
cd /sandbox/code/github/threefoldtech/zeroCI/install
cp cron /var/spool/cron/crontabs/root
cp nginx.conf /etc/nginx/sites-available/default
cp redis.conf /etc/redis/redis.conf
cp jsng_config.toml /root/.config/jumpscale/config.toml
cd /sandbox/code/github/threefoldtech/zeroCI/backend
redis-server /etc/redis/redis.conf
for i in {1..5}; do cp worker.py worker$i.py; python3 worker$i.py &> worker_$i.log & done
rqscheduler &> schedule.log &
service nginx start
service cron start
python3 zeroci.py
