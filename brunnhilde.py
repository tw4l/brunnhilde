#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""

Brunnhilde - A companion to Richard Lehane's Seigfried 
(www.itforarchivists.com/siegfried)

Brunnhilde runs Siegfried against a specified directory, loads the results
into a sqlite3 database, and queries the database to generate aggregate
reports (HTML and CSV) to aid in triage, arrangement, and description of digital archives.

Brunnhilde takes two arguments:

1. path of directory to scan
2. basename for reports (e.g. accession number or other identifier)

'python brunnhilde.py directory basename'

Tested with Python 2.7

The MIT License (MIT)
Copyright (c) 2016 Tim Walsh

"""

import csv
import errno
import os
import sqlite3
import subprocess
import sys

walk_dir = sys.argv[1]
filename = sys.argv[2]

def openHTML(in_name):
	html_file.write("<!DOCTYPE html>")
	html_file.write("<html lang='en'>")
	html_file.write("<head>")
	html_file.write("<title>Brunnhilde report for: %s</title>" % in_name)
	html_file.write("<meta http-equiv='Content-Type' content='text/html; charset=utf-8'>")
	html_file.write("</head>")
	html_file.write("<body max>")
	html_file.write('<h1>Brunnhilde report</h1>')
	html_file.write('<h2>Content scanned: %s</h2>' % in_name)

def writeHTML(header):
	with open(path, 'rb') as csv_report:
		# count lines and then return to start of file
		numline = len(csv_report.readlines())
		csv_report.seek(0)

		r = csv.reader(csv_report)

		if numline > 1: #aka more rows than just header
			html_file.write('<h2>%s</h2>' % header)
			html_file.write('<table border=".5">')

			# generate table
			for row in r:
				# write data
				html_file.write('<tr>')
				for column in row:
					html_file.write('<td>' + column + '</td>')
				html_file.write('</tr>')

			html_file.write('</table>')

		else:
			html_file.write('<h2>%s</h2>' % header)
			html_file.write('None found.')

def closeHTML():
	html_file.write("</body>")
	html_file.write("</html>")

def sqlite_to_csv(sql, path, header):
	with open(path, 'wb') as format_report:
		w = csv.writer(format_report)
		w.writerow(header)
		for row in cursor.execute(sql):
			w.writerow(row)

# create directories
current_dir = os.getcwd()
tablename = os.path.splitext(filename)[0]
# create directory for reports
report_dir = os.path.join(current_dir, '%s' % tablename)
try:
	os.makedirs(report_dir)
except OSError as exception:
	if exception.errno != errno.EEXIST:
		raise
# create subdirectory for CSV reports
csv_dir = os.path.join(report_dir, 'CSVs')
try:
	os.makedirs(csv_dir)
except OSError as exception:
	if exception.errno != errno.EEXIST:
		raise

# run siegfried against specified directory
print("Running Siegfried against %s. This may take a few minutes." % walk_dir)
siegfried_command = "sf -z -csv -hash md5 %s > %s" % (walk_dir, os.path.join(report_dir, filename))
subprocess.call(siegfried_command, shell=True)
print("Characterization complete. Processing results.")

# open sqlite db and start processing
db = os.path.join(report_dir, os.path.splitext(filename)[0]) + '.sqlite'
conn = sqlite3.connect(db)
conn.text_factory = str  # allows utf-8 data to be stored

cursor = conn.cursor()

# import modified csv file into sqlite db
# https://tentacles666.wordpress.com/2014/11/14/python-creating-a-sqlite3-database-from-csv-files/
with open(os.path.join(report_dir, filename), 'rb') as f:
	reader = csv.reader(f)

	header = True
	for row in reader:
		if header:
			# gather column names from first row of csv
			header = False

			sql = "DROP TABLE IF EXISTS %s" % tablename
			cursor.execute(sql)
			sql = "CREATE TABLE %s (%s)" % (tablename,
                          ", ".join([ "%s text" % column for column in row ]))
			cursor.execute(sql)

			insertsql = "INSERT INTO %s VALUES (%s)" % (tablename,
                            ", ".join([ "?" for column in row ]))

			rowlen = len(row)
		
		else:
			# skip lines that don't have right number of columns
			if len(row) == rowlen:
				cursor.execute(insertsql, row)

	conn.commit()

# create html file
html_file = open(os.path.join(report_dir, '%s.html' % tablename), 'wb')
openHTML(tablename)

full_header = ['Filename', 'Filesize', 'Date modified', 'Errors', 'Checksum', 
				'Identifier', 'PRONOM ID', 'Format', 'Format Version', 'MIME type', 
				'Basis for ID', 'Warning']

# ADD IN AGGREGATE REPORTS

# Sorted format list report
sql = "SELECT format, COUNT(*) as 'num' FROM %s GROUP BY format ORDER BY num DESC" % tablename
path = os.path.join(csv_dir, '%s_formats.csv' % tablename)
format_header = ['Format', 'Count']
sqlite_to_csv(sql, path, format_header)
writeHTML('File format')

# Sorted format and version list report
sql = "SELECT format, version, COUNT(*) as 'num' FROM %s GROUP BY format, version ORDER BY num DESC" % tablename
path = os.path.join(csv_dir, '%s_formatVersion.csv' % tablename)
version_header = ['Format', 'Version', 'Count']
sqlite_to_csv(sql, path, version_header)
writeHTML('File format and version')

# Sorted MIMETYPE list report
sql = "SELECT mime, COUNT(*) as 'num' FROM %s GROUP BY mime ORDER BY num DESC" % tablename
path = os.path.join(csv_dir, '%s_mimetypes.csv' % tablename)
mime_header = ['mimetype', 'Count']
sqlite_to_csv(sql, path, mime_header)
writeHTML('Mimetype')

# Dates report
sql = "SELECT SUBSTR(modified, 1, 4) as 'year', COUNT(*) as 'num' FROM %s GROUP BY year ORDER BY num DESC" % tablename
path = os.path.join(csv_dir, '%s_years.csv' % tablename)
year_header = ['Year Last Modified', 'Count']
sqlite_to_csv(sql, path, year_header)
writeHTML('Last modified date by year')

# Unidentified files report
sql = "SELECT * FROM %s WHERE puid='UNKNOWN';" % tablename
path = os.path.join(csv_dir, '%s_unidentified.csv' % tablename)
sqlite_to_csv(sql, path, full_header)
writeHTML('Unidentified')

# Errors report
sql = "SELECT * FROM %s WHERE errors <> '';" % tablename
path = os.path.join(csv_dir, '%s_errors.csv' % tablename)
sqlite_to_csv(sql, path, full_header)
writeHTML('Errors')

# Warnings report
sql = "SELECT * FROM %s WHERE warning <> '';" % tablename
path = os.path.join(csv_dir, '%s_warnings.csv' % tablename)
sqlite_to_csv(sql, path, full_header)
writeHTML('Warnings')

# Duplicates report
sql = "SELECT * FROM %s t1 WHERE EXISTS (SELECT 1 from %s t2 WHERE t2.md5 = t1.md5 AND t1.filename != t2.filename) ORDER BY md5;" % (tablename, tablename)
path = os.path.join(csv_dir, '%s_duplicates.csv' % tablename)
sqlite_to_csv(sql, path, full_header)
writeHTML('Duplicates')

# close HTML file tags
closeHTML()

html_file.close()
cursor.close()
conn.close()

print("Process complete. Reports in %s." % report_dir)