from flask import Flask, render_template
import sqlite3, sys, os
db_path = os.path.dirname(os.path.abspath(__file__)) + "\\db\\urbackup_dashboard.db"

app = Flask(__name__)

@app.route('/')
def index():

    headers = ("Server name","Workstation name","Last seen","Last file backup","Last image backup","File backup status","Image backup status")

    try:
        con = sqlite3.connect(db_path)
        cur = con.cursor()
    except:
        print("Exception raised while opening SQLite DB file")
        sys.exit()

    clients = cur.execute("SELECT * FROM clients").fetchall()

    return render_template('urbackup_dashboard.html',headers=headers,clients=clients,title='UrBackup Dashboard')

if __name__ == '__main__':
    app.run()
