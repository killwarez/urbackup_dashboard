# Git pull test
#
#
#


import platform, csv, os, glob, sys, requests, urbackup_api, urllib3, json
from datetime import datetime
import urbackup_export_clients_params

def export_clients_csv(server_urbackup):
    csv_clients_body = []
    csv_logs_body = []

    for client in clients:

        # Request errors and warnings
        clientid = client["id"]
        client_name = client["name"]
        logs_metrics = server_urbackup._get_json("logs", {"filter": clientid, "ll": 0})
        # with open(client["name"] + ".json", 'w') as file: json.dump(logs_metrics, file)
        # print(json.dumps(logs_metrics, indent=2))
        try:
            if logs_metrics["error"]:
                print("Error reaching logs for client: " + client_name)
                # continue
        except:
            pass

        # Compose tri-state result
        if 'file_disabled' in client:
            if client['file_disabled']:
                file_ok = '-1'
        else:
            file_ok = "1" if client["file_ok"] else "0"
        if 'image_disabled' in client:
            if client['image_disabled']:
                image_ok = '-1'
        else:
            image_ok = "1" if client["image_ok"] else "0"

        # Collect errors, warnings and log messages
        errors = 0
        logid = 0
        try:
            if logs_metrics["logs"][0]["errors"] > 0:
                errors = logs_metrics["logs"][0]["errors"]
                logid = logs_metrics["logs"][0]["id"]
        except:
            print("Error getting client " + client_name + " at " + servername + " errors logged value")
            pass

        warnings = 0
        try:
            if logs_metrics["logs"][0]["warnings"] > 0:
                warnings = logs_metrics["logs"][0]["warnings"]
                logid = logs_metrics["logs"][0]["id"]
        except:
            print("Error getting client " + client_name + " at " + servername + " warnings logged value")
            pass

        logs_messages = ""
        if logid:
            logs_messages = server_urbackup._get_json("logs", {"logid": logid})
            logs_messages = logs_messages["log"]["data"]
        # print(logs_message)
        # print(logid)
        # with open("dump.log", 'w') as file: json.dump(logs_metrics, file)

        lastseen = ""
        try:
            if client["lastseen"]:
                lastseen = datetime.fromtimestamp(client["lastseen"])
        except:
            pass

        lastbackup = ""
        try:
            if client["lastbackup"]:
                lastbackup = datetime.fromtimestamp(client["lastbackup"])
        except:
            pass

        lastbackup_image = ""
        try:
            if client["lastbackup_image"]:
                lastbackup_image = datetime.fromtimestamp(client["lastbackup_image"])
        except:
            pass


        # Compose array rows
        csv_clients_body.append({"servername": servername,
                        "name": client_name,
                        "lastseen": lastseen,
                        "lastbackup": lastbackup,
                        "lastbackup_image": lastbackup_image,
                        "file_ok": file_ok,
                        "image_ok": image_ok,
                        "errors": str(errors),
                        "warnings": str(warnings),
                        "client_ver": 4,
                        "logid": logid})

        if logid: csv_logs_body.append({"servername": servername,
                                        "logid": logid,
                                        "logmessages": logs_messages})


    csv_clients_file = csv_files_path + "clients_" + servername + ".csv"
    csv_clients_header = csv_clients_body[0].keys()

    with open(csv_clients_file, "w", newline="") as file:
        writer = csv.DictWriter(file, fieldnames=csv_clients_header)
        writer.writeheader()
        writer.writerows(csv_clients_body)

    if len(csv_logs_body):
        csv_logs_file = csv_files_path + "logs_" + servername + ".csv"
        csv_logs_header = csv_logs_body[0].keys()

        with open(csv_logs_file, "w", newline="") as file:
            writer = csv.DictWriter(file, fieldnames=csv_logs_header)
            writer.writeheader()
            writer.writerows(csv_logs_body)

def upload_csv():
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

        # Open the CSV file
        with open(filename, 'r') as file:
            # Create headers with the API token
            headers = {'Authorization': urbackup_export_clients_params.api_token}

            # PEM cert path
            pem_cert_path = os.path.dirname(os.path.abspath(__file__)) + "//certificate.pem"
            if os.path.exists(pem_cert_path) and os.path.isfile(pem_cert_path):
                pass
            else:
                print("Certificate path incorrect " + pem_cert_path)
                exit()

            # Create the POST request with the file
            files = {'file': file}
            try:
                urllib3.disable_warnings()
                response = requests.post(urbackup_export_clients_params.server_dashboard, files=files, headers=headers, cert=pem_cert_path, verify=False)
            except requests.exceptions.RequestException as e:
                print('Cannot connect to dashboard host ' + urbackup_export_clients_params.server_dashboard)
                print(e)
                return
            else:
                # Check if the request was successful
                if response.status_code != requests.codes.ok:
                    print(f'Upload failed with error: {response.status_code}')
                    print(response.text)

        os.remove(filename)

if __name__ == '__main__':

    for server_id, server in urbackup_export_clients_params.servers.items():
        server_urbackup = urbackup_api.urbackup_server(server["address"], server["user"], server["password"])

        if not server["name"]:
            servername = platform.node()
        else:
            servername = server["name"]

        clients = server_urbackup.get_status()
        csv_files_path = os.path.dirname(os.path.abspath(__file__)) + "//csv//"

        try:
            if os.path.exists(csv_files_path):
                if not os.path.isdir(csv_files_path):
                    print("Path isn't directory: " + csv_files_path)
                    exit()
            else:
                os.makedirs(csv_files_path)
        except:
            print("Error checking or creating directory at " + csv_files_path)
            exit()

        csv_files_path_mask = csv_files_path + "*.csv"

        export_clients_csv(server_urbackup)
        upload_csv()