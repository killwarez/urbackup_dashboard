from prettytable import PrettyTable
import logging
import sqlite3, os, sys
from jinja2 import Environment, FileSystemLoader
from redmail import EmailSender
import urbackup_dashboard_email_params
from flask import render_template
import datetime
import re

log_path = os.path.dirname(os.path.abspath(__file__)) + "//log"
db_path = os.path.dirname(os.path.abspath(__file__)) + "//db//urbackup_dashboard.db"
email_template_name = "email_user.html"
email_template_dir = os.path.dirname(os.path.abspath(__file__)) + "//templates//"
logging.basicConfig(filename=log_path + '//record.log', level=logging.DEBUG)

def ppt(data):
    table = PrettyTable()

    # Add data to the table
    for client in data:
        table.add_row(client)

    # Print the table
    print(table)

def render_template(template_name, **context):
    env = Environment(loader=FileSystemLoader(searchpath=email_template_dir))
    template = env.get_template(template_name)
    return template.render(context)

# Connect to database
try:
    con = sqlite3.connect(db_path, detect_types=sqlite3.PARSE_DECLTYPES | sqlite3.PARSE_COLNAMES)
    cur = con.cursor()
except:
    logging.debug("Exception raised while opening SQLite DB file")
    sys.exit()

# Query emails
recipients_query = "select servername, clientname, email, last_sent, freq from email_recipients " + \
                    "where clientname <> '' and clientname is not null and servername <> '**ALL**' " + \
                    "order by servername, clientname"
recipients = cur.execute(recipients_query).fetchall()

if not recipients:
   logging.debug("Nobody to send user alerts too. Exiting.")
   exit()

for recipient in recipients:
    cur = con.cursor()

    servername = recipient[0]
    clientname = recipient[1]
    emls = recipient[2]
    eml = re.split(';|,| ', recipient[2])
    last_sent = recipient[3]
    freq = recipient[4]

    if clientname == "**ADMIN**":
       continue

    if clientname == "**ALL**":
        clients = cur.execute(f'''
            select 
                clients.name, 
                case when lastbackup_file_status = 'No recent backup' OR lastbackup_image_status = 'No recent backup' then 'No recent backup' else '' end as lastbackup_status 
            from clients 
            where (lastbackup_image_status = "No recent backup" or lastbackup_file_status = "No recent backup") AND servername = '{servername}' 
            order by clients.name;
            ''').fetchall()
    if not clients:
        print('No clients with outdated backup found for recipient:')
        print(recipient)
        continue
    else:
        for index, client in enumerate(clients):
            session = cur.execute(f'''
                select 
                    sc_sessions.name 
                from sc_sessions 
                where (sc_sessions.GuestMachineName = '{client[0]}' AND sc_sessions.UrbackupServerName = '{servername}') 
                ''').fetchone()
            if session:
                client_list = list(clients[index])
                client_list[0] = session[0]
                client_tuple = tuple(client_list)
                clients[index] = client_tuple
                continue
            session = cur.execute(f'''
                select
                    name, count(name)
                from sc_sessions
                where GuestMachineName = '{client[0]}' collate nocase
            ''').fetchone()
            if session and session[1] == 1:
                client_list = list(clients[index])
                client_list[0] = session[0]
                client_tuple = tuple(client_list)
                clients[index] = client_tuple
                continue
        # ppt(clients)

    html = render_template(email_template_name,clients=clients)

    # Send the email
    email = EmailSender(
      host=urbackup_dashboard_email_params.smtp_host,
      port=urbackup_dashboard_email_params.smtp_port,
      username=urbackup_dashboard_email_params.smtp_username,
      password=urbackup_dashboard_email_params.smtp_password,
      use_starttls=True,
    )

    delta = datetime.timedelta(minutes=int(freq))
    if (last_sent + delta < datetime.datetime.now()):
      try:
        email.send(
          sender=urbackup_dashboard_email_params.smtp_username,
          receivers=eml,
          subject=urbackup_dashboard_email_params.email_subject_user,
          html=html,
        )
      except Exception as e:
        logging.debug(e)
      else:
        last_updated = datetime.datetime.now()

        update_query = f"UPDATE email_recipients SET last_sent = ? WHERE servername = ? AND clientname = ? AND email = ?"
        update_params = (last_updated, servername, clientname, emls)

        cur.execute(update_query, update_params)
        con.commit()

        logging.debug(f"Last sent = {last_updated}, servername = {servername}, clientname = {clientname}, email = {emls}")
    # else:
    #    print("It's not sending time yet")

cur.close()
con.close()