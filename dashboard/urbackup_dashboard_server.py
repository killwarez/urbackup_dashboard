from io import TextIOWrapper
import io
from flask import Flask, render_template, request, send_file
import sqlite3, sys, os, urbackup_csv_importer, urbackup_export_clients_status_update
from datetime import datetime

db_path = os.path.dirname(os.path.abspath(__file__)) + "\\db\\urbackup_dashboard.db"
client_filename = "urbackup_export_clients_status_new.py"
update_filename = "urbackup_export_clients_status_update.py"
update_path = os.path.dirname(os.path.abspath(__file__)) + "\\" + update_filename

app = Flask(__name__)

@app.route('/')
def index():
    # Connect to database
    try:
        con = sqlite3.connect(db_path)
        cur = con.cursor()
    except:
        print("Exception raised while opening SQLite DB file")
        sys.exit()

    headers = ("Server name","Workstation name","Last seen","Last file backup","Last image backup","File backup status","Image backup status", "Errors", "Warnings", "Client version")
    clients = cur.execute("SELECT * FROM clients").fetchall()
    return render_template('urbackup_dashboard.html',headers=headers,clients=clients,title='UrBackup Dashboard')

@app.route('/upload', methods=['POST'])
def upload():

    # Connect to database
    try:
        con = sqlite3.connect(db_path)
        cur = con.cursor()
    except:
        print("Exception raised while opening SQLite DB file")
        sys.exit()

    # Verify API token among database record
    api_token = request.headers.get('Authorization')
    cur.execute("SELECT * FROM api_tokens WHERE api_token = ?", (api_token,))
    result = cur.fetchone()

    # Respond with errors
    if not result:
        return 'Unauthorized', 401

    if 'file' not in request.files:
        return 'No file uploaded', 400

    file = request.files['file']

    if file.filename == '':
        return 'No file selected', 400

    # Try to import file
    if file:
        if urbackup_csv_importer.import_csv(TextIOWrapper(file)):
            return 'Uploaded', 200
        else:
            return 'Import failure', 400

@app.route('/latest_version', methods=['GET'])
def latest_version():

    # Connect to database
    try:
        con = sqlite3.connect(db_path)
        cur = con.cursor()
    except:
        print("Exception raised while opening SQLite DB file")
        sys.exit()

    # Verify API token among database record
    api_token = request.headers.get('Authorization')
    cur.execute("SELECT * FROM api_tokens WHERE api_token = ?", (api_token,))
    result = cur.fetchone()

    # Respond with error
    if not result:
        return 'Unauthorized', 401

    # Return client script latest version number
    version_number = urbackup_export_clients_status_update.get_client_version()
    return str(version_number)

@app.route('/get_latest_version', methods=['GET'])
def get_latest_version():
  
    # Connect to database
    try:
        con = sqlite3.connect(db_path)
        cur = con.cursor()
    except:
        print("Exception raised while opening SQLite DB file")
        sys.exit()

    # Verify API token among database record
    api_token = request.headers.get('Authorization')
    cur.execute("SELECT * FROM api_tokens WHERE api_token = ?", (api_token,))
    result = cur.fetchone()

    # Respond with error
    if not result:
        return 'Unauthorized', 401

    # Generate or retrieve the file to be downloaded
    with open(update_path, 'rb') as file:
        file_data = file.read()

    # Create an in-memory file-like object
    file_obj = io.BytesIO(file_data)

    # Seek to the beginning of the file
    file_obj.seek(0)

    return send_file(file_obj, as_attachment=True, download_name=client_filename)

@app.template_filter()
def format_datetime(value):
    dateTimeObj = datetime.strptime(value, "%Y-%m-%d %H:%M:%S")
    return dateTimeObj.strftime("%Y-%m-%d %H:%M")

if __name__ == '__main__':
    app.run()
