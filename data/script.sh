rm -f /www/pages/log.tgz
tar -hzcvf /www/pages/log.tgz /var/log/ /var/tmp/ /etc/
echo "log.tgz"