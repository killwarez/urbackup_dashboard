# UrBackup cumulative dashboard

Set of scripts to collect clients backup status from several UrBackup servers and display overall information at one page.

Script **export_clients.sh** used to save clients backup status to CSV file. Used information from Clients table of UrBackup database. Exported records upload to your FTP server where other scripts will run.

File **urbackup-csv-importer.py** will parse CSVs and store status data to database.

Script **urbackup-dashboard-server.py** will get and display clients backup status as data table in browser. Support sorting, filtering, status highlights, paging.

## Install

1. Configure FTP client credentials and location in **export_clients.sh** file, then add it to crontab to run periodically

2. On server machine run **urbackup-csv-importer.py** in repeat to store uploaded CSVs in database with cron or task manager.

3. **urbackup-dashboard-server.py** is Flask application, deploy it to production using [guide](https://flask.palletsprojects.com/en/2.0.x/deploying/) or run it in your test environment.

## Python dependencies

Used python libraries: `csv, sqlite3, glob, re, sys, os, traceback, flask`