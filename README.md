# UrBackup Dashboard - Web server and client
Set of Python scripts to collect UrBackup clients' status from multiple [UrBackup Servers](https://www.urbackup.org/download.html) to display on the single dashboard. Email notifications of backup issues.
### Features:
- Dashboard: Receive backup status information via REST API as CSV payload
- Dashboard: Client update API with token authorization
- Dashboard: UrBackup clients' status and errors display
- Client: UrBackup status collection using UrBackup API
- Client: UrBackup clients detailed errors collection
- Client: Auto-update via API
- Email notification of backup issues
### Requirements (Windows)
1. Python
2. Python virtual environment
```
pip install virtualenv
python -m venv venv
.\.venv\Scripts\activate.bat
```
3. Libraries
```
pip install -r requirements.txt
```
### Running (Windows)
#### Dashboard:
Rename empty database to *urbackup_dashboard.db*, then run:
```
cd .\dashboard\
python urbackup_dashboard_server.py
```
#### Client:
Set UrBackup server credentials. Add them to *urbackup_export_clients_params.py*, then run:
```
cd .\client\
python urbackup_export_clients_status.py
```
#### Notifications:
Configure email delivery in the *urbackup_dashboard_email_params.py* file.  
Schedule script running with Cron or Task Manager
### Add new client:
1. Add new token to *DB\urbackup_dashboard.db* -> *api_tokens* table
2. Add the same token to the *urbackup_export_clients_params.py* configuration
### Files and folders
#### Dashboard:
- *urbackup_dashboard_server.py* - Flask-based web server
- *urbackup_dashboard_send_email.py* - Email notification script on backup errors and warnings, should run with an external scheduler
- *urbackup_dashboard_email_params.py* - Jinja-based email template and sending settings; input credentials here before scheduling notifications
- *urbackup_export_clients_status_update.py* - Client updated script redistribution
- *urbackup_export_clients_params.py* - Client update requirement dummy file
- *DB\urbackup_dashboard.db* - SQLite3 dashboard database, add separate API token for every client
- *CSV\\* - Storage for legacy clients
- *Templates\\* - Jinja dashboard template
#### Client:
- *urbackup_export_clients_status.py* - Client main script
- *urbackup_export_clients_params.py* - Client configuration, add separate API token for every client
