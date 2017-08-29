# encoding: utf-8

from __future__ import (print_function, unicode_literals)

import datetime
import logging
import os
import shutil
import subprocess
import sys
import tempfile
import unittest


logging.basicConfig(filename='test.log', level=logging.DEBUG)
stderr = logging.StreamHandler()
stderr.setLevel(logging.WARNING)
logging.getLogger().addHandler(stderr)

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

    def tearDown(self):
        if os.path.isdir(self.dest_tmpdir):
            shutil.rmtree(self.dest_tmpdir)


        super(SelfCleaningTestCase, self).tearDown()

class TestBrunnhildeIntegration(SelfCleaningTestCase):
    """
    Integration tests. sf (Siegfried) must be installed on user's system for tests to work.
    """

    def test_integration_outputs_created(self):
        subprocess.call('python ./brunnhilde.py ./test-data/files/ "%s" brunnhilde_test' % (self.dest_tmpdir), 
            shell=True)
        # siegfried csv and sqlite db
        self.assertTrue(is_non_zero_file(os.path.join(self.dest_tmpdir, 'brunnhilde_test', 
            'siegfried.csv')))
        self.assertTrue(is_non_zero_file(os.path.join(self.dest_tmpdir, 'brunnhilde_test', 
            'siegfried.sqlite')))
        # html report
        self.assertTrue(is_non_zero_file(os.path.join(self.dest_tmpdir, 'brunnhilde_test', 
            'brunnhilde_test.html')))
        # csv reports
        self.assertTrue(is_non_zero_file(os.path.join(self.dest_tmpdir, 'brunnhilde_test', 
            'csv_reports', 'duplicates.csv')))
        self.assertTrue(is_non_zero_file(os.path.join(self.dest_tmpdir, 'brunnhilde_test', 
            'csv_reports', 'errors.csv')))
        self.assertTrue(is_non_zero_file(os.path.join(self.dest_tmpdir, 'brunnhilde_test', 
            'csv_reports', 'formats.csv')))
        self.assertTrue(is_non_zero_file(os.path.join(self.dest_tmpdir, 'brunnhilde_test', 
            'csv_reports', 'formatVersions.csv')))
        self.assertTrue(is_non_zero_file(os.path.join(self.dest_tmpdir, 'brunnhilde_test', 
            'csv_reports', 'mimetypes.csv')))
        self.assertTrue(is_non_zero_file(os.path.join(self.dest_tmpdir, 'brunnhilde_test', 
            'csv_reports', 'unidentified.csv')))
        self.assertTrue(is_non_zero_file(os.path.join(self.dest_tmpdir, 'brunnhilde_test', 
            'csv_reports', 'warnings.csv')))
        self.assertTrue(is_non_zero_file(os.path.join(self.dest_tmpdir, 'brunnhilde_test', 
            'csv_reports', 'years.csv')))
        # tree.txt
        if not sys.platform.startswith('win'):
            self.assertTrue(os.path.isfile(os.path.join(self.dest_tmpdir, 'brunnhilde_test', 
                'tree.txt')))
        # virus check log
        self.assertTrue(os.path.isfile(os.path.join(self.dest_tmpdir, 'brunnhilde_test', 
            'logs', 'viruscheck-log.txt')))

    def test_integration_outputs_created_diskimage(self):
        subprocess.call('python ./brunnhilde.py -d ./test-data/diskimages/sample-floppy-fat.dd "%s" brunnhilde_test' % (self.dest_tmpdir), 
            shell=True)
        # siegfried csv and sqlite db
        self.assertTrue(is_non_zero_file(os.path.join(self.dest_tmpdir, 'brunnhilde_test', 
            'siegfried.csv')))
        self.assertTrue(is_non_zero_file(os.path.join(self.dest_tmpdir, 'brunnhilde_test', 
            'siegfried.sqlite')))
        # html report
        self.assertTrue(is_non_zero_file(os.path.join(self.dest_tmpdir, 'brunnhilde_test', 
            'brunnhilde_test.html')))
        # csv reports
        self.assertTrue(is_non_zero_file(os.path.join(self.dest_tmpdir, 'brunnhilde_test', 
            'csv_reports', 'duplicates.csv')))
        self.assertTrue(is_non_zero_file(os.path.join(self.dest_tmpdir, 'brunnhilde_test', 
            'csv_reports', 'errors.csv')))
        self.assertTrue(is_non_zero_file(os.path.join(self.dest_tmpdir, 'brunnhilde_test', 
            'csv_reports', 'formats.csv')))
        self.assertTrue(is_non_zero_file(os.path.join(self.dest_tmpdir, 'brunnhilde_test', 
            'csv_reports', 'formatVersions.csv')))
        self.assertTrue(is_non_zero_file(os.path.join(self.dest_tmpdir, 'brunnhilde_test', 
            'csv_reports', 'mimetypes.csv')))
        self.assertTrue(is_non_zero_file(os.path.join(self.dest_tmpdir, 'brunnhilde_test', 
            'csv_reports', 'unidentified.csv')))
        self.assertTrue(is_non_zero_file(os.path.join(self.dest_tmpdir, 'brunnhilde_test', 
            'csv_reports', 'warnings.csv')))
        self.assertTrue(is_non_zero_file(os.path.join(self.dest_tmpdir, 'brunnhilde_test', 
            'csv_reports', 'years.csv')))
        # tree.txt
        if not sys.platform.startswith('win'):
            self.assertTrue(os.path.isfile(os.path.join(self.dest_tmpdir, 'brunnhilde_test', 
                'tree.txt')))
        # dfxml
        self.assertTrue(is_non_zero_file(os.path.join(self.dest_tmpdir, 'brunnhilde_test', 
            'dfxml.xml')))
        # carved_files
        self.assertTrue(is_non_zero_file(os.path.join(self.dest_tempdir, 'brunnhilde_test', 
            'carved_files', 'file1.txt.txt')))
        self.assertTrue(is_non_zero_file(os.path.join(self.dest_tempdir, 'brunnhilde_test', 
            'carved_files', 'Tulips.jpg')))
    
    def test_integration_temp_files_deleted(self):
        subprocess.call('python ./brunnhilde.py ./test-data/files/ "%s" brunnhilde_test' % (self.dest_tmpdir), 
            shell=True)
        # temp.html
        self.assertFalse(os.path.isfile(os.path.join(self.dest_tmpdir, 'brunnhilde_test', 
            'temp.html')))
        # uniqueyears.csv
        self.assertFalse(os.path.isfile(os.path.join(self.dest_tmpdir, 'brunnhilde_test', 
            'csv_reports', 'uniqueyears.csv')))


if __name__ == '__main__':
    unittest.main()
