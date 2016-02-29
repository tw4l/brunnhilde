#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""

Brunnhilde - A companion to Richard Lehane's Seigfried 
(www.itforarchivists.com/siegfried)

Brunnhilde runs Siegfried against a specified directory, loads the results
into a sqlite3 database, and queries the database to generate aggregate
reports to aid in triage, arrangement, and description of digital archives.

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

# run siegfried against specified directory
print("Running Siegfried against %s. This may take a few minutes..." % walk_dir)
siegfried_command = "sf -z -csv -hash md5 %s > %s" % (walk_dir, filename)
subprocess.call(siegfried_command, shell=True)
print("Siegfried characterization complete. Processing results...")

# rewrite csv header row
new_filename = os.path.splitext(filename)[0] + "_modified.csv"
with open(filename, 'rb') as inFile, open(new_filename, "wb") as outFile:
	r = csv.reader(inFile)
	w = csv.writer(outFile)

	# skip old header
	next(r, None) 
	# write new header
	w.writerow(['filename', 'filesize', 'modified', 'errors', 'md5', 'identifier', 'id', 'format',
				'version', 'mimetype', 'basis', 'warning'])

	for row in r:
		modified_date = row[2][:4]
		row[2] = modified_date
		w.writerow(row)

	inFile.close()
	outFile.close()

# open sqlite db and start processing
db = os.path.splitext(filename)[0] + '.sqlite'
conn = sqlite3.connect(db)
conn.text_factory = str  # allows utf-8 data to be stored

cursor = conn.cursor()

# import modified csv file into sqlite db
# https://tentacles666.wordpress.com/2014/11/14/python-creating-a-sqlite3-database-from-csv-files/
tablename = os.path.splitext(filename)[0]
with open(new_filename, 'rb') as f:
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

print("Processing complete. Generating reports...")

# create directory for reports
current_dir = os.getcwd()
report_dir = os.path.join(current_dir, '%s_reports' % tablename)
try:
	os.makedirs(report_dir)
except OSError as exception:
	if exception.errno != errno.EEXIST:
		raise

# Sorted format list report
sql = "SELECT format, COUNT(*) as 'num' FROM %s GROUP BY format ORDER BY num DESC" % tablename
report_filename = '%s_formats.csv' % tablename
path = os.path.join(report_dir, report_filename)
with open(path, 'wb') as format_report:
	w = csv.writer(format_report)
	w.writerow(['Format', 'Count'])
	for row in cursor.execute(sql):
		w.writerow(row)

# Sorted format and version list report
sql = "SELECT format, version, COUNT(*) as 'num' FROM %s GROUP BY format, version ORDER BY num DESC" % tablename
report_filename = '%s_formatAndVersion.csv' % tablename
path = os.path.join(report_dir, report_filename)
with open(path, 'wb') as format_version_report:
	w = csv.writer(format_version_report)
	w.writerow(['Format', 'Version', 'Count'])
	for row in cursor.execute(sql):
		w.writerow(row)

# Sorted MIMETYPE list report
sql = "SELECT mimetype, COUNT(*) as 'num' FROM %s GROUP BY mimetype ORDER BY num DESC" % tablename
report_filename = '%s_mimetypes.csv' % tablename
path = os.path.join(report_dir, report_filename)
with open(path, 'wb') as mime_report:
	w = csv.writer(mime_report)
	w.writerow(['MIMEtype', 'Count'])
	for row in cursor.execute(sql):
		w.writerow(row)

# Errors report
sql = "SELECT * FROM %s WHERE errors <> '';" % tablename
report_filename = '%s_errors.csv' % tablename
path = os.path.join(report_dir, report_filename)
with open(path, 'wb') as error_report:
	w = csv.writer(error_report)
	w.writerow(['Filename', 'Filesize', 'Date modified', 'Errors', 'Checksum', 'Identifier', 'PRONOM ID', 
		'Format', 'Format Version', 'MIME type', 'Basis for ID', 'Warning'])
	for row in cursor.execute(sql):
		w.writerow(row)

# Warnings report
sql = "SELECT * FROM %s WHERE warning <> '';" % tablename
report_filename = '%s_warnings.csv' % tablename
path = os.path.join(report_dir, report_filename)
with open(path, 'wb') as warning_report:
	w = csv.writer(warning_report)
	w.writerow(['Filename', 'Filesize', 'Date modified', 'Errors', 'Checksum', 'Identifier', 'PRONOM ID', 
		'Format', 'Format Version', 'MIME type', 'Basis for ID', 'Warning'])
	for row in cursor.execute(sql):
		w.writerow(row)

# Unidentified files report
sql = "SELECT * FROM %s WHERE id='UNKNOWN';" % tablename
report_filename = '%s_unidentified.csv' % tablename
path = os.path.join(report_dir, report_filename)
with open(path, 'wb') as unidentified_report:
	w = csv.writer(unidentified_report)
	w.writerow(['Filename', 'Filesize', 'Date Modified', 'Errors', 'Checksum', 'Identifier', 'PRONOM ID', 
		'Format', 'Format Version', 'MIME Type', 'Basis for ID', 'Warning'])
	for row in cursor.execute(sql):
		w.writerow(row)

# Duplicates report
sql = "SELECT * FROM %s t1 WHERE EXISTS (SELECT 1 from %s t2 WHERE t2.md5 = t1.md5 AND t1.filename != t2.filename);" % (tablename, tablename)
report_filename = '%s_duplicates.csv' % tablename
path = os.path.join(report_dir, report_filename)
with open(path, 'wb') as duplicates_report:
	w = csv.writer(duplicates_report)
	w.writerow(['Filename', 'Filesize', 'Date Modified', 'Errors', 'Checksum', 'Identifier', 'PRONOM ID', 
		'Format', 'Format Version', 'MIME Type', 'Basis for ID', 'Warning'])
	for row in cursor.execute(sql):
		w.writerow(row)

# Dates report
sql = "SELECT modified, COUNT(*) as 'num' FROM %s GROUP BY modified ORDER BY num DESC" % tablename
report_filename = '%s_dates.csv' % tablename
path = os.path.join(report_dir, report_filename)
with open(path, 'wb') as date_report:
	w = csv.writer(date_report)
	w.writerow(['Year Last Modified', 'Count'])
	for row in cursor.execute(sql):
		w.writerow(row)

cursor.close()
conn.close()
print("Process complete. Reports in %s" % report_dir)
