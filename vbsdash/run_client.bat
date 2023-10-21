call .\.venv\scripts\activate.bat
python urbackup_export_clients_status.py
timeout /T 40
deactivate
