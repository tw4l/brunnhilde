# encoding: utf-8
from __future__ import print_function, unicode_literals

import datetime
import os
import shutil
import subprocess
import sys
import tempfile
import unittest
from os.path import join as j


def is_non_zero_file(fpath):
    return os.path.isfile(fpath) and os.path.getsize(fpath) > 0


class SelfCleaningTestCase(unittest.TestCase):
    """TestCase subclass which cleans up self.tmpdir after each test"""

    def setUp(self):
        super(SelfCleaningTestCase, self).setUp()

        # tempdir for brunnhilde outputs
        self.dest_tmpdir = tempfile.mkdtemp()
        if not os.path.isdir(self.dest_tmpdir):
            os.mkdirs(self.dest_tmpdir)

        self.TEST_REPORT_DIR = os.path.join(self.dest_tmpdir, "test")

    def tearDown(self):
        if os.path.isdir(self.dest_tmpdir):
            shutil.rmtree(self.dest_tmpdir)

        super(SelfCleaningTestCase, self).tearDown()


class TestBrunnhildeIntegration(SelfCleaningTestCase):
    """
    Integration tests. sf (Siegfried) must be installed on user's system for tests to work.
    """

    def test_integration_existing_output_dir_quits(self):
        os.makedirs(self.TEST_REPORT_DIR)
        subprocess.call(
            'python brunnhilde.py -n ./test-data/files/ "%s" test' % (self.dest_tmpdir),
            shell=True,
        )
        self.assertFalse(is_non_zero_file(j(self.TEST_REPORT_DIR, "siegfried.csv")))

    def test_integration_existing_output_dir_overwrites(self):
        os.makedirs(self.TEST_REPORT_DIR)
        subprocess.call(
            'python brunnhilde.py -n --overwrite ./test-data/files/ "%s" test'
            % (self.dest_tmpdir),
            shell=True,
        )
        self.assertTrue(is_non_zero_file(j(self.TEST_REPORT_DIR, "siegfried.csv")))
        self.assertTrue(is_non_zero_file(j(self.TEST_REPORT_DIR, "report.html")))

    def test_integration_simple_positional_args(self):
        """Test `brunnhilde.py src dest` syntax introduced in 1.9.0.
        """
        subprocess.call(
            'python brunnhilde.py -n ./test-data/files/ "%s"' % (self.TEST_REPORT_DIR),
            shell=True,
        )
        self.assertTrue(is_non_zero_file(j(self.TEST_REPORT_DIR, "siegfried.csv")))
        self.assertTrue(is_non_zero_file(j(self.TEST_REPORT_DIR, "report.html")))

    def test_integration_outputs_created(self):
        subprocess.call(
            'python brunnhilde.py -n ./test-data/files/ "%s" test' % (self.dest_tmpdir),
            shell=True,
        )
        # siegfried csv and sqlite db
        self.assertTrue(is_non_zero_file(j(self.TEST_REPORT_DIR, "siegfried.csv")))
        # html report
        self.assertTrue(is_non_zero_file(j(self.TEST_REPORT_DIR, "report.html")))
        # csv reports
        self.assertTrue(
            is_non_zero_file(j(self.TEST_REPORT_DIR, "csv_reports", "formats.csv"))
        )
        self.assertTrue(
            is_non_zero_file(
                j(self.TEST_REPORT_DIR, "csv_reports", "formatVersions.csv")
            )
        )
        self.assertTrue(
            is_non_zero_file(j(self.TEST_REPORT_DIR, "csv_reports", "mimetypes.csv"))
        )
        self.assertTrue(
            is_non_zero_file(j(self.TEST_REPORT_DIR, "csv_reports", "years.csv"))
        )
        # tree.txt
        if not sys.platform.startswith("win"):
            self.assertTrue(os.path.isfile(j(self.TEST_REPORT_DIR, "tree.txt")))

    def test_integration_outputs_created_diskimage(self):
        subprocess.call(
            'python brunnhilde.py -nd ./test-data/diskimages/sample-floppy-fat.dd "%s" test'
            % (self.dest_tmpdir),
            shell=True,
        )
        # siegfried csv and sqlite db
        self.assertTrue(is_non_zero_file(j(self.TEST_REPORT_DIR, "siegfried.csv")))
        # html report
        self.assertTrue(is_non_zero_file(j(self.TEST_REPORT_DIR, "report.html")))
        # csv reports
        self.assertTrue(
            is_non_zero_file(j(self.TEST_REPORT_DIR, "csv_reports", "formats.csv"))
        )
        self.assertTrue(
            is_non_zero_file(
                j(self.TEST_REPORT_DIR, "csv_reports", "formatVersions.csv")
            )
        )
        self.assertTrue(
            is_non_zero_file(j(self.TEST_REPORT_DIR, "csv_reports", "mimetypes.csv"))
        )
        self.assertTrue(
            is_non_zero_file(j(self.TEST_REPORT_DIR, "csv_reports", "years.csv"))
        )
        # tree.txt
        if not sys.platform.startswith("win"):
            self.assertTrue(os.path.isfile(j(self.TEST_REPORT_DIR, "tree.txt")))
        # dfxml
        self.assertTrue(is_non_zero_file(j(self.TEST_REPORT_DIR, "dfxml.xml")))
        # carved_files
        self.assertTrue(
            is_non_zero_file(j(self.TEST_REPORT_DIR, "carved_files", "file1.txt.txt"))
        )
        self.assertTrue(
            is_non_zero_file(j(self.TEST_REPORT_DIR, "carved_files", "Tulips.jpg"))
        )

    def test_integration_temp_files_deleted(self):
        subprocess.call(
            'python brunnhilde.py -n ./test-data/files/ "%s" test' % (self.dest_tmpdir),
            shell=True,
        )
        # uniqueyears.csv
        self.assertFalse(
            os.path.isfile(j(self.TEST_REPORT_DIR, "csv_reports", "uniqueyears.csv"))
        )

    def test_integration_clamav(self):
        subprocess.call(
            'python brunnhilde.py ./test-data/files/ "%s" test' % (self.dest_tmpdir),
            shell=True,
        )
        # virus log correctly written
        virus_log = j(self.TEST_REPORT_DIR, "logs", "viruscheck-log.txt")
        with open(virus_log, "r") as f:
            self.assertTrue("Scanned files: 4" in f.read())
        with open(virus_log, "r") as f:
            self.assertTrue("Infected files: 0" in f.read())

    def test_integration_clamav_largefiles(self):
        subprocess.call(
            'python brunnhilde.py -l ./test-data/files/ "%s" test' % (self.dest_tmpdir),
            shell=True,
        )
        # virus log correctly written
        virus_log = j(self.TEST_REPORT_DIR, "logs", "viruscheck-log.txt")
        with open(virus_log, "r") as f:
            self.assertTrue("Scanned files: 4" in f.read())
        with open(virus_log, "r") as f:
            self.assertTrue("Infected files: 0" in f.read())

    def test_integration_clamav_diskimage(self):
        subprocess.call(
            'python brunnhilde.py -d ./test-data/diskimages/sample-floppy-fat.dd "%s" test'
            % (self.dest_tmpdir),
            shell=True,
        )
        # virus log correctly written
        virus_log = j(self.TEST_REPORT_DIR, "logs", "viruscheck-log.txt")
        with open(virus_log, "r") as f:
            self.assertTrue("Scanned files: 2" in f.read())
        with open(virus_log, "r") as f:
            self.assertTrue("Infected files: 0" in f.read())

    def test_integration_retain_sqlite_db(self):
        subprocess.call(
            'python brunnhilde.py -k ./test-data/files/ "%s" test' % (self.dest_tmpdir),
            shell=True,
        )
        self.assertTrue(is_non_zero_file(j(self.TEST_REPORT_DIR, "siegfried.sqlite")))


if __name__ == "__main__":
    unittest.main()
