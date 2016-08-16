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
import shutil
import sqlite3
import subprocess
import sys

def run_siegfried(source_dir):
	'''Run siegfried on directory'''
	# run siegfried against specified directory
	print("\nRunning Siegfried against %s. This may take a few minutes." % source_dir)
	siegfried_command = "sf -z -csv -hash md5 '%s' > %s" % (source_dir, sf_file)
	subprocess.call(siegfried_command, shell=True)
	print("Characterization complete. Processing results.\n")

def run_clamAV(source_dir):
	'''Run ClamAV on directory'''
	# run virus check on specified directory
	timestamp = str(datetime.datetime.now())
	print("\nRunning virus check on %s. This may take a few minutes." % source_dir)
	clamAV_command = "clamscan -i -r %s | tee %s/%s_virusCheck.txt" % (source_dir, report_dir, sourcebase)
	subprocess.call(clamAV_command, shell=True)
        vc_File = "%s/%s_virusCheck.txt" % (report_dir, sourcebase)
        # add timestamp
        target = open(vc_File, 'a')
        target.write("Date scanned: %s" % timestamp)
        target.close()
        # check log for infected files
	if "Infected files: 0" not in open(vc_File).read():
                raw_answer = raw_input("\nInfected file(s) found. Do you want to keep processing (y/n)?")
                answer = str.lower(raw_answer)
                if answer == "n":
                        sys.exit()
        else:
                print("\nNo infections found in %s." % source_dir)

def run_bulkExt(source_dir):
        '''Run bulk extractor on directory'''
        # run bulk extractor against specified directory if option is chosen
        bulkExt_log = "%s/%s_bulkExt-log.txt" % (report_dir, sourcebase)
        print("\nRunning Bulk Extractor on %s. This may take a few minutes." % source_dir)
        try:
                os.makedirs(bulkExt_dir)
        except OSError as exception:
                if exception.errno != errno.EEXIST:
                        raise
        bulkExt_command = "bulk_extractor -S ssn_mode=2 -o %s -R %s | tee %s" % (bulkExt_dir, source_dir, bulkExt_log)
	subprocess.call(bulkExt_command, shell=True)

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
				insertsql = "INSERT INTO siegfried VALUES (%s)" % (", ".join([ "?" for column in row ]))
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
	html_file.write('<p>%s</p>' % os.path.abspath(args.source))
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
	write_html('File formats', path)

	# sorted format and version list report
	sql = "SELECT format, id, version, COUNT(*) as 'num' FROM siegfried GROUP BY format, version ORDER BY num DESC"
	path = os.path.join(csv_dir, '%s_formatVersion.csv' % basename)
	version_header = ['Format', 'ID', 'Version', 'Count']
	sqlite_to_csv(sql, path, version_header)
	write_html('File formats and versions', path)

	# sorted MIMETYPE list report
	sql = "SELECT mime, COUNT(*) as 'num' FROM siegfried GROUP BY mime ORDER BY num DESC"
	path = os.path.join(csv_dir, '%s_mimetypes.csv' % basename)
	mime_header = ['mimetype', 'Count']
	sqlite_to_csv(sql, path, mime_header)
	write_html('Mimetypes', path)

	# dates report
	sql = "SELECT SUBSTR(modified, 1, 4) as 'year', COUNT(*) as 'num' FROM siegfried GROUP BY year ORDER BY num DESC"
	path = os.path.join(csv_dir, '%s_years.csv' % basename)
	year_header = ['Year Last Modified', 'Count']
	sqlite_to_csv(sql, path, year_header)
	write_html('Last modified dates by year', path)

	# unidentified files report
	sql = "SELECT * FROM siegfried WHERE id='UNKNOWN';"
	path = os.path.join(csv_dir, '%s_unidentified.csv' % basename)
	sqlite_to_csv(sql, path, full_header)
	write_html('Unidentified', path)

	# errors report
	sql = "SELECT * FROM siegfried WHERE errors <> '';"
	path = os.path.join(csv_dir, '%s_errors.csv' % basename)
	sqlite_to_csv(sql, path, full_header)
	write_html('Errors', path)

	# warnings report
	sql = "SELECT * FROM siegfried WHERE warning <> '';"
	path = os.path.join(csv_dir, '%s_warnings.csv' % basename)
	sqlite_to_csv(sql, path, full_header)
	write_html('Warnings', path)

	# duplicates report
	sql = "SELECT * FROM siegfried t1 WHERE EXISTS (SELECT 1 from siegfried t2 WHERE t2.md5 = t1.md5 AND t1.filename != t2.filename) ORDER BY md5;"
	path = os.path.join(csv_dir, '%s_duplicates.csv' % basename)
	sqlite_to_csv(sql, path, full_header)
	write_html('Duplicates (md5 hash)', path)

def sqlite_to_csv(sql, path, header):
	'''Write sql query result to csv'''
	with open(path, 'wb') as report:
		w = csv.writer(report)
		w.writerow(header)
		for row in cursor.execute(sql):
			w.writerow(row)

def write_html(header, path):
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

def close_html():
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
	close_html() # close HTML file tags
	make_tree(source_dir) # create tree.txt


""" 
MAIN FLOW 
"""

# parse arguments
parser = argparse.ArgumentParser()
parser.add_argument("-b", "--bulkextractor", help="Run Bulk Extractor on source", action="store_true")
parser.add_argument("-d", "--diskimage", help="Use disk image instead of dir as input", action="store_true")
parser.add_argument("--hfs", help="Use for raw disk images of HFS disks", action="store_true")
parser.add_argument("-n", "--noclam", help="Skip ClamScan Virus Check", action="store_true")
parser.add_argument("-r", "--removefiles", help="Delete 'carved_files' directory when done", action="store_true")
parser.add_argument("source", help="Path to source directory or disk image")
parser.add_argument("filename", help="Name of csv file to create")
args = parser.parse_args()

# system info
brunnhilde_version = 'v0.4.1'
siegfried_version = subprocess.check_output(["sf", "-version"])

# global variables
current_dir = os.getcwd()
filename = args.filename
basename = os.path.splitext(filename)[0]
sourcename = os.path.realpath(args.source)
sourcebase = os.path.basename(sourcename)
report_dir = os.path.join(current_dir, '%s' % basename)
csv_dir = os.path.join(report_dir, 'CSVs')
bulkExt_dir = os.path.join(report_dir, 'bulkExt')
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
		carvefiles = "bash /usr/share/hfsexplorer/bin/unhfs.sh -o %s %s" % (tempdir, args.source)
		try:
			subprocess.call(carvefiles, shell=True)
		except subprocess.CalledProcessError as e:
			print(e.output)
			print("Brunnhilde was unable to export files from disk image. Ending process.")
			shutil.rmtree(report_dir)
			sys.exit()

	else: # non-hfs disks (note: no UDF support yet)
		carvefiles = ['tsk_recover', '-a', args.source, tempdir]
		try:
			subprocess.check_call(carvefiles)
		except subprocess.CalledProcessError as e:
			print(e.output)
			print("Brunnhilde was unable to export files from disk image. Ending process.")
			shutil.rmtree(report_dir)
			sys.exit()

	# process tempdir
	if args.noclam == False: # run clamAV virus check unless specified otherwise
		run_clamAV(tempdir)
	process_content(tempdir)
	if args.bulkextractor == True: # bulk extractor option is chosen
		run_bulkExt(tempdir)
	if args.removefiles == True:
		shutil.rmtree(tempdir)


else: #source is a directory
	if os.path.isdir(args.source) == False:
		print("Source is not a Directory. If you're processing a disk image, place '-d' before source.\n")
		sys.exit()
	if args.noclam == False: # run clamAV virus check unless specified otherwise
		run_clamAV(args.source)
	process_content(args.source)
	if args.bulkextractor == True: # bulk extractor option is chosen
		run_bulkExt(args.source)

 

# close files, connections
html_file.close()
cursor.close()
conn.close()

print("Process complete. Reports in %s." % report_dir)
