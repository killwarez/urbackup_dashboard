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
email_template_name = "email_tech.html"
email_template_dir = os.path.dirname(os.path.abspath(__file__)) + "//templates//"
logging.basicConfig(filename=log_path + '//record.log', level=logging.DEBUG)

def render_template(template_name, **context):
    env = Environment(loader=FileSystemLoader(searchpath=email_template_dir))
    template = env.get_template(template_name)
    return template.render(context)

# Connect to database
try:
    # con = sqlite3.connect(db_path, detect_types=sqlite3.PARSE_DECLTYPES | sqlite3.PARSE_COLNAMES)
    con = sqlite3.connect(db_path)
    cur = con.cursor()
except:
    logging.debug("Exception raised while opening SQLite DB file")
    sys.exit()

# Query emails
recipients_query = "select servername, clientname, email, last_sent, freq from email_recipients " + \
                    "where servername = '**ADMIN**' and clientname = '**ADMIN**' " + \
                    "order by servername, clientname " + \
                    "limit 1"
recipients = cur.execute(recipients_query).fetchall()

if not recipients:
   logging.debug("Nobody to send tech alerts too. Exiting.")
   exit()

for recipient in recipients:
    cur = con.cursor()

    servername = recipient[0]
    clientname = recipient[1]
    emls = recipient[2]
    eml = re.split(';|,| ', recipient[2])
    last_sent = recipient[3]
    freq = recipient[4]

    clients = cur.execute('''
                          select 
                            servername, name, lastseen, lastbackup_file, lastbackup_image, lastbackup_file_status, lastbackup_image_status, errors, 
                            case when servername LIKE '%internet%' then 'internet' else case when servername LIKE '%local%' then 'local' else 'unknown' end end as location 
                          from clients 
                          where 
                            (archived = 0) AND (lastbackup_image_status = "No recent backup" or lastbackup_file_status = "No recent backup" or errors <> 0) 
                          order by location, servername, name 
                          ''').fetchall()

    if not clients:
      #  print('No clients with outdated backup found for recipient:')
      #  print(recipient)
       continue

    # print(clients)

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
    if last_sent is None:
       last_sent = datetime.datetime.fromtimestamp(0)
    else:
       format = "%Y-%m-%d %H:%M:%S.%f"
       last_sent = datetime.datetime.strptime(last_sent, format)
    if (last_sent + delta < datetime.datetime.now()):
      try:
        email.send(
          sender=urbackup_dashboard_email_params.smtp_username,
          receivers=eml,
          subject=urbackup_dashboard_email_params.email_subject_tech,
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

cur.close()
con.close()