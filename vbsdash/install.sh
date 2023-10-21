cd /opt/vbsdash
python3 -m venv .venv
source ./.venv/bin/activate
pip3 install -r requirements.txt
mkdir csv
deactivate

# Install Linux Service
chmod +x start.sh
cp /opt/vbsdash/vbsdash.service /usr/lib/systemd/system/
systemctl daemon-reload && sysctl --system
systemctl enable vbsdash.service

# Set user and permissions
useradd -m vbsdash
chown -R vbsdash:vbsdash /opt/vbsdash
