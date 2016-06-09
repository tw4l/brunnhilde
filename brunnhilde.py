#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Brunnhilde
---
A Siegfried-based digital archives reporting tool

For information on usage and dependencies, see:
github.com/timothyryanwalsh/brunnhilde

Python 2.7

The MIT License (MIT)
Copyright (c) 2016 Tim Walsh
"""

import argparse
import csv
import datetime
import errno
import os
import sqlite3
import subprocess
import sys

def run_siegfried(source_dir):
	'''Run siegfried on directory'''
	# run siegfried against specified directory
	print("Running Siegfried against %s. This may take a few minutes." % source_dir)
	siegfried_command = "sf -z -csv -hash md5 %s > %s" % (source_dir, sf_file)
	subprocess.call(siegfried_command, shell=True)
	print("Characterization complete. Processing results.")

def import_csv():
	'''Import csv file into sqlite db'''
	with open(sf_file, 'rb') as f:
		reader = csv.reader(f)
		header = True
		for row in reader:
			if header:
				header = False # gather column names from first row of csv
				sql = "DROP TABLE IF EXISTS siegfried"
				cursor.execute(sql)
				sql = "CREATE TABLE siegfried (filename text, filesize text, modified text, errors text, md5 text, namespace text, id text, format text, version text, mime text, basis text, warning text)"
				cursor.execute(sql)
				insertsql = "INSERT INTO siegfried VALUES (%s)" % (
                            ", ".join([ "?" for column in row ]))
				rowlen = len(row)
			else:
				# skip lines that don't have right number of columns
				if len(row) == rowlen:
					cursor.execute(insertsql, row)
		conn.commit()

def get_stats(source_dir, scan_started):
	'''Get aggregate statistics and write to html report'''
	cursor.execute("SELECT COUNT(*) from siegfried;")
	num_files = cursor.fetchone()[0]

	cursor.execute("SELECT COUNT(DISTINCT md5) from siegfried;")
	unique_files = cursor.fetchone()[0]

	cursor.execute("SELECT COUNT(*) from siegfried where filesize='0';")
	empty_files = cursor.fetchone()[0]

	cursor.execute("SELECT COUNT(md5) FROM siegfried t1 WHERE EXISTS (SELECT 1 from siegfried t2 WHERE t2.md5 = t1.md5 AND t1.filename != t2.filename)")
	all_dupe_files = cursor.fetchone()[0]

	cursor.execute("SELECT COUNT(DISTINCT md5) FROM siegfried t1 WHERE EXISTS (SELECT 1 from siegfried t2 WHERE t2.md5 = t1.md5 AND t1.filename != t2.filename)")
	unique_dupe_files = cursor.fetchone()[0]

	cursor.execute("SELECT COUNT(*) FROM siegfried WHERE id='UNKNOWN';")
	unidentified_files = cursor.fetchone()[0]

	year_sql = "SELECT DISTINCT SUBSTR(modified, 1, 4) as 'year' FROM siegfried;"
	year_path = os.path.join(csv_dir, '%s_uniqueyears.csv' % basename)
	with open(year_path, 'wb') as year_report:
		w = csv.writer(year_report)
		for row in cursor.execute(year_sql):
			w.writerow(row)
	with open(year_path, 'rb') as year_report:
		r = csv.reader(year_report)
		years = []
		for row in r:
			years.append(row[0])
		begin_date = min(years, key=float)
		end_date = max(years, key=float)
	os.remove(year_path) # delete temporary "uniqueyear" file from csv directory

	cursor.execute("SELECT COUNT(DISTINCT format) as formats from siegfried WHERE format <> '';")
	num_formats = cursor.fetchone()[0]

	cursor.execute("SELECT COUNT(*) FROM siegfried WHERE errors <> '';")
	num_errors = cursor.fetchone()[0]

	cursor.execute("SELECT COUNT(*) FROM siegfried WHERE warning <> '';")
	num_warnings = cursor.fetchone()[0]

	html_file.write("<!DOCTYPE html>")
	html_file.write("<html lang='en'>")
	html_file.write("<head>")
	html_file.write("<title>Brunnhilde report for: %s</title>" % basename)
	html_file.write("<meta http-equiv='Content-Type' content='text/html; charset=utf-8'>")
	html_file.write("</head>")
	html_file.write("<body max>")
	html_file.write('<h1>Brunnhilde %s report</h1>' % brunnhilde_version)
	html_file.write('<h2>Provenance information</h2>')
	html_file.write('<h3>Siegfried version used</h3>')
	html_file.write('<p>%s</p>' % siegfried_version)
	html_file.write('<h3>Time of scan</h3>')
	html_file.write('<p>%s</p>' % scan_started)
	html_file.write('<h3>Source of files</h3>')
	html_file.write('<p>%s</p>' % args.source)
	html_file.write('<h3>Accession/Identifier</h3>')
	html_file.write('<p>%s</p>' % basename)
	html_file.write('<h2>Aggregate statistics</h2>')
	html_file.write('<ul>')
	html_file.write('<li>Total files: %s</li>' % num_files)
	html_file.write('<li>Years (last modified date): %s - %s</li>' % (begin_date, end_date))
	html_file.write('<li>Unique files: %s</li>' % unique_files)
	html_file.write('<li>Empty files: %s</li>' % empty_files)
	html_file.write('<li>Total duplicate files: %s</li>' % all_dupe_files)
	html_file.write('<li>Unique duplicate files: %s</li>' % unique_dupe_files)
	html_file.write('<li>Unidentified files: %s</li>' % unidentified_files)
	html_file.write('<li>Identified file formats: %s</li>' % num_formats)
	html_file.write('<li>Siegfried errors: %s</li>' % num_errors)
	html_file.write('<li>Siegfried warnings: %s</li>' % num_warnings)
	html_file.write('</ul>')
	html_file.write('<p><em>Note: As Siegfried scans both archive packages (e.g. Zip files) and their contents, numbers of unique, empty, and duplicate files may appear not to perfectly add up.</em></p>')

def generate_reports():
	'''Run sql queries on db to generate reports, write to csv and html'''
	full_header = ['Filename', 'Filesize', 'Date modified', 'Errors', 'Checksum', 
				'Namespace', 'ID', 'Format', 'Format Version', 'MIME type', 
				'Basis for ID', 'Warning']

	# sorted format list report
	sql = "SELECT format, id, COUNT(*) as 'num' FROM siegfried GROUP BY format ORDER BY num DESC"
	path = os.path.join(csv_dir, '%s_formats.csv' % basename)
	format_header = ['Format', 'ID', 'Count']
	sqlite_to_csv(sql, path, format_header)
	writeHTML('File formats', path)

	# sorted format and version list report
	sql = "SELECT format, id, version, COUNT(*) as 'num' FROM siegfried GROUP BY format, version ORDER BY num DESC"
	path = os.path.join(csv_dir, '%s_formatVersion.csv' % basename)
	version_header = ['Format', 'ID', 'Version', 'Count']
	sqlite_to_csv(sql, path, version_header)
	writeHTML('File formats and versions', path)

	# sorted MIMETYPE list report
	sql = "SELECT mime, COUNT(*) as 'num' FROM siegfried GROUP BY mime ORDER BY num DESC"
	path = os.path.join(csv_dir, '%s_mimetypes.csv' % basename)
	mime_header = ['mimetype', 'Count']
	sqlite_to_csv(sql, path, mime_header)
	writeHTML('Mimetypes', path)

	# dates report
	sql = "SELECT SUBSTR(modified, 1, 4) as 'year', COUNT(*) as 'num' FROM siegfried GROUP BY year ORDER BY num DESC"
	path = os.path.join(csv_dir, '%s_years.csv' % basename)
	year_header = ['Year Last Modified', 'Count']
	sqlite_to_csv(sql, path, year_header)
	writeHTML('Last modified dates by year', path)

	# unidentified files report
	sql = "SELECT * FROM siegfried WHERE id='UNKNOWN';"
	path = os.path.join(csv_dir, '%s_unidentified.csv' % basename)
	sqlite_to_csv(sql, path, full_header)
	writeHTML('Unidentified', path)

	# errors report
	sql = "SELECT * FROM siegfried WHERE errors <> '';"
	path = os.path.join(csv_dir, '%s_errors.csv' % basename)
	sqlite_to_csv(sql, path, full_header)
	writeHTML('Errors', path)

	# warnings report
	sql = "SELECT * FROM siegfried WHERE warning <> '';"
	path = os.path.join(csv_dir, '%s_warnings.csv' % basename)
	sqlite_to_csv(sql, path, full_header)
	writeHTML('Warnings', path)

	# duplicates report
	sql = "SELECT * FROM siegfried t1 WHERE EXISTS (SELECT 1 from siegfried t2 WHERE t2.md5 = t1.md5 AND t1.filename != t2.filename) ORDER BY md5;"
	path = os.path.join(csv_dir, '%s_duplicates.csv' % basename)
	sqlite_to_csv(sql, path, full_header)
	writeHTML('Duplicates (md5 hash)', path)

def sqlite_to_csv(sql, path, header):
	'''Write sql query result to csv'''
	with open(path, 'wb') as report:
		w = csv.writer(report)
		w.writerow(header)
		for row in cursor.execute(sql):
			w.writerow(row)

def writeHTML(header, path):
	'''Write csv file to html table'''
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
	'''Write html closing tags'''
	html_file.write("</body>")
	html_file.write("</html>")

def make_tree(source_dir):
	'''Call tree on source directory and save output to tree.txt'''
	# create tree report
	tree_command = "tree -tDhR %s > %s" % (source_dir, os.path.join(report_dir, '%s_tree.txt' % basename))
	subprocess.call(tree_command, shell=True)

def process_content(source_dir):
	'''Run through main processing flow on specified directory'''
	scan_started = str(datetime.datetime.now()) # get time
	run_siegfried(source_dir) # run siegfried
	import_csv() # load csv into sqlite db
	get_stats(source_dir, scan_started) # get aggregate stats and write to html file
	generate_reports() # run sql queries, print to html and csv
	closeHTML() # close HTML file tags
	make_tree(source_dir) # create tree.txt


""" 
MAIN FLOW 
"""

# parse arguments
parser = argparse.ArgumentParser()
parser.add_argument("-d", "--diskimage", help="Use disk image instead of dir as input", action="store_true")
parser.add_argument("source", help="Path to source directory or disk image")
parser.add_argument("filename", help="Name of csv file to create")
args = parser.parse_args()

# system info
brunnhilde_version = 'v0.4.0'
siegfried_version = subprocess.check_output(["sf", "-version"])

# global variables
current_dir = os.getcwd()
filename = args.filename
basename = os.path.splitext(filename)[0]
report_dir = os.path.join(current_dir, '%s' % basename)
csv_dir = os.path.join(report_dir, 'CSVs')
sf_file = os.path.join(report_dir, filename)

# create directory for reports
try:
	os.makedirs(report_dir)
except OSError as exception:
	if exception.errno != errno.EEXIST:
		raise
	
# create subdirectory for CSV reports
try:
	os.makedirs(csv_dir)
except OSError as exception:
	if exception.errno != errno.EEXIST:
		raise

# create html report
html_file = open(os.path.join(report_dir, '%s.html' % basename), 'wb')

# open sqlite db
db = os.path.join(report_dir, os.path.splitext(filename)[0]) + '.sqlite'
conn = sqlite3.connect(db)
conn.text_factory = str  # allows utf-8 data to be stored
cursor = conn.cursor()

# characterize source
if args.diskimage == True: # source is a disk image
	# make tempdir
	tempdir = os.path.join(report_dir, 'carved_files')
	try:
		os.makedirs(tempdir)
	except OSError as exception:
		if exception.errno != errno.EEXIST:
			raise

	# export disk image contents to tempdir
	if args.hfs == True: # hfs disks
		carvefiles = ['bash', '/usr/share/hfsexplorer/bin/unhfs.sh', '-o', tempdir, '-resforks', 'APPLEDOUBLE']
		try:
			subprocess.check_call(carvefiles)
		except subprocess.CalledProcessError as e:
			print(e.output)
			sys.exit()

	else: # non-hfs disks (note: no UDF support yet)
		carvefiles = ['tsk_recover', '-a', args.source, tempdir]
		try:
			subprocess.check_call(carvefiles)
		except subprocess.CalledProcessError as e:
			print(e.output)
			sys.exit()

	# process tempdir
	process_content(tempdir)

else: #source is a directory
	process_content(args.source)

# close files, connections
html_file.close()
cursor.close()
conn.close()

print("Process complete. Reports in %s." % report_dir)
