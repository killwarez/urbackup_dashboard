cd /opt/vbsdash
while true;
do
    srv="/usr/lib/systemd/system/vbsdash.service"
    if [ -z `pidof vbsdash` ] && [ -f $srv ];
    then
        source ./.venv/bin/activate
        python3 urbackup_export_clients_status.py
    else
        # Write log that service is Up
        echo 0
    fi
    sleep 30
done
