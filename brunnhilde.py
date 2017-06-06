#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Brunnhilde
---

A Siegfried-based digital archives reporting tool

For information on usage and dependencies, see:
github.com/timothyryanwalsh/brunnhilde

Tested in Python 2.7 and 3.5

The MIT License (MIT)
Copyright (c) 2016 Tim Walsh
http://bitarchivist.net

"""
import argparse
from collections import OrderedDict
import csv
import datetime
import errno
from itertools import islice
import os
import re
import shutil
import sqlite3
import subprocess
import sys

def run_siegfried(args, source_dir):
    """Run siegfried on directory"""
    print("\nRunning Siegfried against %s. This may take a few minutes." % source_dir)
    global sf_command
    hash_type = 'md5'
    if args.hash == 'sha1':
        hash_type = 'sha1'
    elif args.hash == 'sha256':
        hash_type = 'sha256'
    elif args.hash == 'sha512':
        hash_type = 'sha512'
    sf_command = "sf -csv -hash %s '%s' > '%s'" % (hash_type, source_dir, sf_file)
    if args.scanarchives == True:
        sf_command = sf_command.replace('sf -csv', 'sf -z -csv')
    if args.throttle == True:
        sf_command = sf_command.replace('-csv -hash', '-csv -throttle 10ms -hash')
    subprocess.call(sf_command, shell=True)
    print("\nCharacterization complete. Processing results.")
    return sf_command

def run_clamav(source_dir):
    """Run ClamAV on directory"""
    timestamp = str(datetime.datetime.now())
    print("\nRunning virus check on %s. This may take a few minutes." % source_dir)
    virus_log = os.path.join(log_dir, 'viruscheck-log.txt')
    clamav_command = "clamscan -i -r '%s' | tee '%s'" % (source_dir, virus_log)
    subprocess.call(clamav_command, shell=True)
    # add timestamp
    target = open(virus_log, 'a')
    target.write("Date scanned: %s" % timestamp)
    target.close()
    # check log for infected files
    if "Infected files: 0" not in open(virus_log).read():
        print("\nWARNING: Infected file(s) found in %s. See %s for details." % (source_dir, virus_log))
    else:
        print("\nNo infections found in %s." % source_dir)

def run_bulkext(source_dir):
    """Run bulk extractor on directory"""
    bulkext_log = os.path.join(log_dir, 'bulkext-log.txt')
    print("\nRunning Bulk Extractor on %s. This may take a few minutes." % source_dir)
    try:
        os.makedirs(bulkext_dir)
    except OSError as exception:
        if exception.errno != errno.EEXIST:
            raise
    bulkext_command = "bulk_extractor -S ssn_mode=2 -o '%s' -R '%s' | tee '%s'" % (bulkext_dir, source_dir, bulkext_log)
    subprocess.call(bulkext_command, shell=True)

def import_csv(cursor, conn):
    """Import csv file into sqlite db"""
    with open(sf_file, 'r') as f:
        reader = csv.reader(x.replace('\0', '') for x in f) # replace null bytes with empty strings on read
        header = True
        for row in reader:
            if header:
                header = False # gather column names from first row of csv
                sql = "DROP TABLE IF EXISTS siegfried"
                cursor.execute(sql)
                sql = "CREATE TABLE siegfried (filename text, filesize text, modified text, errors text, hash text, namespace text, id text, format text, version text, mime text, basis text, warning text)"
                cursor.execute(sql)
                insertsql = "INSERT INTO siegfried VALUES (%s)" % (", ".join([ "?" for column in row ]))
                rowlen = len(row)
            else:
                # skip lines that don't have right number of columns
                if len(row) == rowlen:
                    cursor.execute(insertsql, row)
        conn.commit()

def get_stats(args, source_dir, scan_started, cursor, html, brunnhilde_version, siegfried_version):
    """Get aggregate statistics and write to html report"""
    
    # get stats from sqlite db
    cursor.execute("SELECT COUNT(*) from siegfried;") # total files
    num_files = cursor.fetchone()[0]

    cursor.execute("SELECT COUNT(DISTINCT hash) from siegfried WHERE filesize<>'0';") # distinct files
    distinct_files = cursor.fetchone()[0]

    cursor.execute("SELECT COUNT(*) from siegfried where filesize='0';") # empty files
    empty_files = cursor.fetchone()[0]

    cursor.execute("SELECT COUNT(hash) FROM siegfried t1 WHERE EXISTS (SELECT 1 from siegfried t2 WHERE t2.hash = t1.hash AND t1.filename != t2.filename) AND filesize<>'0'") # duplicates
    all_dupes = cursor.fetchone()[0]

    cursor.execute("SELECT COUNT(DISTINCT hash) FROM siegfried t1 WHERE EXISTS (SELECT 1 from siegfried t2 WHERE t2.hash = t1.hash AND t1.filename != t2.filename) AND filesize<>'0'") # distinct duplicates
    distinct_dupes = cursor.fetchone()[0]

    duplicate_copies = int(all_dupes) - int(distinct_dupes) # number of duplicate copies of unique files
    duplicate_copies = str(duplicate_copies)

    cursor.execute("SELECT COUNT(*) FROM siegfried WHERE id='UNKNOWN';") # unidentified files
    unidentified_files = cursor.fetchone()[0]

    year_sql = "SELECT DISTINCT SUBSTR(modified, 1, 4) as 'year' FROM siegfried;" # min and max year
    year_path = os.path.join(csv_dir, 'uniqueyears.csv')
    with open(year_path, 'w') as year_report:
        w = csv.writer(year_report)
        for row in cursor.execute(year_sql):
            w.writerow(row)
    with open(year_path, 'r') as year_report:
        r = csv.reader(year_report)
        years = []
        for row in r:
            years.append(row[0])
        if not years:
            begin_date = "N/A"
            end_date = "N/A"  
        else:
            begin_date = min(years, key=float)
            end_date = max(years, key=float)
    os.remove(year_path) # delete temporary "uniqueyear" file from csv reports directory

    datemodified_sql = "SELECT DISTINCT modified FROM siegfried;" # min and max full modified date
    datemodified_path = os.path.join(csv_dir, 'datemodified.csv')
    with open(datemodified_path, 'w') as date_report:
        w = csv.writer(date_report)
        for row in cursor.execute(datemodified_sql):
            w.writerow(row)
    with open(datemodified_path, 'r') as date_report:
        r = csv.reader(date_report)
        dates = []
        for row in r:
            dates.append(row[0])
        if not dates:
            earliest_date = "N/A"
            latest_date = "N/A"
        else:
            earliest_date = min(dates)
            latest_date = max(dates)
    os.remove(datemodified_path)

    cursor.execute("SELECT COUNT(DISTINCT format) as formats from siegfried WHERE format <> '';") # number of identfied file formats
    num_formats = cursor.fetchone()[0]

    cursor.execute("SELECT COUNT(*) FROM siegfried WHERE errors <> '';") # number of siegfried errors
    num_errors = cursor.fetchone()[0]

    cursor.execute("SELECT COUNT(*) FROM siegfried WHERE warning <> '';") # number of siegfried warnings
    num_warnings = cursor.fetchone()[0]

    # get size from du and format
    size = subprocess.check_output(['du', '-sh', source_dir]).decode()
    size = size.replace('%s' % source_dir, '')
    size = size.replace('K', ' KB')
    size = size.replace('M', ' MB')
    size = size.replace('G', ' GB')
    size = size.replace('T', ' TB')

    # write html
    html.write('<!DOCTYPE html>')
    html.write('\n<html lang="en">')
    html.write('\n<head>')
    html.write('\n<title>Brunnhilde report for: %s</title>' % basename)
    html.write('\n<meta http-equiv="Content-Type" content="text/html; charset=utf-8">')
    html.write('\n<link rel="stylesheet" href="https://maxcdn.bootstrapcdn.com/bootstrap/3.3.7/css/bootstrap.min.css" integrity="sha384-BVYiiSIFeK1dGmJRAkycuHAHRg32OmUcww7on3RYdg4Va+PmSTsz/K68vbdEjh4u" crossorigin="anonymous">')
    html.write('\n</head>')
    html.write('\n<body style="margin:5px">')
    html.write('\n<h1>Brunnhilde HTML report</h1>')
    html.write('\n<h3>Input source (directory or disk image)</h3>')
    html.write('\n<p>%s</p>' % source)
    html.write('\n<h3>Accession/Identifier</h3>')
    html.write('\n<p>%s</p>' % basename)
    html.write('\n<h2>Provenance information</h2>')
    html.write('\n<h3>Brunnhilde version</h3>')
    html.write('\n<p>%s</p>' % brunnhilde_version)
    html.write('\n<h3>Siegfried version</h3>')
    html.write('\n<p>%s</p>' % siegfried_version)
    html.write('\n<h3>Siegfried command</h3>')
    html.write('\n<p>%s</p>' % sf_command)
    html.write('\n<h3>Time of scan</h3>')
    html.write('\n<p>%s</p>' % scan_started)
    html.write('\n<h2>Aggregate stats</h2>')
    html.write('\n<h3>Overview</h3>')
    html.write('\n<p>Total files: %s</p>' % num_files)
    html.write('\n<p>Total size: %s</p>' % size)
    html.write('\n<p>Years (last modified): %s - %s</p>' % (begin_date, end_date))
    html.write('\n<p>Earliest date: %s</p>' % earliest_date)
    html.write('\n<p>Latest date: %s</p>' % latest_date)
    html.write('\n<h3>File contents*</h3>')
    html.write('\n<p>Distinct files: %s</p>' % distinct_files)
    html.write('\n<p>Distinct files that have duplicates: %s</p>' % distinct_dupes)
    html.write('\n<p>Duplicate copies of distinct files: %s</p>' % duplicate_copies)
    html.write('\n<p>Empty files: %s</p>' % empty_files)
    html.write('\n<p>*<em>Calculated by hash value. Empty files are not counted in first three categories. Total files = distinct files + duplicate copies + empty files.</em></p>')
    html.write('\n<h3>Format identification</h3>')
    html.write('\n<p>Identified file formats: %s</p>' % num_formats)
    html.write('\n<p>Unidentified files: %s</p>' % unidentified_files)
    html.write('\n<p>Siegfried warnings: %s</p>' % num_warnings)
    html.write('\n<h3>Errors</h3>')
    html.write('\n<p>Siegfried errors: %s</p>' % num_errors)
    html.write('\n<h2>Virus scan report</h2>')
    if args.noclam == True:
        html.write('\n<p>Virus scan skipped.</p>')
    else:
        with open(os.path.join(log_dir, 'viruscheck-log.txt')) as f:
            virus_report = f.read()
        html.write('\n<p>%s</p>' % virus_report)
    html.write('\n<h2>Detailed reports</h2>')
    html.write('\n<p><a href="#File formats">File formats</a></p>')
    html.write('\n<p><a href="#File formats and versions">File formats and versions</a></p>')
    html.write('\n<p><a href="#MIME types">MIME types</a></p>')
    html.write('\n<p><a href="#Last modified dates by year">Last modified dates by year</a></p>')
    html.write('\n<p><a href="#Unidentified">Unidentified</a></p>')
    if args.showwarnings == True:
        html.write('\n<p><a href="#Warnings">Warnings</a></p>')
    html.write('\n<p><a href="#Errors">Errors</a></p>')
    html.write('\n<p><a href="#Duplicates">Duplicates</a></p>')
    if args.bulkextractor == True:
        html.write('\n<p><a href="#Personally Identifiable Information (PII)">Personally Identifiable Information (PII)</a></p>')

def generate_reports(args, cursor, html):
    """Run sql queries on db to generate reports, write to csv and html"""
    full_header = ['Filename', 'Filesize', 'Date modified', 'Errors', 'Checksum', 
                'Namespace', 'ID', 'Format', 'Format version', 'MIME type', 
                'Basis for ID', 'Warning']

    # sorted format list report
    sql = "SELECT format, id, COUNT(*) as 'num' FROM siegfried GROUP BY format ORDER BY num DESC"
    path = os.path.join(csv_dir, 'formats.csv')
    format_header = ['Format', 'ID', 'Count']
    sqlite_to_csv(sql, path, format_header, cursor)
    write_html('File formats', path, ',', html)

    # sorted format and version list report
    sql = "SELECT format, id, version, COUNT(*) as 'num' FROM siegfried GROUP BY format, version ORDER BY num DESC"
    path = os.path.join(csv_dir, 'formatVersions.csv')
    version_header = ['Format', 'ID', 'Version', 'Count']
    sqlite_to_csv(sql, path, version_header, cursor)
    write_html('File formats and versions', path, ',', html)

    # sorted mimetype list report
    sql = "SELECT mime, COUNT(*) as 'num' FROM siegfried GROUP BY mime ORDER BY num DESC"
    path = os.path.join(csv_dir, 'mimetypes.csv')
    mime_header = ['MIME type', 'Count']
    sqlite_to_csv(sql, path, mime_header, cursor)
    write_html('MIME types', path, ',', html)

    # dates report
    sql = "SELECT SUBSTR(modified, 1, 4) as 'year', COUNT(*) as 'num' FROM siegfried GROUP BY year ORDER BY num DESC"
    path = os.path.join(csv_dir, 'years.csv')
    year_header = ['Year Last Modified', 'Count']
    sqlite_to_csv(sql, path, year_header, cursor)
    write_html('Last modified dates by year', path, ',', html)

    # unidentified files report
    sql = "SELECT * FROM siegfried WHERE id='UNKNOWN';"
    path = os.path.join(csv_dir, 'unidentified.csv')
    sqlite_to_csv(sql, path, full_header, cursor)
    write_html('Unidentified', path, ',', html)
    
    # warnings report
    sql = "SELECT * FROM siegfried WHERE warning <> '';"
    path = os.path.join(csv_dir, 'warnings.csv')
    sqlite_to_csv(sql, path, full_header, cursor)
    if args.showwarnings == True:
        write_html('Warnings', path, ',', html)

    # errors report
    sql = "SELECT * FROM siegfried WHERE errors <> '';"
    path = os.path.join(csv_dir, 'errors.csv')
    sqlite_to_csv(sql, path, full_header, cursor)
    write_html('Errors', path, ',', html)

    # duplicates report
    sql = "SELECT * FROM siegfried t1 WHERE EXISTS (SELECT 1 from siegfried t2 WHERE t2.hash = t1.hash AND t1.filename != t2.filename) AND filesize<>'0' ORDER BY hash;"
    path = os.path.join(csv_dir, 'duplicates.csv')
    sqlite_to_csv(sql, path, full_header, cursor)
    write_html('Duplicates', path, ',', html)

def sqlite_to_csv(sql, path, header, cursor):
    """Write sql query result to csv"""
    with open(path, 'w') as report:
        w = csv.writer(report)
        w.writerow(header)
        for row in cursor.execute(sql):
            w.writerow(row)

def write_html(header, path, file_delimiter, html):
    """Write csv file to html table"""
    with open(path, 'r') as in_file:
        # count lines and then return to start of file
        numline = len(in_file.readlines())
        in_file.seek(0)

        #open csv reader
        r = csv.reader(in_file, delimiter="%s" % file_delimiter)

        # write header
        html.write('\n<a name="%s"></a>' % header)
        html.write('\n<h3>%s</h3>' % header)
        if header == 'Duplicates':
            html.write('\n<p><em>Duplicates are grouped by hash value.</em></p>')
        elif header == 'Personally Identifiable Information (PII)':
            html.write('\n<p><em>Potential PII in source, as identified by bulk_extractor.</em></p>')
        
        # if writing PII, handle separately
        if header == 'Personally Identifiable Information (PII)':
            if numline > 5: # aka more rows than just header
                html.write('\n<table class="table table-striped table-bordered table-condensed">')
                #write header
                html.write('\n<tr>')
                html.write('\n<td><strong>File</strong></td>')
                html.write('\n<td><strong>Value Found</strong></td>')
                html.write('\n<td><strong>Context</strong></td>')
                # write data
                for row in islice(r, 4, None): # skip header lines
                    html.write('\n</tr>')
                    for row in r:
                        # write data
                        html.write('\n<tr>')
                        for column in row:
                            html.write('\n<td>' + column + '</td>')
                        html.write('\n</tr>')
                    html.write('\n</table>')
            else:
                html.write('\nNone found.')

        # if writing duplicates, handle separately
        elif header == 'Duplicates':
            if numline > 1: #aka more rows than just header
                # read md5s from csv and write to list
                hash_list = []
                for row in r:
                    hash_list.append(row[4])
                # deduplicate md5_list
                hash_list = list(OrderedDict.fromkeys(hash_list))
                hash_list.remove('Checksum')
                # for each hash in md5_list, print header, file info, and list of matching files
                for hash_value in hash_list:
                    html.write('\n<p>Files matching checksum <strong>%s</strong>:</p>' % hash_value)
                    html.write('\n<table class="table table-striped table-bordered table-condensed">')
                    html.write('\n<tr>')
                    html.write('\n<td><strong>Filename</strong></td><td><strong>Filesize</strong></td>')
                    html.write('<td><strong>Date modified</strong></td><td><strong>Errors</strong></td>')
                    html.write('<td><strong>Checksum</strong></td><td><strong>Namespace</strong></td>')
                    html.write('<td><strong>ID</strong></td><td><strong>Format</strong></td>')
                    html.write('<td><strong>Format version</strong></td><td><strong>MIME type</strong></td>')
                    html.write('<td><strong>Basis for ID</strong></td><td><strong>Warning</strong></td>')
                    html.write('\n</tr>')
                    in_file.seek(0) # back to beginning of file
                    for row in r:
                        if row[4] == '%s' % hash_value:
                            # write data
                            html.write('\n<tr>')
                            for column in row:
                                html.write('\n<td>' + column + '</td>')
                            html.write('\n</tr>')
                    html.write('\n</table>')
            else:
                html.write('\nNone found.')

        # otherwise write as normal
        else:
            if numline > 1: #aka more rows than just header
                html.write('\n<table class="table table-striped table-bordered table-condensed">')
                # write header row
                html.write('\n<tr>')
                row1 = next(r)
                for column in row1:
                    html.write('\n<td><strong>' + column + '</strong></td>')
                html.write('\n</tr>')
                # write data rows
                for row in r:
                    # write data
                    html.write('\n<tr>')
                    for column in row:
                        html.write('\n<td>' + column + '</td>')
                    html.write('\n</tr>')
                html.write('\n</table>')
            else:
                html.write('\nNone found.')
        
        # write link to top
        html.write('\n<p>(<a href="#top">Return to top</a>)</p>')

def close_html(html):
    """Write html closing tags"""
    html.write('\n</body>')
    html.write('\n</html>')

def make_tree(source_dir):
    """Call tree on source directory and save output to tree.txt"""
    tree_command = "tree -tDhR '%s' > '%s'" % (source_dir, os.path.join(report_dir, 'tree.txt'))
    subprocess.call(tree_command, shell=True)

def process_content(args, source_dir, cursor, conn, html, brunnhilde_version, siegfried_version):
    """Run through main processing flow on specified directory"""
    scan_started = str(datetime.datetime.now()) # get time
    run_siegfried(args, source_dir) # run siegfried
    import_csv(cursor, conn) # load csv into sqlite db
    get_stats(args, source_dir, scan_started, cursor, html, brunnhilde_version, siegfried_version) # get aggregate stats and write to html file
    generate_reports(args, cursor, html) # run sql queries, print to html and csv
    close_html(html) # close HTML file tags
    make_tree(source_dir) # create tree.txt

def write_pronom_links(old_file, new_file):
    """Use regex to replace fmt/# and x-fmt/# PUIDs with link to appropriate PRONOM page"""
    with open(old_file, 'r') as in_file:
        with open(new_file, 'w') as out_file:
            for line in in_file:
                regex = r"fmt\/[0-9]+|x\-fmt\/[0-9]+" #regex to match fmt/# or x-fmt/#
                pronom_links_to_replace = re.findall(regex, line)
                new_line = line
                for match in pronom_links_to_replace:
                    new_line = line.replace(match, "<a href=\"http://nationalarchives.gov.uk/PRONOM/" + 
                            match + "\" target=\"_blank\">" + match + "</a>")
                    line = new_line # allow for more than one match per line
                out_file.write(new_line)

def _make_parser(version):
    parser = argparse.ArgumentParser()
    parser.add_argument("-a", "--allocated", help="Instruct tsk_recover to export only allocated files (recovers all files by default)", action="store_true")
    parser.add_argument("-b", "--bulkextractor", help="Run Bulk Extractor on source", action="store_true")
    parser.add_argument("-d", "--diskimage", help="Use disk image instead of dir as input", action="store_true")
    parser.add_argument("--hash", help="Specify hash algorithm", dest="hash", action="store", type=str)
    parser.add_argument("--hfs", help="Use for raw disk images of HFS disks", action="store_true")
    parser.add_argument("-n", "--noclam", help="Skip ClamScan Virus Check", action="store_true")
    parser.add_argument("-r", "--removefiles", help="Delete 'carved_files' directory when done (disk image input only)", action="store_true")
    parser.add_argument("-t", "--throttle", help="Pause for 1s between Siegfried scans", action="store_true")
    parser.add_argument("--tsk_imgtype", help="Specify format of image type for tsk_recover. See tsk_recover man page for details", action="store")
    parser.add_argument("--tsk_fstype", help="Specify file system type for tsk_recover. See tsk_recover man page for details", action="store")
    parser.add_argument("--tsk_sector_offset", help="Sector offset for particular volume for tsk_recover to recover", action="store")
    parser.add_argument("-V", "--version", help="Display Brunnhilde version", action="version", version="%s" % version)
    parser.add_argument("-w", "--showwarnings", help="Add Siegfried warnings to HTML report", action="store_true")
    parser.add_argument("-z", "--scanarchives", help="Decompress and scan zip, tar, gzip, warc, arc with Siegfried", action="store_true")
    parser.add_argument("source", help="Path to source directory or disk image")
    parser.add_argument("destination", help="Path to destination for reports")
    parser.add_argument("basename", help="Accession number or identifier, used as basename for outputs")

    return parser

def main():
    # system info
    brunnhilde_version = 'brunnhilde 1.5.0'
    siegfried_version = subprocess.check_output(["sf", "-version"]).decode()

    parser = _make_parser(brunnhilde_version)
    args = parser.parse_args()

    # global variables
    global source, destination, basename, report_dir, csv_dir, log_dir, bulkext_dir, sf_file
    source = os.path.abspath(args.source)
    destination = os.path.abspath(args.destination)
    basename = args.basename
    report_dir = os.path.join(destination, '%s' % basename)
    csv_dir = os.path.join(report_dir, 'csv_reports')
    log_dir = os.path.join(report_dir, 'logs')
    bulkext_dir = os.path.join(report_dir, 'bulk_extractor')
    sf_file = os.path.join(report_dir, 'siegfried.csv')

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

    # create subdirectory for logs if needed
    if args.bulkextractor == False and args.noclam == True:
        pass
    else:
        try:
            os.makedirs(log_dir)
        except OSError as exception:
            if exception.errno != errno.EEXIST:
                raise

    # create html report
    temp_html = os.path.join(report_dir, 'temp.html')
    html = open(temp_html, 'w')

    # open sqlite db
    db = os.path.join(report_dir, 'siegfried.sqlite')
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
            carvefiles = "bash /usr/share/hfsexplorer/bin/unhfs -v -resforks APPLEDOUBLE -o '%s' '%s'" % (tempdir, source)
            print("\nAttempting to carve files from disk image using HFS Explorer.")
            try:
                subprocess.call(carvefiles, shell=True)
                print("\nFile carving successful.")
            except subprocess.CalledProcessError as e:
                print(e.output)
                print("\nBrunnhilde was unable to export files from disk image. Ending process.")
                shutil.rmtree(report_dir)
                sys.exit()

        else: # non-hfs disks (note: no UDF support yet)
            print("\nAttempting to carve files from disk image using tsk_recover.")
            # recover allocated or all files depending on user input
            if args.allocated == True:
                carvefiles = ['tsk_recover', '-a', source, tempdir]
            else:
                carvefiles = ['tsk_recover', '-e', source, tempdir]

            # add optional user-supplied inputs at appropriate list indices
            if args.tsk_fstype:
                carvefiles.insert(3, '-f')
                carvefiles.insert(4, args.tsk_fstype)
            if args.tsk_imgtype:
                carvefiles.insert(3, '-i')
                carvefiles.insert(4, args.tsk_imgtype)
            if args.tsk_sector_offset:
                carvefiles.insert(3, '-o')
                carvefiles.insert(4, args.tsk_sector_offset)

            # call command
            try:
                subprocess.check_output(carvefiles)
                print("\nFile carving successful.")
            except subprocess.CalledProcessError as e:
                print(e.output)
                print("\nBrunnhilde was unable to export files from disk image. Ending process.")
                shutil.rmtree(report_dir)
                sys.exit()

        # process tempdir
        if args.noclam == False: # run clamAV virus check unless specified otherwise
            run_clamav(tempdir)
        process_content(args, tempdir, cursor, conn, html, brunnhilde_version, siegfried_version)
        if args.bulkextractor == True: # bulk extractor option is chosen
            run_bulkext(tempdir)
            write_html('Personally Identifiable Information (PII)', '%s' % os.path.join(bulkext_dir, 'pii.txt'), '\t', html)
        if args.removefiles == True:
            shutil.rmtree(tempdir)


    else: #source is a directory
        if os.path.isdir(source) == False:
            print("\nSource is not a Directory. If you're processing a disk image, place '-d' before source.")
            sys.exit()
        if args.noclam == False: # run clamAV virus check unless specified otherwise
            run_clamav(source)
        process_content(args, source, cursor, conn, html, brunnhilde_version, siegfried_version)
        if args.bulkextractor == True: # bulk extractor option is chosen
            run_bulkext(source)
            write_html('Personally Identifiable Information (PII)', '%s' % os.path.join(bulkext_dir, 'pii.txt'), '\t', html)

    # close HTML file
    html.close()

    # write new html file, with hrefs for PRONOM IDs
    new_html = os.path.join(report_dir, '%s.html' % basename)
    write_pronom_links(temp_html, new_html)

    # remove temp html file
    os.remove(temp_html)

    # close database connections
    cursor.close()
    conn.close()

    print("\nBrunnhilde characterization complete. Reports in %s." % report_dir)

if __name__ == '__main__':
    main()
