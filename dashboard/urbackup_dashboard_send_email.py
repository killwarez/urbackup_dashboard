import sqlite3, os, sys
from jinja2 import Template
from redmail import EmailSender
import urbackup_dashboard_email_params

db_path = os.path.dirname(os.path.abspath(__file__)) + "\\db\\urbackup_dashboard.db"
email_template_name = "notification_email.html"
email_template_dir = os.path.dirname(os.path.abspath(__file__)) + "\\templates\\"

# Connect to database
try:
    con = sqlite3.connect(db_path)
    cur = con.cursor()
except:
    print("Exception raised while opening SQLite DB file")
    sys.exit()

# Query data
clients = cur.execute(
    'select servername, name, lastseen, lastbackup_image, lastbackup_image_status, errors, warnings from clients ' + \
    'where (errors > 0 or warnings > 0) ' + \
    'order by lastseen').fetchall()

# Create then render template
template = Template(urbackup_dashboard_email_params.email_body)
html = template.render(data=clients)

# Send the email
email = EmailSender(
  host=urbackup_dashboard_email_params.smtp_host,
  port=urbackup_dashboard_email_params.smtp_port,
  username=urbackup_dashboard_email_params.smtp_username,
  password=urbackup_dashboard_email_params.smtp_password,
  use_starttls=True,
)

email.send(
  sender=urbackup_dashboard_email_params.smtp_username,
  receivers=urbackup_dashboard_email_params.email_recipients,
  subject=urbackup_dashboard_email_params.email_subject,
  html=html,
)