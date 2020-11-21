set -ex
if [ ! -z "$NAMESPACE" ] ; then
  echo "NAMESPACE=$NAMESPACE" >> /etc/environment
fi
if [ ! -z "$REDIS" ] ; then
  echo "REDIS=$REDIS" >> /etc/environment
fi
mkdir /zeroci/xml
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
python3 zeroci.py
