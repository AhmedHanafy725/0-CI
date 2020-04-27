cp ./services/* /etc/systemd/system
systemctl start mongodb
systemctl start redis
systemctl start zeroci
systemctl enable zeroci
systemctl start rqscheduler
systemctl enable rqscheduler
for i in {1..5}
do 
systemctl start rqworker\@$i
systemctl enable rqworker\@$i
done