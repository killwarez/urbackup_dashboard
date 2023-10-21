cd /opt/vbsdashsrv
python3 -m venv .venv
source ./.venv/bin/activate
pip3 install -r requirements.txt
mkdir csv
deactivate

# Install Linux Service
chmod +x start.sh
cp /opt/vbsdashsrv/vbsdashsrv.service /usr/lib/systemd/system/
systemctl daemon-reload && sysctl --system
systemctl enable vbsdashsrv.service

# Set user and permissions
useradd -m vbsdashsrv
chown -R vbsdashsrv:vbsdashsrv /opt/vbsdashsrv