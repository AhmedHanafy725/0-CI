set -ex
mkdir /var/zeroci
mkdir -p /root/.config/jumpscale/
cd /sandbox/code/github/threefoldtech/zeroCI/install/config
cp cron /var/spool/cron/crontabs/root
cp redis.conf /etc/redis/redis.conf
cp jsng_config.toml /root/.config/jumpscale/config.toml
cd /sandbox/code/github/threefoldtech/zeroCI/backend
redis-server /etc/redis/redis.conf
for i in {1..5}; do cp worker.py worker$i.py; python3 worker$i.py &> worker_$i.log & done
rqscheduler &> schedule.log &
service cron start
python3 zeroci.py &> zeroci.log &
caddy reverse-proxy --from $DOMAIN --to 0.0.0.0:6010
