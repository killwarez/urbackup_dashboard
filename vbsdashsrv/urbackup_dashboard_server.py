import logging
from io import TextIOWrapper
import os, json
from flask import Flask, render_template, request, send_from_directory, jsonify
import sqlite3, sys, os, urbackup_csv_importer
import datetime

db_path = os.path.dirname(os.path.abspath(__file__)) + "//db//urbackup_dashboard.db"
log_path = os.path.dirname(os.path.abspath(__file__)) + "//log"

if not os.path.exists(log_path):
    os.makedirs(log_path)

logging.basicConfig(filename=log_path + '//record.log', level=logging.DEBUG)

app = Flask(__name__)

@app.route('/favicon.ico')
def favicon():
    return send_from_directory(os.path.join(app.root_path, 'static'), 'favicon.ico', mimetype='image/vnd.microsoft.icon')

@app.route('/')
def index():
    # Connect to database
    try:
        con = sqlite3.connect(db_path)
        cur = con.cursor()
    except:
        print("Exception raised while opening SQLite DB file")
        sys.exit()

    get_servers_errors = '''select
                                servername,
                                sum(case when lastbackup_file_status = 'Ok' OR lastbackup_file_status = 'Disabled' then 0 else 1 end) as lastfile_errors,
                                sum(case when lastbackup_image_status = 'Ok' OR lastbackup_image_status = 'Disabled' then 0 else 1 end) as lastimage_errors,
                                sum(case errors when '0' then 0 else 1 end) as server_errors,
                                sum(case warnings when '0' then 0 else 1 end) as server_warnings,
                                case when servername LIKE '%internet%' then 'internet' else case when servername LIKE '%local%' then 'local' else 'unknown' end end as location,
                                max(lastseen)
                            from clients
                            where
                                archived < 1
                            group by
                                location, servername'''

    headers = ("Server name", "Total file errors", "Total image errors", "Total logged errors", "Total logged warnings", "Location", "Recent last seen")
    content = cur.execute(get_servers_errors).fetchall()
    cur.close()
    con.close()
    return render_template('urbackup_dashboard_servers.html',headers=headers,content=content,title='UrBackup Dashboard')

@app.route('/clients')
def clients():
    # Connect to database
    try:
        con = sqlite3.connect(db_path)
        cur = con.cursor()
    except:
        print("Exception raised while opening SQLite DB file")
        sys.exit()

    headers = ("","Server name","Workstation name","Last seen","Last file backup","Last image backup","File backup status","Image backup status", "Errors", "Warnings", "Client version", "Logid", "Note")
    content = cur.execute("SELECT id, servername, name, lastseen, lastbackup_file, lastbackup_image, lastbackup_file_status, lastbackup_image_status, errors, warnings, client_ver, logid, note FROM clients WHERE archived < 1").fetchall()
    cur.close()
    con.close()
    return render_template('urbackup_dashboard_clients.html',headers=headers,content=content,title='UrBackup Dashboard')

@app.route('/archived')
def archived():
    # Connect to database
    try:
        con = sqlite3.connect(db_path)
        cur = con.cursor()
    except:
        print("Exception raised while opening SQLite DB file")
        sys.exit()

    headers = ("Server name","Workstation name","Last seen","Last file backup","Last image backup","File backup status","Image backup status", "Note")
    content = cur.execute("SELECT servername, name, lastseen, lastbackup_file, lastbackup_image, lastbackup_file_status, lastbackup_image_status, note FROM clients WHERE archived > 0").fetchall()
    cur.close()
    con.close()
    return render_template('urbackup_dashboard_archive.html',headers=headers,content=content,title='UrBackup Dashboard')

@app.route('/replica')
def replica():
    # Connect to database
    try:
        con = sqlite3.connect(db_path)
        cur = con.cursor()
    except:
        print("Exception raised while opening SQLite DB file")
        sys.exit()

    headers = ("VM Name","State","Health","Mode","Primary Server","Replica Server")
    content = cur.execute("SELECT VMName, State, Health, Mode, PrimaryServer, ReplicaServer FROM replica").fetchall()
    cur.close()
    con.close()
    return render_template('urbackup_dashboard_replica.html',headers=headers,content=content,title='UrBackup Dashboard')

@app.route('/emails')
def emails():
    # Connect to database
    try:
        con = sqlite3.connect(db_path)
        cur = con.cursor()
    except:
        print("Exception raised while opening SQLite DB file")
        sys.exit()

    try:
        headers = ("Server name","Client name","Email","Frequency (mins)", "Last sent","Location")
        content = cur.execute("""SELECT 
                                    servername, clientname, email, freq, last_sent, 
                                    case when servername LIKE '%internet%' then 'internet' else case when servername LIKE '%local%' then 'local' else 'unknown' end end as location 
                                 FROM email_recipients 
                              """).fetchall()
    except Exception as e:
        return 'Error: ' + str(e), 500
    else:
        return render_template('urbackup_dashboard_emails.html',headers=headers,content=content,title='UrBackup Dashboard')
    finally:
        cur.close()
        con.close()

@app.route('/sessions')
def sessions():
    # Connect to database
    try:
        con = sqlite3.connect(db_path)
        cur = con.cursor()
    except:
        print("Exception raised while opening SQLite DB file")
        sys.exit()

    try:
        headers = ("Session name","Computer name","Server name")
        content = cur.execute("SELECT Name, GuestMachineName, UrbackupServerName FROM sc_sessions").fetchall()
    except Exception as e:
        return 'Error: ' + str(e), 500
    else:
        return render_template('urbackup_dashboard_sessions.html',headers=headers,content=content,title='UrBackup Dashboard')
    finally:
        cur.close()
        con.close()

@app.route('/getlog', methods=['POST'])
def getlog():
    # Connect to database
    try:
        con = sqlite3.connect(db_path)
        cur = con.cursor()
    except:
        print("Exception raised while opening SQLite DB file")
        sys.exit()

    try:
        data = request.json  # Assuming JSON payload is sent in the request body
        if not data or not isinstance(data, list):
            return 'Invalid payload, expected JSON', 400
    except Exception as e:
        return 'Error: ' + str(e), 500

    try:
        for record in data:
            logid = record.get('logid')
            servername = record.get('servername')

            if logid and servername:
                sql_query = 'SELECT logmessages FROM logs WHERE logid = ' + logid + ' AND servername LIKE "%' + servername + '%"'
                cur.execute(sql_query)
                content = cur.fetchall()

                logHTML = []

                for row in content:
                    logmessages = row[0]
                    logmessages = logmessages.split("\n")
                    for message in logmessages:
                        if len(message) > 1:
                            text = message.split("-")
                            loglevel = "Info" if text[0] == "0" else "Warning" if text[0] == "1" else "Error" if text[0] == "2" else "Unknown"
                            if text[0] == "0":
                                loglevel = "Info"
                                rowclass = ''
                            if text[0] == "1":
                                loglevel = "Warning"
                                rowclass = ' class="table-warning"'
                            if text[0] == "2":
                                loglevel = "Error"
                                rowclass = ' class="table-danger"'
                            formatted_date = datetime.datetime.fromtimestamp(int(text[1])).strftime("%Y-%m-%d %H:%M")
                            row = f"<tr{rowclass}><td>{loglevel}</td><td>{formatted_date}</td><td>{text[2]}</td></tr>"
                            logHTML.append(row)
                    logHTML = '<table class="table table-sm table-logs"><tr><th>Level</th><th>Timestamp</th><th>Message</th></tr>' + "".join(logHTML) + "</table>"

                con.commit()
        cur.close()
        con.close()

        return logHTML, 200
    except Exception as e:
        cur.close()
        con.close()

        print('Error: ' + str(e))
        return 'Error: ' + str(e), 500

@app.route('/getnote', methods=['POST'])
def getnote():
    # Connect to database
    try:
        con = sqlite3.connect(db_path)
        cur = con.cursor()
    except:
        print("Exception raised while opening SQLite DB file")
        sys.exit()

    try:
        data = request.json  # Assuming JSON payload is sent in the request body
        if not data or not isinstance(data, list):
            return 'Invalid payload, expected JSON', 400
    except Exception as e:
        return 'Error: ' + str(e), 500

    try:
        for record in data:
            servername = record.get('servername')
            clientname = record.get('clientname')

            if clientname and servername:
                sql_query = 'SELECT note FROM clients WHERE servername LIKE "%' + servername + '%" AND name LIKE "%' + clientname + '%"'
                cur.execute(sql_query)
                content = cur.fetchall()
        if content:
            cur.close()
            con.close()
            return content, 200
        else:
            cur.close()
            con.close()
            return 'No data', 404
    except Exception as e:
        cur.close()
        con.close()
        print('Error: ' + str(e))
        return 'Error: ' + str(e), 500

@app.route('/getemailrecipient', methods=['POST'])
def getemailrecipient():
    # Connect to database
    try:
        con = sqlite3.connect(db_path)
        cur = con.cursor()
    except:
        print("Exception raised while opening SQLite DB file")
        sys.exit()

    try:
        data = request.json  # Assuming JSON payload is sent in the request body
        if not data or not isinstance(data, list):
            return 'Invalid payload, expected JSON', 400
    except Exception as e:
        return 'Error: ' + str(e), 500

    try:
        result = []
        for record in data:
            servername = record.get('servername')
            clientname = record.get('clientname')
            # email = record.get('email')

            if clientname and servername:
                # sql_query = 'SELECT servername, clientname, email, freq FROM email_recipients WHERE servername LIKE "%' + servername + '%" AND clientname LIKE "%' + clientname + '%" AND email LIKE "%' + email + '%"'
                sql_query = 'SELECT servername, clientname, email, freq FROM email_recipients WHERE servername LIKE "%' + servername + '%" AND clientname LIKE "%' + clientname + '%"'
                cur.execute(sql_query)
                content = cur.fetchone()

                if content:
                    result.append({
                    'servername': content[0],
                    'clientname': content[1],
                    'email': content[2],
                    'freq': content[3]
                    })

        if result:
            cur.close()
            con.close()
            return result, 200
        else:
            cur.close()
            con.close()
            return 'No data', 404
    except Exception as e:
        cur.close()
        con.close()
        print('Error: ' + str(e))
        return 'Error: ' + str(e), 500


@app.route('/setemailrecipient', methods=['POST'])
def setemailrecipient():
    # Connect to database
    try:
        con = sqlite3.connect(db_path)
        cur = con.cursor()
    except:
        print("Exception raised while opening SQLite DB file")
        sys.exit()

    try:
        data = request.json  # Assuming JSON payload is sent in the request body
        if not data or not isinstance(data, list):
            return 'Invalid payload, expected JSON', 400
    except Exception as e:
        return 'Error: ' + str(e), 500

    try:
        for record in data:
            servernameold = record.get('servernameold')
            clientnameold = record.get('clientnameold')
            servernamenew = record.get('servernamenew')
            clientnamenew = record.get('clientnamenew')
            emailnew = record.get('emailnew')
            freqnew = record.get('freqnew')

            if servernamenew and clientnamenew and servernameold and clientnameold and emailnew and freqnew:
                # Assuming 'recipients' table has columns: servername, clientname, email, freq
                sql_query = "UPDATE email_recipients SET servername = ?, clientname = ?, email = ?, freq = ? WHERE servername = ? AND clientname = ?"
                cur.execute(sql_query, (servernamenew, clientnamenew, emailnew, freqnew, servernameold, clientnameold))
                con.commit()
        cur.close()
        con.close()
        return 'Recipient updated successfully', 200
    except Exception as e:
        cur.close()
        con.close()
        return 'Error: ' + str(e), 500


@app.route('/addemailrecipient', methods=['POST'])
def addemailrecipient():
    # Connect to database
    try:
        con = sqlite3.connect(db_path)
        cur = con.cursor()
    except:
        print("Exception raised while opening SQLite DB file")
        sys.exit()

    try:
        data = request.json  # Assuming JSON payload is sent in the request body
        if not data or not isinstance(data, list):
            return 'Invalid payload, expected JSON', 400
    except Exception as e:
        return 'Error: ' + str(e), 500

    try:
        for record in data:
            servernamenew = record.get('servernamenew')
            clientnamenew = record.get('clientnamenew')
            emailnew = record.get('emailnew')
            freqnew = record.get('freqnew')

            if servernamenew and clientnamenew and emailnew and freqnew:
                # Assuming 'recipients' table has columns: servername, clientname, email, freq
                last_sent = datetime.datetime.now()
                sql_query = "INSERT INTO email_recipients (servername, clientname, email, freq, last_sent) VALUES (?, ?, ?, ?, ?)"
                cur.execute(sql_query, (servernamenew, clientnamenew, emailnew, freqnew, last_sent))
                con.commit()
        cur.close()
        con.close()
        return 'Recipient added successfully', 200
    except Exception as e:
        cur.close()
        con.close()
        return 'Error: ' + str(e), 500

@app.route('/deleteemailrecipient', methods=['POST'])
def deleteemailrecipient():
    # Connect to database
    try:
        con = sqlite3.connect(db_path)
        cur = con.cursor()
    except:
        print("Exception raised while opening SQLite DB file")
        sys.exit()

    try:
        data = request.json  # Assuming JSON payload is sent in the request body
        if not data or not isinstance(data, list):
            return 'Invalid payload, expected JSON', 400
    except Exception as e:
        return 'Error: ' + str(e), 500

    try:
        for record in data:
            servernamenew = record.get('servername')
            clientnamenew = record.get('clientname')

            if servernamenew and clientnamenew:
                # Assuming 'recipients' table has columns: servername, clientname, email, freq
                sql_query = "DELETE FROM email_recipients WHERE servername = ? AND clientname = ?"
                cur.execute(sql_query, (servernamenew, clientnamenew))
                con.commit()
        cur.close()
        con.close()
        return 'Recipient removed successfully', 200
    except Exception as e:
        cur.close()
        con.close()
        return 'Error: ' + str(e), 500


@app.route('/deletearchived', methods=['POST'])
def deletearchived():
    # Connect to database
    try:
        con = sqlite3.connect(db_path)
        cur = con.cursor()
    except:
        print("Exception raised while opening SQLite DB file")
        sys.exit()

    try:
        data = request.json  # Assuming JSON payload is sent in the request body
        if not data or not isinstance(data, list):
            return 'Invalid payload, expected JSON', 400
    except Exception as e:
        return 'Error: ' + str(e), 500

    try:
        for record in data:
            servernamenew = record.get('servername')
            clientnamenew = record.get('clientname')

            if servernamenew and clientnamenew:
                # Assuming 'recipients' table has columns: servername, clientname, email, freq
                sql_query = "DELETE FROM clients WHERE servername = ? AND name = ? AND archived = 1"
                cur.execute(sql_query, (servernamenew, clientnamenew))
                con.commit()
        cur.close()
        con.close()
        return 'Archived client removed successfully', 200
    except Exception as e:
        cur.close()
        con.close()
        return 'Error: ' + str(e), 500

@app.route('/archive', methods=['POST'])
def archive():
    # Connect to database
    try:
        con = sqlite3.connect(db_path)
        cur = con.cursor()
    except:
        print("Exception raised while opening SQLite DB file")
        sys.exit()

    try:
        data = request.json  # Assuming JSON payload is sent in the request body
        if not data or not isinstance(data, list):
            return 'Invalid payload, expected JSON', 400
    except Exception as e:
        return 'Error: ' + str(e), 500

    try:
        for record in data:
            servername = record.get('servername')
            clientname = record.get('clientname')

            if servername and clientname:
                # Assuming 'clients' table has columns: servername, name, archived
                sql_query = "UPDATE clients SET archived = 1 WHERE servername = ? AND name = ?"
                cur.execute(sql_query, (servername, clientname))
                con.commit()
        cur.close()
        con.close()
        return 'Records archived successfully', 200
    except Exception as e:
        cur.close()
        con.close()
        return 'Error: ' + str(e), 500

@app.route('/setnote', methods=['POST'])
def setnote():
    # Connect to database
    try:
        con = sqlite3.connect(db_path)
        cur = con.cursor()
    except:
        print("Exception raised while opening SQLite DB file")
        sys.exit()

    try:
        data = request.json  # Assuming JSON payload is sent in the request body
        if not data or not isinstance(data, list):
            return 'Invalid payload, expected JSON', 400
    except Exception as e:
        return 'Error: ' + str(e), 500

    try:
        for record in data:
            note = record.get('note')
            servername = record.get('servername')
            clientname = record.get('clientname')

            if servername and clientname:
                # Assuming 'clients' table has columns: servername, name, archived
                sql_query = "UPDATE clients SET note = ? WHERE servername = ? AND name = ?"
                cur.execute(sql_query, (note, servername, clientname))
                con.commit()
        cur.close()
        con.close()
        return 'Note saved successfully', 200
    except Exception as e:
        cur.close()
        con.close()
        return 'Error: ' + str(e), 500

@app.route('/upload', methods=['POST'])
def upload():

    app.logger.debug("Upload endpoint call")

    # Connect to database
    try:
        con = sqlite3.connect(db_path)
        cur = con.cursor()
    except:
        app.logger.debug("Exception raised while opening SQLite DB file")
        sys.exit()

    # Verify API token among database record
    api_token = request.headers.get('Authorization')
    cur.execute("SELECT * FROM api_tokens WHERE api_token = ?", (api_token,))
    result = cur.fetchone()
    cur.close()
    con.close()

    # Respond with errors
    if not result:
        app.logger.debug("Unauthorized")
        return 'Unauthorized', 401

    if 'file' not in request.files:
        app.logger.debug("No file uploaded")
        return 'No file uploaded', 400

    file = request.files['file']

    if file.filename == '':
        app.logger.debug("No file selected")
        return 'No file selected', 400

    app.logger.debug(file.filename)

    # Try to import clients
    if file and "clients_" in file.filename:
        if urbackup_csv_importer.import_clients_csv(TextIOWrapper(file)):
            return 'Uploaded', 200
        else:
            app.logger.debug("Import failure " + file.filename)
            return 'Import failure', 400

    # Try to import logs
    if file and "logs_" in file.filename:
        if urbackup_csv_importer.import_logs_csv(TextIOWrapper(file)):
            return 'Uploaded', 200
        else:
            app.logger.debug("Import failure " + file.filename)
            return 'Import failure', 400

    # Try to import replica
    if file and "replica_" in file.filename:
        if urbackup_csv_importer.import_replica_json(TextIOWrapper(file)):
            return 'Uploaded', 200
        else:
            app.logger.debug("Import failure " + file.filename)
            return 'Import failure', 400

    # Try to import sessions
    if file and "sc_sessions_" in file.filename:
        if urbackup_csv_importer.import_sc_sessions_json(TextIOWrapper(file)):
            return 'Uploaded', 200
        else:
            app.logger.debug("Import failure " + file.filename)
            return 'Import failure', 400

    return 'Unknown file type', 400

@app.route('/setsessionmapping', methods=['POST'])
def setsessionmapping():
    # Connect to database
    try:
        con = sqlite3.connect(db_path)
        cur = con.cursor()
    except:
        print("Exception raised while opening SQLite DB file")
        sys.exit()

    try:
        data = request.json  # Assuming JSON payload is sent in the request body
        if not data or not isinstance(data, list):
            return 'Invalid payload, expected JSON', 400
    except Exception as e:
        return 'Error: ' + str(e), 500

    try:
        for record in data:
            sessionname = record.get('sessionname')
            servername = record.get('servername')
            clientname = record.get('clientname')

            if servername and clientname and sessionname:
                # Assuming 'recipients' table has columns: servername, clientname, email, freq
                sql_query = "UPDATE sc_sessions SET UrbackupServerName = ? WHERE GuestMachineName = ? AND Name = ?"
                cur.execute(sql_query, (servername, clientname, sessionname))
                con.commit()
                if cur.rowcount > 0: result = True
        cur.close()
        con.close()
        if result:
            return 'Session updated successfully', 200
        else:
            return 'Some error', 400
    except Exception as e:
        cur.close()
        con.close()
        return 'Error: ' + str(e), 500

@app.route('/getsessionmapping', methods=['POST'])
def getsessionmapping():
    # Connect to database
    try:
        con = sqlite3.connect(db_path)
        cur = con.cursor()
    except:
        print("Exception raised while opening SQLite DB file")
        sys.exit()

    try:
        data = request.json  # Assuming JSON payload is sent in the request body
        if not data or not isinstance(data, list):
            return 'Invalid payload, expected JSON', 400
    except Exception as e:
        return 'Error: ' + str(e), 500

    try:
        sessionname = data[0].get('sessionname')
        clientname = data[0].get('clientname')
        result = []

        if clientname and sessionname:
            # Assuming 'recipients' table has columns: servername, clientname, email, freq
            sql_query = "SELECT Name, GuestMachineName, UrbackupServerName FROM sc_sessions WHERE Name = ? AND GuestMachineName = ?"
            cur.execute(sql_query, (sessionname, clientname))
            con.commit()
            content = cur.fetchone()

            if content:
                result.append({
                    'sessionname': content[0],
                    'clientname': content[1],
                    'servername': content[2]
                })
        cur.close()
        con.close()
        if result:
            return result, 200
        else:
            return 'No data', 404
    except Exception as e:
        cur.close()
        con.close()
        return 'Error: ' + str(e), 500

@app.template_filter()
def format_datetime(value):
    result = ""
    if value:
        try:
            dateTimeObj = datetime.datetime.strptime(value, "%Y-%m-%d %H:%M:%S")
            result = dateTimeObj.strftime("%Y-%m-%d %H:%M")
        except:
            pass

        try:
            dateTimeObj = datetime.datetime.strptime(value, "%Y-%m-%d %H:%M:%S.%f")
            result = dateTimeObj.strftime("%Y-%m-%d %H:%M")
        except:
            pass
    return result

@app.template_filter()
def format_replica_state(state):
    state_mapping = {
        1: 'Running',
        2: 'Paused',
        3: 'Critical',
        4: 'Normal'
    }
    return state_mapping.get(int(state), 'Unknown')

@app.template_filter()
def format_replica_health(health):
    health_mapping = {
        1: 'Healthy',
        2: 'Warning',
        3: 'Critical'
    }
    return health_mapping.get(int(health), 'Unknown')

@app.template_filter()
def format_replica_mode(mode):
    mode_mapping = {
        2: 'Primary',
        4: 'Replica'
    }
    return mode_mapping.get(int(mode), 'Unknown')

def check_column(tbl, col):
    return

if __name__ == '__main__':
    app.run(host="0.0.0.0", debug=True)
