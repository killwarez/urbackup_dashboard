import csv, sqlite3
import glob, re
import sys, os
import traceback

csv_files_path_mask = os.path.dirname(os.path.abspath(__file__)) + "\\csv\\clients_*.csv"
db_path = os.path.dirname(os.path.abspath(__file__)) + "\\db\\urbackup_dashboard.db"

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

# enum files by mask
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

# open db
try:
    con = sqlite3.connect(db_path)
    cur = con.cursor()
except:
    print("Exception raised opening SQLite DB file")
    sys.exit()

# read filenames array and import csv files to table adding server name
for filename in csvfiles:

    # get servername from filename
    m = re.search('.+clients_(.+)\.csv', filename)
    if m:
        servername = m.group(1)

    #read csv file
    try:
        with open(filename,'r') as csv_file:
            # csv.DictReader uses first line in file for column headings by default
            dict_csv = csv.DictReader(csv_file) # comma is default delimiter

            for row_csv in dict_csv:
                dict_clients = [
                    row_csv["lastseen"],
                    row_csv["lastbackup"],
                    row_csv["lastbackup_image"],
                    strstatus(row_csv["file_ok"]),
                    strstatus(row_csv["image_ok"]),
                    servername,
                    row_csv["name"]
                ]
                sql_query_str = "UPDATE clients SET lastseen = ?, lastbackup_file = ?, lastbackup_image = ?, lastbackup_file_status = ?, lastbackup_image_status = ? WHERE servername = ? AND name = ?"
                cur.executemany(sql_query_str, [dict_clients])

                if cur.rowcount < 1:
                    dict_clients = [
                        servername,
                        row_csv["name"],
                        row_csv["lastseen"],
                        row_csv["lastbackup"],
                        row_csv["lastbackup_image"],
                        strstatus(row_csv["file_ok"]),
                        strstatus(row_csv["image_ok"])
                    ]
                    cur.executemany("INSERT INTO clients (servername, name, lastseen, lastbackup_file, lastbackup_image, lastbackup_file_status, lastbackup_image_status) VALUES (?, ?, ?, ?, ?, ?, ?);", [dict_clients])

    except sqlite3.Error as er:
        #print('SQLite error: %s' % (' '.join(er.args)))
        #print("Exception class is: ", er.__class__)
        #print('SQLite traceback: ')
        #exc_type, exc_value, exc_tb = sys.exc_info()
        #print(traceback.format_exception(exc_type, exc_value, exc_tb))
        print("Exception raised while importing CSV file " + filename + " to DB")
        sys.exit()
    else:
        os.remove(filename)

con.commit()
con.close()