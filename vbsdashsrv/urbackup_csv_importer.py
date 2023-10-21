import logging
import csv, sqlite3
import sys, os
import json

csv_files_path_mask = os.path.dirname(os.path.abspath(__file__)) + "//csv//clients_*.csv"
db_path = os.path.dirname(os.path.abspath(__file__)) + "//db//urbackup_dashboard.db"
log_path = os.path.dirname(os.path.abspath(__file__)) + "//log"
json_path = os.path.dirname(os.path.abspath(__file__)) + "//json//"

if not os.path.exists(log_path):
    os.makedirs(log_path)

if not os.path.exists(json_path):
    os.makedirs(json_path)

logging.basicConfig(filename=log_path + '//record.log', level=logging.DEBUG)

# Compose text status from code
def strstatus(status):
    match status:
        case "0":
            return "No recent backup"
        case "1":
            return "Ok"
        case "-1":
            return "Disabled"
        case _:
            return "Unknown status"

# DB columns existence check
def check_column_exists(table_name, column_name):
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    # Execute PRAGMA statement to fetch table info
    cursor.execute(f"PRAGMA table_info({table_name})")
    columns = cursor.fetchall()

    # Check if the column exists in the table
    for column in columns:
        if column[1] == column_name:
            return True

    cursor.close()
    conn.close()

    return False

# DB columns addition
def create_column(table_name, column_name):
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    # Execute ALTER TABLE statement to add the new column
    cursor.execute(f"ALTER TABLE {table_name} ADD COLUMN {column_name} TEXT")

    conn.commit()
    cursor.close()
    conn.close()

# Import CSV structure to DB
def import_clients_csv(csv_data):
    # csv.DictReader uses first line in file for column headings by default
    dict_csv = csv.DictReader(csv_data) # comma is default delimiter
    csv_with_errors = True if 'logid' in dict_csv.fieldnames else False

    # open db
    try:
        con = sqlite3.connect(db_path)
        cur = con.cursor()
    except:
        logging.debug("Exception raised opening SQLite DB file")
        cur.close()
        con.close()
        sys.exit()

    # Import CSV data
    try:
        for row_csv in dict_csv:
            if row_csv["name"].startswith("##restore##"):
                continue
            if csv_with_errors:
                dict_clients = [
                    row_csv["lastseen"],
                    row_csv["lastbackup"],
                    row_csv["lastbackup_image"],
                    strstatus(row_csv["file_ok"]),
                    strstatus(row_csv["image_ok"]),
                    row_csv["errors"],
                    row_csv["warnings"],
                    row_csv["client_ver"],
                    row_csv["logid"],
                    row_csv["lastseen"],
                    row_csv["servername"],
                    row_csv["name"]
                ]
            else:
                dict_clients = [
                    row_csv["lastseen"],
                    row_csv["lastbackup"],
                    row_csv["lastbackup_image"],
                    strstatus(row_csv["file_ok"]),
                    strstatus(row_csv["image_ok"]),
                    "",
                    "",
                    "",
                    "",
                    row_csv["lastseen"],
                    row_csv["servername"],
                    row_csv["name"]
                ]

            sql_query_str = "UPDATE clients SET lastseen = ?, lastbackup_file = ?, lastbackup_image = ?, lastbackup_file_status = ?, lastbackup_image_status = ?, errors = ?, warnings = ?, client_ver = ?, logid = ?,  archived = iif(lastseen < ?, 0, archived) WHERE servername = ? AND name = ?"
            cur.executemany(sql_query_str, [dict_clients])

            if cur.rowcount < 1:
                if csv_with_errors:
                    dict_clients = [
                        row_csv["servername"],
                        row_csv["name"],
                        row_csv["lastseen"],
                        row_csv["lastbackup"],
                        row_csv["lastbackup_image"],
                        strstatus(row_csv["file_ok"]),
                        strstatus(row_csv["image_ok"]),
                        row_csv["errors"],
                        row_csv["warnings"],
                        row_csv["client_ver"],
                        row_csv["logid"]
                    ]
                else:
                    dict_clients = [
                        row_csv["servername"],
                        row_csv["name"],
                        row_csv["lastseen"],
                        row_csv["lastbackup"],
                        row_csv["lastbackup_image"],
                        strstatus(row_csv["file_ok"]),
                        strstatus(row_csv["image_ok"]),
                        "",
                        "",
                        "",
                        ""
                    ]

                cur.executemany("INSERT INTO clients (servername, name, lastseen, lastbackup_file, lastbackup_image, lastbackup_file_status, lastbackup_image_status, errors, warnings, client_ver, logid) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?);", [dict_clients])
        con.commit()
        cur.close()

    except sqlite3.Error as er:
        logging.debug("Exception raised while importing clients CSV file to DB")
        logging.debug(er)
        return(False)
    else:
        return(True)
    finally:
        con.close()


def import_logs_csv(csv_data):
    # csv.DictReader uses first line in file for column headings by default
    dict_csv = csv.DictReader(csv_data) # comma is default delimiter

    # open db
    try:
        con = sqlite3.connect(db_path)
        cur = con.cursor()
    except:
        logging.debug("Exception raised opening SQLite DB file")
        sys.exit()

    # Import CSV data
    try:
        for row_csv in dict_csv:
                dict_logs = [
                    row_csv["logmessages"],
                    row_csv["servername"],
                    row_csv["logid"]
                ]
                sql_query_str = "UPDATE logs SET logmessages = ? WHERE servername = ? AND logid = ?"
                cur.executemany(sql_query_str, [dict_logs])

                if cur.rowcount < 1:
                    dict_logs = [
                        row_csv["servername"],
                        row_csv["logid"],
                        row_csv["logmessages"]
                    ]
                    cur.executemany("INSERT INTO logs (servername, logid, logmessages) VALUES (?, ?, ?);", [dict_logs])
        con.commit()
        cur.close()
        con.close()
        return True

    except sqlite3.Error as er:
        logging.debug("Exception raised while importing logs CSV file to DB")
        logging.debug(er)
        con.commit()
        cur.close()
        con.close()
        return False

def import_replica_json(json_data):

    db_path = os.path.dirname(os.path.abspath(__file__)) + "//db//urbackup_dashboard.db"
    data = json.load(json_data)

    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
    except:
        logging.debug("Exception raised opening SQLite DB file")
        sys.exit()

    try:
        for entry in data:
            # Try to update the record, if it already exists
            cursor.execute("UPDATE replica SET State=?, Health=?, Mode=? WHERE VMName=? AND PrimaryServer=? AND ReplicaServer=?",
                (entry['State'], entry['Health'], entry['Mode'], entry['VMName'], entry['PrimaryServer'], entry['ReplicaServer']))

            # If nothing was updated, then add record
            if cursor.rowcount == 0:
                    cursor.execute("INSERT OR IGNORE INTO replica (VMName, State, Health, Mode, PrimaryServer, ReplicaServer) VALUES (?, ?, ?, ?, ?, ?)",
                        (entry['VMName'], entry['State'], entry['Health'], entry['Mode'], entry['PrimaryServer'], entry['ReplicaServer']))

        conn.commit()
    except sqlite3.Error as er:
        # Commit the changes and close the connection
        logging.debug("Exception raised while importing replica JSON file to DB")
        logging.debug(er)
        return(False)
    else:
        return(True)
    finally:
        cursor.close()
        conn.close()

def import_sc_sessions_json(json_data):

    db_path = os.path.dirname(os.path.abspath(__file__)) + "//db//urbackup_dashboard.db"
    data = json.load(json_data)

    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
    except:
        logging.debug("Exception raised opening SQLite DB file")
        sys.exit()

    try:
        for entry in data:
            # Try to update the record, if it already exists
            # INSERT INTO phonebook(name,phonenumber) VALUES('Alice','704-555-1212') ON CONFLICT(name) DO UPDATE SET phonenumber=excluded.phonenumber;

            cursor.execute("INSERT OR IGNORE INTO sc_sessions (Name,GuestMachineName) VALUES (?,?)", (entry['Name'], entry['GuestMachineName']))
            # cursor.execute("INSERT INTO sc_sessions (Name,GuestMachineName) VALUES (?,?) " + \
            #                "ON CONFLICT(GuestMachineName) DO UPDATE SET Name = ? " + \
            #                "WHERE Override < 1", (entry['Name'], entry['GuestMachineName'], entry['Name']))
            conn.commit()

    except sqlite3.Error as er:
        # Commit the changes and close the connection
        logging.debug("Exception raised while importing SC sessions JSON file to DB")
        logging.debug(er)
        return False
    else:
        return True
    finally:
        cursor.close()
        conn.close()

if __name__ == '__main__':
    # Check and add columns to DB
    table_name = 'clients'
    column_names = ['errors','warnings','client_ver']
    for column_name in column_names:
        if not check_column_exists(table_name, column_name):
            create_column(table_name, column_name)