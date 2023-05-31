import csv, sqlite3
import glob
import sys, os

csv_files_path_mask = os.path.dirname(os.path.abspath(__file__)) + "\\csv\\clients_*.csv"
db_path = os.path.dirname(os.path.abspath(__file__)) + "\\db\\urbackup_dashboard.db"

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

    return False

# DB columns addition
def create_column(table_name, column_name):
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    # Execute ALTER TABLE statement to add the new column
    cursor.execute(f"ALTER TABLE {table_name} ADD COLUMN {column_name} TEXT")

    conn.commit()
    conn.close()

# Import CSV structure to DB
def import_csv(csv_data):
    # csv.DictReader uses first line in file for column headings by default
    dict_csv = csv.DictReader(csv_data) # comma is default delimiter
    csv_with_errors = True if 'errors' in dict_csv.fieldnames else False

    # open db
    try:
        con = sqlite3.connect(db_path)
        cur = con.cursor()
    except:
        print("Exception raised opening SQLite DB file")
        sys.exit()

    # Import CSV data
    try:
        for row_csv in dict_csv:
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
                    row_csv["servername"],
                    row_csv["name"]
                ]

            sql_query_str = "UPDATE clients SET lastseen = ?, lastbackup_file = ?, lastbackup_image = ?, lastbackup_file_status = ?, lastbackup_image_status = ?, errors = ?, warnings = ?, client_ver = ? WHERE servername = ? AND name = ?"
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
                        row_csv["client_ver"]
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
                        ""
                    ]
                
                cur.executemany("INSERT INTO clients (servername, name, lastseen, lastbackup_file, lastbackup_image, lastbackup_file_status, lastbackup_image_status, errors, warnings, client_ver) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?);", [dict_clients])
    
    except sqlite3.Error as er:
        print("Exception raised while importing CSV file " + filename + " to DB")
        con.commit()
        con.close()
        return(False)
    else:
        con.commit()
        con.close()
        return(True)

if __name__ == '__main__':
    # Check and add columns to DB
    table_name = 'clients'
    column_names = ['errors','warnings','client_ver']
    for column_name in column_names:
        if not check_column_exists(table_name, column_name):
            create_column(table_name, column_name)

    # Collect filenames for import
    csvfiles = []
    try:
        for file in glob.glob(csv_files_path_mask):
            csvfiles.append(file)
    except:
        print("Exception raised while enumerating CSV files")
        sys.exit()
    else:
        if csvfiles == []:
            sys.exit()

    # Read filenames array and import csv files to table adding server name
    for filename in csvfiles:
        # Read csv file
        try:
            with open(filename,'r') as csv_file:
                import_csv(csv_file)
        except:
            pass
        else:
            os.remove(filename)