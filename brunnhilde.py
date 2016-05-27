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
Works with Siegfried versions 1.0.0 to 1.4.5 (not yet 1.5.*)

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
	html_file.write('<h2>Aggregate stats</h2>')
	html_file.write('<ul>')
	html_file.write('<li>Total files: %s</li>' % num_files)
	html_file.write('<li>Unique files: %s</li>' % unique_files)
	html_file.write('<li>Duplicate files: %s</li>' % dupe_files)
	html_file.write('<li>Unidentified files: %s</li>' % unidentified_files)
	#html_file.write('<li>Years represented: </li>') FIRST AND LAST? ALL?
	html_file.write('<li>Total file formats: %s</li>' % num_formats)
	html_file.write('<li>Siegfried errors: %s</li>' % num_errors)
	html_file.write('<li>Siegfried warnings: %s</li>' % num_warnings)
	html_file.write('</ul>')

	# WRITE AGGREGATE STATS

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
	with open(path, 'wb') as report:
		w = csv.writer(report)
		w.writerow(header)
		for row in cursor.execute(sql):
			w.writerow(row)

# create directories
current_dir = os.getcwd()
basename = os.path.splitext(filename)[0]

# create directory for reports
report_dir = os.path.join(current_dir, '%s' % basename)
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

# import csv file into sqlite db
# https://tentacles666.wordpress.com/2014/11/14/python-creating-a-sqlite3-database-from-csv-files/
with open(os.path.join(report_dir, filename), 'rb') as f:
	reader = csv.reader(f)

	header = True
	for row in reader:
		if header:
			# gather column names from first row of csv
			header = False

			sql = "DROP TABLE IF EXISTS siegfried"
			cursor.execute(sql)
			sql = "CREATE TABLE siegfried (filename text, filesize text, modified text, errors text, md5 text, id text, puid text, format text, version text, mime text, basis text, warning text)"
			cursor.execute(sql)

			insertsql = "INSERT INTO siegfried VALUES (%s)" % (
                            ", ".join([ "?" for column in row ]))

			rowlen = len(row)
		
		else:
			# skip lines that don't have right number of columns
			if len(row) == rowlen:
				cursor.execute(insertsql, row)

	conn.commit()


# Get aggregate stats
cursor.execute("SELECT COUNT(*) from siegfried;")
num_files = cursor.fetchone()[0]

cursor.execute("SELECT COUNT(DISTINCT md5) from siegfried;")
unique_files = cursor.fetchone()[0]

cursor.execute("SELECT COUNT(*) FROM siegfried t1 WHERE EXISTS (SELECT 1 from siegfried t2 WHERE t2.md5 = t1.md5 AND t1.filename != t2.filename)")
dupe_files = cursor.fetchone()[0]

cursor.execute("SELECT COUNT(*) FROM siegfried WHERE puid='UNKNOWN';")
unidentified_files = cursor.fetchone()[0]

#cursor.execute("SELECT DISTINCT SUBSTR(modified, 1, 4) as 'year'FROM siegfried;")
#years = THIS ONE IS DIFFERENT

cursor.execute("SELECT COUNT(DISTINCT format) as formats from siegfried;")
num_formats = cursor.fetchone()[0]

cursor.execute("SELECT COUNT(*) FROM siegfried WHERE errors <> '';")
num_errors = cursor.fetchone()[0]

cursor.execute("SELECT COUNT(*) FROM siegfried WHERE warning <> '';")
num_warnings = cursor.fetchone()[0]


# create html file
html_file = open(os.path.join(report_dir, '%s.html' % basename), 'wb')
openHTML(basename)

full_header = ['Filename', 'Filesize', 'Date modified', 'Errors', 'Checksum', 
				'Identifier', 'PRONOM ID', 'Format', 'Format Version', 'MIME type', 
				'Basis for ID', 'Warning']


# Sorted format list report
sql = "SELECT format, COUNT(*) as 'num' FROM siegfried GROUP BY format ORDER BY num DESC"
path = os.path.join(csv_dir, '%s_formats.csv' % basename)
format_header = ['Format', 'Count']
sqlite_to_csv(sql, path, format_header)
writeHTML('File format')

# Sorted format and version list report
sql = "SELECT format, version, COUNT(*) as 'num' FROM siegfried GROUP BY format, version ORDER BY num DESC"
path = os.path.join(csv_dir, '%s_formatVersion.csv' % basename)
version_header = ['Format', 'Version', 'Count']
sqlite_to_csv(sql, path, version_header)
writeHTML('File format and version')

# Sorted MIMETYPE list report
sql = "SELECT mime, COUNT(*) as 'num' FROM siegfried GROUP BY mime ORDER BY num DESC"
path = os.path.join(csv_dir, '%s_mimetypes.csv' % basename)
mime_header = ['mimetype', 'Count']
sqlite_to_csv(sql, path, mime_header)
writeHTML('Mimetype')

# Dates report
sql = "SELECT SUBSTR(modified, 1, 4) as 'year', COUNT(*) as 'num' FROM siegfried GROUP BY year ORDER BY num DESC"
path = os.path.join(csv_dir, '%s_years.csv' % basename)
year_header = ['Year Last Modified', 'Count']
sqlite_to_csv(sql, path, year_header)
writeHTML('Last modified date by year')

# Unidentified files report
sql = "SELECT * FROM siegfried WHERE puid='UNKNOWN';"
path = os.path.join(csv_dir, '%s_unidentified.csv' % basename)
sqlite_to_csv(sql, path, full_header)
writeHTML('Unidentified')

# Errors report
sql = "SELECT * FROM siegfried WHERE errors <> '';"
path = os.path.join(csv_dir, '%s_errors.csv' % basename)
sqlite_to_csv(sql, path, full_header)
writeHTML('Errors')

# Warnings report
sql = "SELECT * FROM siegfried WHERE warning <> '';"
path = os.path.join(csv_dir, '%s_warnings.csv' % basename)
sqlite_to_csv(sql, path, full_header)
writeHTML('Warnings')

# Duplicates report
sql = "SELECT * FROM siegfried t1 WHERE EXISTS (SELECT 1 from siegfried t2 WHERE t2.md5 = t1.md5 AND t1.filename != t2.filename) ORDER BY md5;"
path = os.path.join(csv_dir, '%s_duplicates.csv' % basename)
sqlite_to_csv(sql, path, full_header)
writeHTML('Duplicates')

# close HTML file tags
closeHTML()

html_file.close()
cursor.close()
conn.close()

print("Process complete. Reports in %s." % report_dir)
