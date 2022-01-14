#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Brunnhilde
---

A Siegfried-based characterization tool for disk images and directories.

For information on usage and dependencies, see: github.com/tw4l/brunnhilde

Python 2.7 & 3.4+

The MIT License (MIT)
Copyright (c) 2017-2020 Tessa Walsh
https://bitarchivist.net

"""
from __future__ import print_function

import argparse
from collections import OrderedDict
import csv
import datetime
import errno
from itertools import islice
import logging
import math
import os
import re
import requests
import shutil
import sqlite3
import subprocess
import sys


BRUNNHILDE_VERSION = "brunnhilde 1.9.3"

CSS = """
body {
  font-family: Arial, Helvetica, sans-serif;
  margin: 100px 20px 20px 20px;
  padding: 10px;
  width: 95%;
}

header {
  position: fixed;
  top: 0;
  width: 95%;
  padding-bottom: 10px;
  border-bottom: 2px solid #000;
  background: white;
  z-index: 1001;
}

h1 {
  margin-bottom: 10px;
}

nav a {
  padding-right: 10px;
}

nav a:not(:first-child) {
  padding-left: 10px;
}

nav a:not(:last-child) {
  border-right: 1px solid #ddd;
}

div {
  padding-bottom: 10px;
}

table {
  border-collapse: collapse;
}

td {
  border-bottom: 1px solid #ddd;
  padding: 10px 20px 6px 20px;
}

td:not(:last-child) {
  border-right: 1px solid #ddd;
}

th {
  border-bottom: 2px solid #ddd;
  padding: 10px 20px 6px 20px;
  background-color: #f5f5f5;
}

th:not(:last-child) {
  border-right: 1px solid #ddd;
}

tr:hover {
  background-color: #f5f5f5;
}

a {
  color: #007BFF;
  text-decoration: none;
}

a.anchor {
  display: block;
  position: relative;
  top: -120px;
  visibility: hidden;
}

hr {
  width: 25%;
  color: #ddd;
  text-align: left;
  margin-left: 0;
}

.hidden {
  display: none;
}
"""


def _configure_logging():
    global logger
    logger = logging.getLogger()
    logger.setLevel(logging.INFO)
    handler = logging.StreamHandler(stream=sys.stdout)
    formatter = logging.Formatter("%(asctime)s - %(levelname)s - %(message)s")
    handler.setFormatter(formatter)
    logger.addHandler(handler)


def log_info(msg, time_warning=False):
    """Log info message with optional time warning"""
    if time_warning:
        msg += " This might take a while..."
    logger.info(msg)


def log_error_and_exit_message(msg):
    """Log error and shutdown message"""
    shutdown_msg = "Brunnhilde was unable to finish processing. Shutting down."
    logger.error(msg)
    logger.error(shutdown_msg)


def _determine_hash_type(args):
    """Return hash_type value to use as argument for Siegfried

    Defaults to md5 if no or invalid user input.
    """
    HASH_CHOICES = ("sha1", "sha256", "sha512")
    if args.hash and args.hash.lower() in HASH_CHOICES:
        return args.hash.lower()
    return "md5"


def run_siegfried(args, source_dir, use_hash):
    """Run siegfried on directory"""
    log_info("Running Siegfried.", time_warning=True)
    global sf_command
    if use_hash:
        hash_type = _determine_hash_type(args)
        sf_command = 'sf -csv -hash %s "%s" > "%s"' % (hash_type, source_dir, sf_file)
    else:
        sf_command = 'sf -csv "%s" > "%s"' % (source_dir, sf_file)
    if args.scanarchives:
        sf_command = sf_command.replace("sf -csv", "sf -z -csv")
    if args.throttle:
        sf_command = sf_command.replace("-csv -hash", "-csv -throttle 10ms -hash")
    if args.verbosesf:
        sf_command = sf_command.replace(" -hash", " -log p,t -hash")
    subprocess.call(sf_command, shell=True)
    log_info("Siegfried scan complete. Processing results.")


def run_clamav(args, source_dir):
    """Run ClamAV on directory"""
    timestamp = str(datetime.datetime.now())
    log_info("Running virus scan.", time_warning=True)
    virus_log = os.path.join(log_dir, "viruscheck-log.txt")
    if args.largefiles:
        if sys.platform.startswith("win"):
            clamav_command = (
                'clamscan -i -r "%s" --max-scansize=0 --max-filesize=0 > "%s"'
                % (source_dir, virus_log)
            )
        else:
            clamav_command = (
                'clamscan -i -r "%s" --max-scansize=0 --max-filesize=0 | tee "%s"'
                % (source_dir, virus_log)
            )
            
    else:
        if sys.platform.startswith("win"):
            clamav_command = 'clamscan -i -r "%s" > "%s"' % (source_dir, virus_log)
        else:
            clamav_command = 'clamscan -i -r "%s" | tee "%s"' % (source_dir, virus_log)
    subprocess.call(clamav_command, shell=True)
    # add timestamp
    target = open(virus_log, "a")
    target.write("Date scanned: %s" % timestamp)
    target.close()
    # check log for infected files
    if os.path.getsize(virus_log) > 40:  # check to see if clamscan actually ran
        if "Infected files: 0" not in open(virus_log).read():
            logger.warning(
                "INFECTED FILE(S) FOUND. See {} for details.".format(virus_log)
            )
        else:
            log_info("No viruses found.")
    else:
        logger.warning("ClamAV not properly configured.")


def run_bulk_extractor(args, source_dir, ssn_mode):
    """Run bulk extractor on directory"""
    bulk_extractor_log = os.path.join(log_dir, "bulk_extractor-log.txt")
    log_info("Running bulk_extractor.", time_warning=True)
    try:
        os.makedirs(bulkext_dir)
    except OSError as exception:
        if exception.errno != errno.EEXIST:
            raise
    cmd = [
        "bulk_extractor",
        "-o",
        bulkext_dir,
        "-S",
        "ssn_mode={}".format(str(ssn_mode)),
        "-R",
        source_dir,
    ]
    if args.regex:
        cmd.insert(1, "-F")
        cmd.insert(2, args.regex)
    try:
        if sys.version_info > (3, 0):
            log_file = open(bulk_extractor_log, "w", encoding="utf-8")
        else:
            log_file = open(bulk_extractor_log, "wb")
        subprocess.call(cmd, stderr=subprocess.STDOUT, stdout=log_file)
        log_file.close()
        log_info("bulk_extractor scan complete.")
    except subprocess.CalledProcessError as e:
        logger.warning("Error running bulk_extractor: {}".format(e))


def convert_size(size):
    """Convert size in bytes to human-readable expression"""
    if size == 0:
        return "0 bytes"
    size_name = ("bytes", "KB", "MB", "GB", "TB", "PB", "EB", "ZB", "YB")
    i = int(math.floor(math.log(size, 1024)))
    p = math.pow(1024, i)
    s = round(size / p)
    s = str(s)
    s = s.replace(".0", "")
    return "%s %s" % (s, size_name[i])


def import_csv(cursor, conn, use_hash):
    """Import csv file into sqlite db

    Returns use_hash as a mechanism for updating the value if the input
    Siegfried CSV is found to have a hash column. This provides a
    double-check for Siegfried CSVs provided as input from stdin or a
    file and prevents users from having to use the --hash flag when
    providing their own inputs.
    """
    # Create CSV reader
    if sys.version_info > (3, 0):
        f = open(sf_file, "r", encoding="utf8")
    else:
        f = open(sf_file, "rb")
    try:
        reader = csv.reader(
            x.replace("\0", "") for x in f
        )  # replace null bytes with empty strings on read
    except UnicodeDecodeError:
        f = (x.encode("utf-8").strip() for x in f)  # skip non-utf8 encodable characters
        reader = csv.reader(
            x.replace("\0", "") for x in f
        )  # replace null bytes with empty strings on read

    # Read CSV into database
    header = True
    for row in reader:
        if header:
            header = False  # gather column names from first row of csv
            sql = "DROP TABLE IF EXISTS siegfried"
            cursor.execute(sql)

            # If Siegfried CSV has 'hash' column, set use_hash to true
            NUMBER_OF_COLUMNS_WITH_HASH = 12
            use_hash = False
            if len(row) == NUMBER_OF_COLUMNS_WITH_HASH:
                use_hash = True

            sql = "CREATE TABLE siegfried (filename text, filesize text, modified text, errors text, namespace text, id text, format text, version text, mime text, basis text, warning text)"
            if use_hash:
                sql = "CREATE TABLE siegfried (filename text, filesize text, modified text, errors text, hash text, namespace text, id text, format text, version text, mime text, basis text, warning text)"

            cursor.execute(sql)

            insertsql = "INSERT INTO siegfried VALUES (%s)" % (
                ", ".join(["?" for column in row])
            )
            rowlen = len(row)
        else:
            # skip lines that don't have right number of columns
            if len(row) == rowlen:
                cursor.execute(insertsql, row)
    conn.commit()
    f.close()
    return use_hash


def create_html_report(
    args, source_dir, scan_started, cursor, html, siegfried_version, use_hash,
):
    """Get aggregate statistics and write to html report"""
    # Gather stats from database.
    cursor.execute("SELECT COUNT(*) from siegfried;")  # total files
    num_files = cursor.fetchone()[0]

    cursor.execute("SELECT COUNT(*) from siegfried where filesize='0';")  # empty files
    empty_files = cursor.fetchone()[0]

    if use_hash:
        cursor.execute(
            "SELECT COUNT(DISTINCT hash) from siegfried WHERE filesize<>'0';"
        )  # distinct files
        distinct_files = cursor.fetchone()[0]

        cursor.execute(
            "SELECT COALESCE(SUM(hash_count), 0) FROM (SELECT COUNT(hash) as hash_count FROM siegfried WHERE filesize<>'0' GROUP BY hash HAVING COUNT(hash) > 1 AND COUNT(DISTINCT filename) > 1);"
        )  # duplicates
        all_dupes = cursor.fetchone()[0]

        cursor.execute(
            "SELECT COUNT(DISTINCT hash) FROM (SELECT hash FROM siegfried WHERE filesize<>'0' GROUP BY hash HAVING COUNT(hash) > 1 AND COUNT(DISTINCT filename) > 1);"
        )  # distinct duplicates
        distinct_dupes = cursor.fetchone()[0]

        duplicate_copies = int(all_dupes) - int(
            distinct_dupes
        )  # number of duplicate copies of unique files
        duplicate_copies = str(duplicate_copies)

    cursor.execute(
        "SELECT COUNT(*) FROM siegfried WHERE id='UNKNOWN';"
    )  # unidentified files
    unidentified_files = cursor.fetchone()[0]

    year_sql = "SELECT DISTINCT SUBSTR(modified, 1, 4) as 'year' FROM siegfried;"  # min and max year
    year_path = os.path.join(csv_dir, "uniqueyears.csv")
    # if python3, specify newline to prevent extra csv line in windows
    # else, open and read csv in bytes mode
    # see: https://stackoverflow.com/questions/3348460/csv-file-written-with-python-has-blank-lines-between-each-row
    if sys.version_info > (3, 0):
        year_report = open(year_path, "w", newline="")
    else:
        year_report = open(year_path, "wb")
    w = csv.writer(year_report)
    for row in cursor.execute(year_sql):
        w.writerow(row)
    year_report.close()

    if sys.version_info > (3, 0):
        year_report_read = open(year_path, "r", newline="")
    else:
        year_report_read = open(year_path, "rb")
    r = csv.reader(year_report_read)
    years = []
    for row in r:
        if row:
            years.append(row[0])
    if not years:
        begin_date = "N/A"
        end_date = "N/A"
    else:
        begin_date = min(years, key=float)
        end_date = max(years, key=float)
    year_report_read.close()

    # delete temporary uniqueyear file from csv reports dir
    os.remove(year_path)

    datemodified_sql = (
        "SELECT DISTINCT modified FROM siegfried;"  # min and max full modified date
    )
    datemodified_path = os.path.join(csv_dir, "datemodified.csv")
    # specify newline in python3 to prevent extra csv lines in windows
    # read and write csv in byte mode in python2
    if sys.version_info > (3, 0):
        date_report = open(datemodified_path, "w", newline="")
    else:
        date_report = open(datemodified_path, "wb")
    w = csv.writer(date_report)
    for row in cursor.execute(datemodified_sql):
        w.writerow(row)
    date_report.close()

    if sys.version_info > (3, 0):
        date_report_read = open(datemodified_path, "r", newline="")
    else:
        date_report_read = open(datemodified_path, "rb")
    r = csv.reader(date_report_read)
    dates = []
    for row in r:
        if row:
            dates.append(row[0])
    if not dates:
        earliest_date = "N/A"
        latest_date = "N/A"
    else:
        earliest_date = min(dates)
        latest_date = max(dates)
    date_report_read.close()

    os.remove(
        datemodified_path
    )  # delete temporary datemodified file from csv reports dir

    cursor.execute(
        "SELECT COUNT(DISTINCT format) as formats from siegfried WHERE format <> '';"
    )  # number of identfied file formats
    num_formats = cursor.fetchone()[0]

    cursor.execute(
        "SELECT COUNT(*) FROM siegfried WHERE errors <> '';"
    )  # number of siegfried errors
    num_errors = cursor.fetchone()[0]

    cursor.execute(
        "SELECT COUNT(*) FROM siegfried WHERE warning <> '';"
    )  # number of siegfried warnings
    num_warnings = cursor.fetchone()[0]

    # calculate size from recursive dirwalk and format
    size_bytes = 0
    if sys.version_info > (3, 0):
        for root, dirs, files in os.walk(source_dir):
            for f in files:
                file_path = os.path.join(root, f)
                file_info = os.stat(file_path)
                size_bytes += file_info.st_size
    else:
        for root, dirs, files in os.walk(unicode(source_dir, "utf-8")):
            for f in files:
                file_path = os.path.join(root, f)
                try:
                    file_info = os.stat(file_path)
                    size_bytes += file_info.st_size
                except OSError as e:  # report when Brunnhilde can't find file
                    logger.warning(
                        "OSError: {}. File size of this file not included in Brunnhilde HTML report statistics.".format(
                            file_path
                        )
                    )
    size = convert_size(size_bytes)

    # write html
    html.write("<!DOCTYPE html>")
    html.write('\n<html lang="en">')
    html.write("\n<head>")
    html.write("\n<title>Brunnhilde report: {}</title>".format(basename))
    html.write('\n<meta charset="utf-8">')
    html.write('\n<style type="text/css">{}</style>'.format(CSS))
    html.write("\n</head>")
    html.write("\n<body>")

    # navbar
    html.write("\n<header>")
    html.write("\n<h1>Brunnhilde HTML report</h1>")
    html.write("\n<nav>")
    html.write('\n<a href="#Provenance">Provenance</a>')
    html.write('\n<a href="#Stats">Statistics</a>')
    if not (args.noclam or sys.platform.startswith("win")):
        html.write('\n<a href="#Virus report">Virus report</a>')
    html.write('\n<a href="#File formats">File formats</a>')
    html.write('\n<a href="#File format versions">Versions</a>')
    html.write('\n<a href="#MIME types">MIME types</a>')
    html.write('\n<a href="#Last modified dates by year">Dates</a>')
    html.write('\n<a href="#Unidentified">Unidentified</a>')
    if args.warnings:
        html.write('\n<a href="#Warnings">Warnings</a>')
    html.write('\n<a href="#Errors">Errors</a>')
    if use_hash:
        html.write('\n<a href="#Duplicates">Duplicates</a>')
    if args.bulkextractor:
        html.write('\n<a href="#SSNs">SSNs</a>')
    html.write("\n</nav>")
    html.write("\n</header>")

    # provenance
    html.write("\n<div>")
    html.write('\n<a class="anchor" name="Provenance"></a>')
    html.write("\n<h2>Provenance</h2>")
    html.write(
        "\n<p><strong>Input source (directory or disk image):</strong> {}</p>".format(
            source
        )
    )
    html.write("\n<p><strong>Accession/identifier:</strong> {}</p>".format(basename))
    html.write(
        "\n<p><strong>Brunnhilde version:</strong> {}</p>".format(BRUNNHILDE_VERSION)
    )
    if not (args.csv or args.stdin):
        html.write(
            "\n<p><strong>Siegfried version:</strong> {}</p>".format(siegfried_version)
        )
        html.write("\n<p><strong>Siegfried command:</strong> {}</p>".format(sf_command))
    html.write("\n<p><strong>Scan started:</strong> {}</p>".format(scan_started))
    html.write("\n</div>")

    # statistics
    html.write("\n<div>")
    html.write('\n<a class="anchor" name="Stats"></a>')
    html.write("\n<h2>Statistics</h2>")
    html.write("\n<p><strong>Total files:</strong> {}</p>".format(num_files))
    html.write("\n<p><strong>Total size:</strong> {}</p>".format(size))
    if use_hash:
        html.write(
            "\n<p><strong>Distinct files:</strong> {}</p>".format(distinct_files)
        )
        html.write("\n<p><strong>Duplicates:</strong> {}".format(duplicate_copies))
        if duplicate_copies:
            html.write(
                ' (of {} distinct files) <a href="#Duplicates">(see list)</a></p>'.format(
                    distinct_dupes
                )
            )
        else:
            html.write(' <a href="#Duplicates">(see list)</a></p>')
    html.write(
        "\n<p><strong>Empty (zero byte) files:</strong> {}</p>".format(empty_files)
    )
    html.write("\n<hr>")
    html.write(
        "\n<p><strong>Years (last modified):</strong> {begin} - {end}</p>".format(
            begin=begin_date, end=end_date
        )
    )
    html.write("\n<p><strong>Earliest date:</strong> {}</p>".format(earliest_date))
    html.write("\n<p><strong>Latest date:</strong> {}</p>".format(latest_date))
    html.write("\n<hr>")
    html.write(
        "\n<p><strong>Identified file formats:</strong> {}</p>".format(num_formats)
    )
    html.write(
        "\n<p><strong>Unidentified files:</strong> {}".format(unidentified_files)
    )
    if unidentified_files:
        html.write(' <a href="#Unidentified">(see list)</a></p>')
    else:
        html.write(" </p>")
    html.write("\n<hr>")
    if args.warnings:
        html.write("\n<p><strong>Siegfried warnings:</strong> {}".format(num_warnings))
        if num_warnings:
            html.write(' <a href="#Warnings">(see list)</a></p>')
        else:
            html.write(" </p>")
    html.write("\n<p><strong>Siegfried errors:</strong> {}".format(num_errors))
    if num_errors:
        html.write(' <a href="#Errors">(see list)</a></p>')
    else:
        html.write(" </p>")
    html.write("\n</div>")

    # virus report
    if not (args.noclam or sys.platform.startswith("win")):
        html.write("\n<div>")
        html.write('\n<a class="anchor" name="Virus report"></a>')
        html.write("\n<h2>Virus report</h2>")
        with open(os.path.join(log_dir, "viruscheck-log.txt")) as f:
            for line in f:
                html.write("\n<p>{}</p>".format(line))
        html.write("\n</div>")


def generate_reports(args, cursor, html, use_hash):
    """Run sql queries on db to generate reports, write to csv and html"""
    full_header = [
        "Filename",
        "Filesize",
        "Date modified",
        "Errors",
        "Namespace",
        "ID",
        "Format",
        "Format version",
        "MIME type",
        "Basis for ID",
        "Warning",
    ]
    if use_hash:
        full_header.insert(4, "Checksum")

    # sorted format list report
    sql = "SELECT format, id, COUNT(*) as 'num' FROM siegfried GROUP BY format ORDER BY num DESC"
    path = os.path.join(csv_dir, "formats.csv")
    format_header = ["Format", "ID", "Count"]
    sqlite_to_csv(sql, path, format_header, cursor)
    write_html_report_section("File formats", path, ",", html)

    # sorted format and version list report
    sql = "SELECT format, id, version, COUNT(*) as 'num' FROM siegfried GROUP BY format, version ORDER BY num DESC"
    path = os.path.join(csv_dir, "formatVersions.csv")
    version_header = ["Format", "ID", "Version", "Count"]
    sqlite_to_csv(sql, path, version_header, cursor)
    write_html_report_section("File format versions", path, ",", html)

    # sorted mimetype list report
    sql = (
        "SELECT mime, COUNT(*) as 'num' FROM siegfried GROUP BY mime ORDER BY num DESC"
    )
    path = os.path.join(csv_dir, "mimetypes.csv")
    mime_header = ["MIME type", "Count"]
    sqlite_to_csv(sql, path, mime_header, cursor)
    write_html_report_section("MIME types", path, ",", html)

    # dates report
    sql = "SELECT SUBSTR(modified, 1, 4) as 'year', COUNT(*) as 'num' FROM siegfried GROUP BY year ORDER BY num DESC"
    path = os.path.join(csv_dir, "years.csv")
    year_header = ["Year Last Modified", "Count"]
    sqlite_to_csv(sql, path, year_header, cursor)
    write_html_report_section("Last modified dates by year", path, ",", html)

    # unidentified files report
    sql = "SELECT filename, filesize, modified FROM siegfried WHERE id='UNKNOWN';"
    path = os.path.join(csv_dir, "unidentified.csv")
    unidentified_header = ["File", "Size", "Date Modified"]
    sqlite_to_csv(sql, path, unidentified_header, cursor)
    write_html_report_section("Unidentified", path, ",", html)

    # warnings report
    sql = "SELECT filename, errors, id, format, version, basis, warning FROM siegfried WHERE warning <> '';"
    path = os.path.join(csv_dir, "warnings.csv")
    warnings_header = [
        "File",
        "Errors",
        "ID",
        "Format",
        "Version",
        "Basis for ID",
        "Warning",
    ]
    sqlite_to_csv(sql, path, warnings_header, cursor)
    if args.warnings:
        write_html_report_section("Warnings", path, ",", html)

    # errors report
    sql = "SELECT filename, filesize, modified, errors, warning FROM siegfried WHERE errors <> '';"
    path = os.path.join(csv_dir, "errors.csv")
    errors_header = ["File", "Size", "Date Modified", "Errors", "Warnings"]
    sqlite_to_csv(sql, path, errors_header, cursor)
    write_html_report_section("Errors", path, ",", html)

    if use_hash:
        # duplicates report
        sql = "SELECT * FROM siegfried WHERE hash IN (SELECT hash FROM siegfried WHERE filesize<>'0' GROUP BY hash HAVING COUNT(hash) > 1 AND COUNT(DISTINCT filename) > 1) ORDER BY hash;"
        path = os.path.join(csv_dir, "duplicates.csv")
        sqlite_to_csv(sql, path, full_header, cursor)
        write_html_report_section("Duplicates", path, ",", html)


def sqlite_to_csv(sql, path, header, cursor):
    """Execute SQL query and write results, if any, to a CSV file

    In Python 3, specify newline to prevent extra lines in Windows.
    In Python 2, write the CSV in byte mode.
    """
    cursor.execute(sql)
    results = cursor.fetchall()
    if not results:
        return
    if sys.version_info > (3, 0):
        report = open(path, "w", newline="", encoding="utf8")
    else:
        report = open(path, "wb")
    w = csv.writer(report)
    w.writerow(header)
    for row in results:
        w.writerow(row)
    report.close()


def write_html_report_section(header, path, file_delimiter, html):
    """Write HTML report section from input CSV file or bulk_extractor feature file

    If expected source doesn't exist, write default message instead.
    """
    input_exists = True
    if os.path.isfile(path) and os.path.getsize(path) > 0:
        if sys.version_info > (3, 0):
            in_file = open(path, "r", encoding="utf8")
        else:
            in_file = open(path, "rb")
        # open csv reader
        r = csv.reader(in_file, delimiter="%s" % file_delimiter)
    else:
        input_exists = False

    # write header
    html.write("\n<div>")
    html.write('\n<a class="anchor" name="{}"></a>'.format(header))
    html.write("\n<h2>{}</h2>".format(header))
    if header == "Duplicates":
        html.write("\n<p><em>Duplicates are grouped by hash value.</em></p>")
    elif header == "SSNs":
        html.write(
            "\n<p><em>Potential Social Security Numbers identified by bulk_extractor.</em></p>"
        )

    DEFAULT_TEXT = "\nNone found.\n<br><br>"
    if not input_exists:
        html.write(DEFAULT_TEXT)
        html.write("\n</div>")
        return

    # if writing PII, handle separately
    if header == "SSNs":
        html.write("\n<table>")
        # write header
        html.write("\n<thead>")
        html.write("\n<tr>")
        html.write("\n<th>File</th>")
        html.write("\n<th>Feature</th>")
        html.write("\n<th>Context</th>")
        html.write("\n</tr>")
        html.write("\n</thead>")
        # write data
        html.write("\n<tbody>")
        for row in islice(r, 4, None):  # skip header lines
            for row in r:
                # write data
                html.write("\n<tr>")
                for column in row:
                    html.write("\n<td>" + column + "</td>")
                html.write("\n</tr>")
        html.write("\n</tbody>")
        html.write("\n</table>")

    # if writing duplicates, handle separately
    elif header == "Duplicates":
        # read md5s from csv and write to dict
        duplicates_dict = {}
        for row in r:
            if row and row[4]:
                hash_value = row[4]
                if hash_value not in duplicates_dict.keys():
                    # Store info from first file with matching hash
                    duplicates_dict[hash_value] = {
                        "info": {
                            "row_size": row[1],
                            "row_errors": row[3],
                            "row_id": row[6],
                            "row_format": row[7],
                            "row_format_version": row[8],
                            "row_mime": row[9],
                            "row_basis": row[10],
                            "row_warning": row[11]
                        },
                        "files": []
                        }
                row_file_info = {"row_filename": row[0], "row_date_modified": row[2]}
                duplicates_dict[hash_value]["files"].append(row_file_info)

        # deduplicate md5_list and remove column header from list
        hash_list = sorted(list(OrderedDict.fromkeys(duplicates_dict)))
        hash_list.remove("Checksum")
        # for each hash in md5_list, print header, file info, and list of matching files
        for hash_value in hash_list:
            html.write(
                "\n<p>Files matching hash <strong>{}</strong>:</p>".format(hash_value)
            )
            # Print info for the group
            hash_info = duplicates_dict[hash_value]["info"]
            row_size_readable = convert_size(int(hash_info["row_size"]))
            html.write("\n<ul>")
            if " bytes" in row_size_readable:
                html.write(
                    "\n<li><strong>Size:</strong> {} bytes</li>".format(
                        hash_info["row_size"]
                    )
                )
            else:
                html.write(
                    "\n<li><strong>Size:</strong> {bytes} bytes ({readable})</li>".format(
                        bytes=hash_info["row_size"], readable=row_size_readable
                    )
                )
            html.write(
                "\n<li><strong>ID:</strong> {}</li>".format(
                    add_pronom_link_for_puids(hash_info["row_id"])
                )
            )
            html.write(
                "\n<li><strong>Format:</strong> {}</li>".format(hash_info["row_format"])
            )
            if hash_info["row_format_version"]:
                html.write(
                    "\n<li><strong>Format version:</strong> {}</li>".format(
                        hash_info["row_format_version"]
                    )
                )
            if hash_info["row_mime"]:
                html.write(
                    "\n<li><strong>MIME type:</strong> {}</li>".format(hash_info["row_mime"])
                )
            if hash_info["row_basis"]:
                html.write(
                    "\n<li><strong>Basis for ID:</strong> {}</li>".format(
                        hash_info["row_basis"]
                    )
                )
            if hash_info["row_warning"]:
                html.write(
                    "\n<li><strong>Warning:</strong> {}</li>".format(
                        hash_info["row_warning"]
                    )
                )
            if hash_info["row_errors"]:
                html.write(
                    "\n<li><strong>Errors:</strong> {}</li>".format(hash_info["row_errors"])
                )
            html.write("\n</ul>")

            # Write table of matching files (columns: filename, modified date)
            html.write("\n<table>")
            html.write("\n<thead>")
            html.write("\n<tr>")
            html.write("\n<th>Filename</th><th>Date modified</th>")
            html.write("\n</tr>")
            html.write("\n</thead>")
            html.write("\n<tbody>")
            for file_info in duplicates_dict[hash_value]["files"]:
                # write data
                html.write("\n<tr>")
                html.write("\n<td>" + file_info["row_filename"] + "</td>")
                html.write("\n<td>" + file_info["row_date_modified"] + "</td>")
                html.write("\n</tr>")
            html.write("\n</tbody>")
            html.write("\n</table>")
            html.write("<br>")

    # otherwise write as normal
    else:
        html.write("\n<table>")
        # write header row
        html.write("\n<thead>")
        html.write("\n<tr>")
        row1 = next(r)
        for column in row1:
            html.write("\n<th>" + column + "</th>")
        html.write("\n</tr>")
        html.write("\n</thead>")
        # write data rows
        html.write("\n<tbody>")
        for row in r:
            # write data
            html.write("\n<tr>")
            for column in row:
                column = add_pronom_link_for_puids(column)
                html.write("\n<td>" + column + "</td>")
            html.write("\n</tr>")
        html.write("\n</tbody>")
        html.write("\n</table>")

    html.write("\n</div>")
    in_file.close()


def _return_csv_reader_to_start_of_file(csv_reader_instance):
    csv_reader_instance.seek(0)


def add_pronom_link_for_puids(text):
    """If text is a PUID, add a link to the PRONOM website"""
    PUID_REGEX = r"fmt\/[0-9]+|x\-fmt\/[0-9]+"  # regex to match fmt/# or x-fmt/#
    if re.match(PUID_REGEX, text) is not None:
        return '<a href="https://nationalarchives.gov.uk/PRONOM/{}" target="_blank">{}</a>'.format(
            text, text
        )
    return text


def close_html_report(html):
    """Add JavaScript and write html closing tags"""
    html.write("\n</body>")
    html.write("\n</html>")


def make_tree(source_dir):
    """Call tree on source directory and save output to tree.txt"""
    tree_command = 'tree -tDhR "%s" > "%s"' % (
        source_dir,
        os.path.join(report_dir, "tree.txt"),
    )
    subprocess.call(tree_command, shell=True)


def accept_or_run_siegfried(args, source_dir, use_hash):
    """Write file/stdin Siegfried CSV to sf_file or run Siegfried to create it"""
    if args.csv:
        try:
            shutil.copyfile(os.path.abspath(args.csv), sf_file)
        except (IOError, OSError) as e:
            log_error_and_exit_message("Unable to copy CSV file: {}".format(e))
            sys.exit(1)

    elif args.stdin:
        try:
            if sys.version_info > (3, 0):
                csv_out = open(sf_file, "w", newline="")
            else:
                csv_out = open(sf_file, "wb")
            csv_writer = csv.writer(csv_out)
            csv_reader = csv.reader(sys.stdin, delimiter=",")
            for line in csv_reader:
                csv_writer.writerow(line)
            csv_out.close()
        except Exception as e:
            log_error_and_exit_message(
                "Unable to read CSV from piped stdin: {}".format(e)
            )
            sys.exit(1)

    else:
        run_siegfried(args, source_dir, use_hash)


def process_content(
    args, source_dir, cursor, conn, html, siegfried_version, use_hash, ssn_mode,
):
    """Run through main processing flow on specified directory"""
    scan_started = str(datetime.datetime.now())
    accept_or_run_siegfried(args, source_dir, use_hash)
    use_hash = import_csv(cursor, conn, use_hash)
    create_html_report(
        args, source_dir, scan_started, cursor, html, siegfried_version, use_hash,
    )
    generate_reports(args, cursor, html, use_hash)
    if args.bulkextractor:
        run_bulk_extractor(args, source_dir, ssn_mode)
        write_html_report_section(
            "SSNs", os.path.join(bulkext_dir, "pii.txt"), "\t", html
        )
    close_html_report(html)  # close HTML file tags
    if not sys.platform.startswith("win"):
        make_tree(source_dir)  # create tree.txt on mac and linux machines


def carve_files_with_unhfs(args, html, out_dir, disk_image):
    """Carve files from HFS disk image"""
    if sys.platform.startswith("linux"):
        unhfs_bin = "/usr/share/hfsexplorer/bin/unhfs"
    elif sys.platform.startswith("darwin"):
        unhfs_bin = "/usr/local/share/hfsexplorer/bin/unhfs"
    # TODO: Add else statement with path to unhfs binary on windows

    cmd = [unhfs_bin, "-v", "-o", out_dir, disk_image]
    if args.hfs_resforks:
        cmd.insert(1, "-resforks")
        cmd.insert(2, "APPLEDOUBLE")
    if args.hfs_partition:
        cmd.insert(1, "-partition")
        cmd.insert(2, str(args.hfs_partition))
    if args.hfs_fsroot:
        cmd.insert(1, "-fsroot")
        cmd.insert(2, args.hfs_fsroot)

    log_info("Attempting to carve files from disk image using HFS Explorer.")
    try:
        subprocess.check_output(cmd)
        log_info("File carving successful.")
    except subprocess.CalledProcessError as e:
        log_error_and_exit_message(
            "Unable to export files from disk image: {}".format(e.output)
        )
        close_files_conns_on_exit(html, conn, cursor, report_dir)
        sys.exit(1)


def carve_files_with_tsk_recover(args, html, out_dir, disk_image):
    """Attempt to carve files from disk image with tsk_recover"""
    mode = "-e"
    if args.allocated:
        mode = "-a"

    cmd = ["tsk_recover", mode, disk_image, out_dir]
    if args.tsk_fstype:
        cmd.insert(2, "-f")
        cmd.insert(3, args.tsk_fstype)
    if args.tsk_imgtype:
        cmd.insert(2, "-i")
        cmd.insert(3, args.tsk_imgtype)
    if args.tsk_sector_offset:
        cmd.insert(2, "-o")
        cmd.insert(3, args.tsk_sector_offset)

    log_info("Attempting to carve files from disk image using tsk_recover.")
    try:
        subprocess.check_output(cmd)
        log_info("File carving successful.")
    except subprocess.CalledProcessError as e:
        log_error_and_exit_message(
            "Unable to export files from disk image: {}".format(e.output)
        )
        close_files_conns_on_exit(html, conn, cursor, report_dir)
        sys.exit(1)


def create_dfxml():
    """Create DFXML with fiwalk"""
    fiwalk_file = os.path.join(report_dir, "dfxml.xml")
    log_info("Attempting to generate DFXML file from disk image using fiwalk.")
    try:
        subprocess.check_output(["fiwalk", "-X", fiwalk_file, source])
        log_info("DFXML file created.")
    except subprocess.CalledProcessError as e:
        logger.warning("Fiwalk could not create DFXML for disk: {}".format(e.output))


def close_files_conns_on_exit(html, conn, cursor, report_dir):
    cursor.close()
    conn.close()
    html.close()
    shutil.rmtree(report_dir)


def _make_parser():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "-a",
        "--allocated",
        help="Instruct tsk_recover to export only allocated files (recovers all files by default)",
        action="store_true",
    )
    parser.add_argument(
        "-b",
        "--bulkextractor",
        help="Run Bulk Extractor on source",
        action="store_true",
    )
    parser.add_argument(
        "--ssn_mode",
        help="Specify ssn_mode for Bulk Extractor (0, 1, or 2)",
        action="store",
        type=int,
    )
    parser.add_argument("--regex", help="Specify path to regex file", action="store")
    parser.add_argument(
        "-d",
        "--diskimage",
        help="Use disk image instead of dir as input (Linux and macOS only)",
        action="store_true",
    )
    parser.add_argument(
        "--hfs", help="Use for raw disk images of HFS disks", action="store_true"
    )
    parser.add_argument(
        "--hfs_resforks",
        "--resforks",
        help="HFS option: Extract AppleDouble resource forks from HFS disks",
        action="store_true",
    )
    parser.add_argument(
        "--hfs_partition",
        help="HFS option: Specify partition number as integer for unhfs to extract (e.g. --hfs_partition 1)",
        action="store",
        type=int,
    )
    parser.add_argument(
        "--hfs_fsroot",
        help="HFS option: Specify POSIX path (file or dir) in the HFS file system for unhfs to extract (e.g. --hfs_fsroot /Users/tessa/backup/)",
        action="store",
        type=str,
    )
    parser.add_argument(
        "--tsk_imgtype",
        help="TSK option: Specify format of image type for tsk_recover. See tsk_recover man page for details",
        action="store",
    )
    parser.add_argument(
        "--tsk_fstype",
        help="TSK option: Specify file system type for tsk_recover. See tsk_recover man page for details",
        action="store",
    )
    parser.add_argument(
        "--tsk_sector_offset",
        help="TSK option: Sector offset for particular volume for tsk_recover to recover",
        action="store",
    )
    parser.add_argument(
        "--hash", help="Specify hash algorithm", dest="hash", action="store", type=str
    )
    parser.add_argument(
        "-k",
        "--keepsqlite",
        help="Retain Brunnhilde-generated sqlite db after processing",
        action="store_true",
    )
    parser.add_argument(
        "-l",
        "--largefiles",
        help="Enable virus scanning of large files",
        action="store_true",
    )
    parser.add_argument(
        "-n", "--noclam", help="Skip ClamAV virus scan", action="store_true"
    )
    parser.add_argument(
        "-r",
        "--removefiles",
        help="Delete 'carved_files' directory when done (disk image input only)",
        action="store_true",
    )
    parser.add_argument(
        "-t",
        "--throttle",
        help="Pause for 1s between Siegfried scans",
        action="store_true",
    )
    parser.add_argument(
        "-v",
        "--verbosesf",
        help="Log verbose Siegfried output to terminal while processing",
        action="store_true",
    )
    parser.add_argument(
        "-V",
        "--version",
        help="Display Brunnhilde version",
        action="version",
        version=BRUNNHILDE_VERSION,
    )
    parser.add_argument(
        "-w",
        "--warnings",
        "--showwarnings",
        help="Add Siegfried warnings to HTML report",
        action="store_true",
    )
    parser.add_argument(
        "-z",
        "--scanarchives",
        help="Decompress and scan zip, tar, gzip, warc, arc with Siegfried",
        action="store_true",
    )
    parser.add_argument(
        "--save_assets",
        help="DEPRECATED. Non-functional in Brunnhilde 1.9.1+ but retained for API stability",
        action="store"
    )
    parser.add_argument(
        "--load_assets",
        help="DEPRECATED. Non-functional in Brunnhilde 1.9.1+ but retained for API stability",
        action="store"
    )
    parser.add_argument(
        "--csv",
        help="Path to Siegfried CSV file to read as input (directories only)",
        action="store",
        type=str,
    )
    parser.add_argument(
        "--stdin",
        help="Read Siegfried CSV from piped stdin (directories only)",
        action="store_true",
    )
    parser.add_argument(
        "-o",
        "--overwrite",
        help="Overwrite reports directory if it already exists",
        action="store_true",
    )
    parser.add_argument(
        "--in-memory-db",
        help="Use in-memory sqlite database rather than writing it to disk",
        action="store_true"
    )
    parser.add_argument("source", help="Path to source directory or disk image")
    parser.add_argument("destination", help="Path to destination for reports")
    parser.add_argument(
        "basename",
        nargs="?",
        default=None,
        help=(
            "DEPRECATED. Accession number or identifier, used as basename for outputs. "
            "Prefer using the new simpler `brunnhilde.py source destination` syntax. "
            "The basename argument is retained for API stability and used when provided."
        ),
    )

    return parser


def main():
    parser = _make_parser()
    args = parser.parse_args()

    _configure_logging()

    global source, destination, basename, report_dir, csv_dir, log_dir, bulkext_dir, sf_file, ssn_mode
    source = os.path.abspath(args.source)
    destination = os.path.abspath(args.destination)
    # Brunnhilde API backward compatibility: Use basename positional
    # arg if provided. Otherwise use destination as report directory.
    if args.basename:
        basename = str(args.basename)
        report_dir = os.path.join(destination, basename)
    else:
        basename = os.path.basename(destination)
        report_dir = destination
    csv_dir = os.path.join(report_dir, "csv_reports")
    log_dir = os.path.join(report_dir, "logs")
    bulkext_dir = os.path.join(report_dir, "bulk_extractor")
    sf_file = os.path.join(report_dir, "siegfried.csv")

    # Create report directory
    if os.path.exists(report_dir):
        if not args.overwrite:
            log_error_and_exit_message(
                "Output directory already exists. To overwrite, use the -o/--overwrite option."
            )
            sys.exit(1)

        try:
            shutil.rmtree(report_dir)
        except OSError as e:
            log_error_and_exit_message(
                "Unable to delete existing output directory: {}".format(e)
            )
            sys.exit(1)

    try:
        os.makedirs(report_dir)
    except OSError as exception:
        if exception.errno != errno.EEXIST:
            raise

    # Check that Siegfried is installed and save version.
    try:
        siegfried_version = subprocess.check_output(["sf", "-version"]).decode()
    except subprocess.CalledProcessError:
        log_error_and_exit_message(
            "Siegfried is not installed or available on PATH. "
            "Please ensure that all dependencies are properly installed."
        )
        sys.exit(1)

    # Check that source type is correct.
    if args.diskimage and not os.path.isfile(source):
        log_error_and_exit_message(
            "Source is not a file. Do not use the -d/--diskimage argument unless source is a disk image."
        )
        sys.exit(1)
    elif not args.diskimage and os.path.isfile(source):
        log_error_and_exit_message(
            "Source is not a directory. Use the -d/--diskimage argument if source is a disk image."
        )
        sys.exit(1)

    # Check that Siegfried CSV options were not used with disk image source.
    if args.diskimage and (args.csv or args.stdin):
        log_error_and_exit_message(
            "Use of the --stdin and --csv options is not supported for disk images."
        )
        sys.exit(1)

    # Print warnings for deprecated flags.
    if args.save_assets or args.load_assets:
        logger.warning(
            "DEPRECATION NOTICE: --save_assets and --load_assets options are "
            "deprecated. In Brunnhilde 1.9+, the HTML report has no external "
            "JavaScript or CSS dependencies to be managed. The flags are "
            "retained for API stability but are no longer functional."
        )
    if args.basename:
        logger.warning(
            "DEPRECATION NOTICE: The basename argument is deprecated in Brunnhilde 1.9.0. "
            "Prefer using the new simpler `brunnhilde.py source destination` syntax. "
            "The basename argument is retained for API stability and used if provided."
        )

    log_info("Brunnhilde started. Source: {}.".format(source))

    use_hash = True
    if args.hash == "none":
        use_hash = False

    ssn_mode = 1
    if args.ssn_mode in (0, 2):
        ssn_mode = args.ssn_mode

    # Create report subdirectories directories
    dirs_to_create = [csv_dir]
    if not (args.bulkextractor is False and args.noclam is True):
        dirs_to_create.append(log_dir)
    for new_dir in dirs_to_create:
        try:
            os.makedirs(new_dir)
        except OSError as exception:
            if exception.errno != errno.EEXIST:
                raise

    # Create html report
    html_report_path = os.path.join(report_dir, "report.html")
    if sys.version_info > (3, 0):
        html = open(html_report_path, "w", encoding="utf8")
    else:
        html = open(html_report_path, "wb")

    # Open database connection and cursor
    db = os.path.join(report_dir, "siegfried.sqlite")
    if args.in_memory_db:
        db = ":memory:"
    conn = sqlite3.connect(db)
    conn.text_factory = str  # allows utf-8 data to be stored
    cursor = conn.cursor()

    # If source is a disk image, carve files for analysis and create DFXML if possible
    if args.diskimage:
        if sys.platform.startswith("win"):
            log_error_and_exit_message(
                "Disk images not supported as inputs in Windows."
            )
            close_files_conns_on_exit(html, conn, cursor, report_dir)
            sys.exit(1)

        tempdir = os.path.join(report_dir, "carved_files")
        try:
            os.makedirs(tempdir)
        except OSError as exception:
            if exception.errno != errno.EEXIST:
                raise

        if args.hfs:
            carve_files_with_unhfs(args, html, tempdir, source)
        else:
            carve_files_with_tsk_recover(args, html, tempdir, source)
            create_dfxml()

        # Use the carved_files directory as source for analysis moving forward
        source = tempdir

    if not args.noclam:
        run_clamav(args, source)

    process_content(
        args, source, cursor, conn, html, siegfried_version, use_hash, ssn_mode,
    )

    # Delete carved_files directory if user elected not to keep it
    if args.diskimage:
        if args.removefiles:
            shutil.rmtree(tempdir)

    # Close HTML file
    html.close()

    # Close database connections
    cursor.close()
    conn.close()

    # Remove sqlite db
    if not args.in_memory_db and not args.keepsqlite:
        os.remove(os.path.join(report_dir, "siegfried.sqlite"))

    log_info(
        "Brunnhilde characterization complete. Reports written to %s." % report_dir
    )


if __name__ == "__main__":
    main()
