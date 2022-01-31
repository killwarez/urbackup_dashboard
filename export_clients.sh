#!/usr/bin/bash
HOST = '192.168.1.1'
USER = '12345'
PASS = '12345'
sqlite3 -header -csv /var/urbackup/backup_server.db "select * from clients" >/tmp/clients_$HOSTNAME.csv
ftp -n $HOST <<FTP_SCRIPT
quote user $USER
quote pass $PASS
put /tmp/clients_$HOSTNAME.csv /clients_$HOSTNAME.csv
quit
FTP_SCRIPT
rm /tmp/clients_$HOSTNAME.csv
exit 0