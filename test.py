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


class SelfCleaningTestCase(unittest.TestCase):
    """TestCase subclass which cleans up self.tmpdir after each test"""

    def setUp(self):
        super(SelfCleaningTestCase, self).setUp()

        # tempdir for sample data
        self.src_tmpdir = tempfile.mkdtemp()
        if os.path.isdir(self.src_tmpdir):
            shutil.rmtree(self.src_tmpdir)
        shutil.copytree('test-data', self.src_tmpdir)

        # tempdir for brunnhilde outputs
        self.dest_tmpdir = tempfile.mkdtemp()
        if not os.path.isdir(self.dest_tmpdir):
            os.mkdirs(self.dest_tmpdir)

    def tearDown(self):
        for temp_dir in self.src_tmpdir, self.dest_tmpdir:
            if os.path.isdir(temp_dir):
                shutil.rmtree(temp_dir)


        super(SelfCleaningTestCase, self).tearDown()


class TestBrunnhildeIntegration(SelfCleaningTestCase):

    def test_integration_outputs_created(self):
        subprocess.call("python ./brunnhilde.py %s %s brunnhilde_test" % (self.src_tmpdir, 
            self.dest_tmpdir), shell=True)
        # siegfried csv and sqlite db
        self.assertTrue(os.path.isfile(os.path.join(self.dest_tmpdir, 'brunnhilde_test', 
            'siegfried.csv')))
        self.assertTrue(os.path.isfile(os.path.join(self.dest_tmpdir, 'brunnhilde_test', 
            'siegfried.sqlite')))
        # html report
        self.assertTrue(os.path.isfile(os.path.join(self.dest_tmpdir, 'brunnhilde_test', 
            'brunnhilde_test.html')))
        # csv reports
        self.assertTrue(os.path.isfile(os.path.join(self.dest_tmpdir, 'brunnhilde_test', 
            'csv_reports', 'duplicates.csv')))
        self.assertTrue(os.path.isfile(os.path.join(self.dest_tmpdir, 'brunnhilde_test', 
            'csv_reports', 'errors.csv')))
        self.assertTrue(os.path.isfile(os.path.join(self.dest_tmpdir, 'brunnhilde_test', 
            'csv_reports', 'formats.csv')))
        self.assertTrue(os.path.isfile(os.path.join(self.dest_tmpdir, 'brunnhilde_test', 
            'csv_reports', 'formatVersions.csv')))
        self.assertTrue(os.path.isfile(os.path.join(self.dest_tmpdir, 'brunnhilde_test', 
            'csv_reports', 'mimetypes.csv')))
        self.assertTrue(os.path.isfile(os.path.join(self.dest_tmpdir, 'brunnhilde_test', 
            'csv_reports', 'unidentified.csv')))
        self.assertTrue(os.path.isfile(os.path.join(self.dest_tmpdir, 'brunnhilde_test', 
            'csv_reports', 'warnings.csv')))
        self.assertTrue(os.path.isfile(os.path.join(self.dest_tmpdir, 'brunnhilde_test', 
            'csv_reports', 'years.csv')))
        # tree.txt
        self.assertTrue(os.path.isfile(os.path.join(self.dest_tmpdir, 'brunnhilde_test', 
            'tree.txt')))
        # virus check log
        self.assertTrue(os.path.isfile(os.path.join(self.dest_tmpdir, 'brunnhilde_test', 
            'logs', 'viruscheck-log.txt')))
    
    def test_integration_temp_files_deleted(self):
        subprocess.call("python ./brunnhilde.py %s %s brunnhilde_test" % (self.src_tmpdir, 
            self.dest_tmpdir), shell=True)
        # temp.html
        self.assertFalse(os.path.isfile(os.path.join(self.dest_tmpdir, 'brunnhilde_test', 
            'temp.html')))
        # uniqueyears.csv
        self.assertFalse(os.path.isfile(os.path.join(self.dest_tmpdir, 'brunnhilde_test', 
            'csv_reports', 'uniqueyears.csv')))


if __name__ == '__main__':
    unittest.main()