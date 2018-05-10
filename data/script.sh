rm -f /www/pages/log.tgz
tar -hzcvf /www/pages/log.tgz /var/log/ /var/tmp/ /etc/
echo "http://$(ifconfig | grep -v '127.0.0.1' | grep  'inet ' |awk -F ":" '{print $2}'|awk '{print $1}')/log.tgz"