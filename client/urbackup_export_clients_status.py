import platform, csv, os, glob, sys, requests
from datetime import datetime
import urbackup_export_clients_params

update_path = os.path.dirname(os.path.abspath(__file__)) + "\\" + "urbackup_export_clients_status_new.py"
old_client_path = os.path.dirname(os.path.abspath(__file__)) + "\\" + "urbackup_export_clients_status_old.py"

url_upload = urbackup_export_clients_params.server_dashboard + 'upload'
url_latest_version_check = urbackup_export_clients_params.server_dashboard + 'latest_version'
url_latest_version_get = urbackup_export_clients_params.server_dashboard + 'get_latest_version'

csv_body = []
servername = platform.node()
clients = urbackup_export_clients_params.server_urbackup.get_status()
csv_files_path = os.path.dirname(os.path.abspath(__file__)) + "\\csv\\"
csv_files_path_mask = csv_files_path + "clients_*.csv"

def export_clients_csv():
    for client in clients:
        # print(client["name"])
        # pprint(client)
        
        # Request errors and warnings
        clientid = client["id"]
        logs_metrics = urbackup_export_clients_params.server_urbackup._get_json("logs", {"filter": clientid, "ll": 0})

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
        
        # Compose array row
        csv_body.append({"servername": servername, 
                        "name": client["name"], 
                        "lastseen": "0" if client["lastseen"] == 0 else datetime.fromtimestamp(client["lastseen"]),
                        "lastbackup": "0" if client["lastbackup"] == 0 else datetime.fromtimestamp(client["lastbackup"]),
                        "lastbackup_image": "0" if client["lastbackup_image"] == 0 else datetime.fromtimestamp(client["lastbackup_image"]),
                        "file_ok": file_ok,
                        "image_ok": image_ok,
                        "errors": str(logs_metrics["logs"][0]["errors"]),
                        "warnings": str(logs_metrics["logs"][0]["warnings"]),
                        "client_ver": get_client_version()})

    now = datetime.now()
    csv_file = csv_files_path + "clients_" + servername + ".csv"
    csv_header = csv_body[0].keys()

    with open(csv_file, "w", newline="") as file:
        writer = csv.DictWriter(file, fieldnames=csv_header)
        writer.writeheader()
        writer.writerows(csv_body)

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

            # Create the POST request with the file
            files = {'file': file}
            try:
                response = requests.post(url_upload, files=files, headers=headers)
            except:
                print('Cannot connect to dashboard host ' + urbackup_export_clients_params.server_dashboard)
                return
            else:
                # Check if the request was successful
                if response.status_code != requests.codes.ok:
                    print('Upload failed with error:')
                    print(response.status_code)
                    
        os.remove(filename)

def get_client_version():
    return 2

def check_client_update():
    result = False

    # Create headers with the API token
    headers = {'Authorization': urbackup_export_clients_params.api_token}

    # Create the POST request with the file
    response = requests.get(url_latest_version_check, headers=headers)

    # Check if the request was successful
    if response.status_code != requests.codes.ok:
        print('Latest version check failed:')
        print(response.status_code)
    else:
        print('Update version: ' + str(int(response.text)))
        print('Current version: ' + str(get_client_version()))
        if int(response.text) > get_client_version(): result = True
    
    return result

def get_client_update():
    # Create headers with the API token
    headers = {'Authorization': urbackup_export_clients_params.api_token}

    # Create the POST request with the file
    response = requests.get(url_latest_version_get, headers=headers)

    # Check if the request was successful
    if response.status_code == requests.codes.ok:
        # Get the filename from the 'Content-Disposition' header
        #filename = response.headers.get('Content-Disposition').split('=')[1]

        # Save the file locally
        with open(update_path, 'wb') as file:
            file.write(response.content)
        print(f'File "{update_path}" downloaded successfully.')
    else:
        print('Download failed with error:')
        print(response.text)

if __name__ == '__main__':
    try:
        update_available = check_client_update()
    except:
        pass
    else:
        if update_available: get_client_update()

    if os.path.isfile(update_path):
        os.rename(os.path.abspath(__file__),old_client_path)
        os.rename(update_path, os.path.abspath(__file__))

    export_clients_csv()
    upload_csv()