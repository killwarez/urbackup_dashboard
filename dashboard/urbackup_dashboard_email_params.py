smtp_host = 'smtp.server.address'
smtp_port = 587
smtp_username = 'username@server.com'
smtp_password = 'password'

email_recipients = ['recipient@server.com']
email_subject = 'UrBackup Dashboard Notification'

email_body = """
    <html>
        <head>
            <title>My Email</title>
        </head>
        <body>
            <h3>UrBackup Dashboard Error and Warnings</h1>
            <table id="data" style="border: 1px solid black; border-collapse: collapse;">
            <thead style="border: 1px solid black; padding: 8px 16px;">
                <tr>
                    <th style="border: 0px solid black; padding: 8px 16px;">Server name</th>
                    <th style="border: 0px solid black; padding: 8px 16px;">Computer name</th>
                    <th style="border: 0px solid black; padding: 8px 16px;">Last seen</th>
                    <th style="border: 0px solid black; padding: 8px 16px;">Last image backup</th>
                    <th style="border: 0px solid black; padding: 8px 16px;">Image backup result</th>
                    <th style="border: 0px solid black; padding: 8px 16px;">Errors</th>
                    <th style="border: 0px solid black; padding: 8px 16px;">Warnings</th>
                </tr>
            </thead>
            <tbody>
            {% for row in data %}
                <tr>
                    <td style="border: 1px solid black; padding: 8px 16px;">{{ row[0] }}</td>
                    <td style="border: 1px solid black; padding: 8px 16px;">{{ row[1] }}</td>
                    <td style="border: 1px solid black; padding: 8px 16px;">{{ row[2] }}</td>
                    <td style="border: 1px solid black; padding: 8px 16px;">{{ row[3] }}</td>
                    <td style="border: 1px solid black; padding: 8px 16px; text-align: center">{{ row[4] }}</td>
                    <td style="border: 1px solid black; padding: 8px 16px; text-align: center">{{ row[5] }}</td>
                    <td style="border: 1px solid black; padding: 8px 16px; text-align: center">{{ row[6] }}</td>
                </tr>
            {% endfor %}
            </tbody>
        </table>
    </body>
  </html>"""
