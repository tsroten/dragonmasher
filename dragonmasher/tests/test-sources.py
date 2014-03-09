# -*- coding: utf-8 -*-
"""Unit tests for the dragonmasher.sources module."""

from __future__ import unicode_literals
import os
import unittest

from ticktock import TimeoutShelf

from dragonmasher import sources


class PackageResourceSourceTestCase(unittest.TestCase):
    """Tests for the package resource source classes.

    This tests the BasePackageResourceSource class and the CSVMixin class.

    """

    def test_hsk_data(self):
        """Tests that the HSK data loads correctly."""
        hsk = sources.HSK()
        hsk.read()
        self.assertEqual(4995, len(hsk.data))
        self.assertEqual('2', hsk.data['便宜']['HSK-level'])

    def test_tocfl_data(self):
        """Tests that the TOCFL data loads correctly."""
        tocfl = sources.TOCFL()
        tocfl.read()
        self.assertEqual(7415, len(tocfl.data))
        self.assertEqual('1', tocfl.data['便宜']['TOCFL-level'])
        self.assertEqual('VS/N', tocfl.data['便宜']['TOCFL-pos'])
        self.assertEqual('購物', tocfl.data['便宜']['TOCFL-category'])

    def test_xdcyz_data(self):
        """Tests that the XDCYZ data loads correctly."""
        xdcyz = sources.XianDaiChangYongZi()
        xdcyz.read()
        self.assertEqual(3500, len(xdcyz.data))
        self.assertEqual('1', xdcyz.data['爱']['XDCYZ-level'])
        self.assertEqual('10', xdcyz.data['爱']['XDCYZ-strokes'])


class BaseRemoteSourceTestCase(unittest.TestCase):
    """Tests for the BaseRemoteSource class."""

    def __init__(self, *args, **kwargs):
        """Finds data file."""
        data_dir = os.path.join(os.path.dirname(__file__), 'data')
        self.data_file = os.path.join(data_dir, 'remote_source_test.txt')
        super(BaseRemoteSourceTestCase, self).__init__(*args, **kwargs)

    def setUp(self):
        """Creates a RemoteSource instance."""
        data_file = self.data_file

        class RemoteSource(sources.BaseRemoteSource):
            name = 'RemoteSource'
            download_url = 'http://foo.com/remote_source_test.txt'

            def _download(self, url, filename):
                with open(data_file) as f:
                    data = f.read()
                with open(filename, 'w') as f:
                    f.write(data)

            def process_file(self, fname, contents):
                return {'test': contents}

        self.source = RemoteSource(cache_data=False)

    def tearDown(self):
        """Deletes cache files and temporary files."""
        if self.source.cache_data:
            self.source.cache.dict.delete()
        if self.source.temp_dir is not None:
            self.source._cleanup()

    def test_remote_source_init(self):
        """Tests that BaseRemoteSource.__init__ works correctly."""
        self.assertTrue(isinstance(self.source.data, dict))
        self.assertFalse(self.source.cache_data)
        self.assertFalse(hasattr(self.source, 'cache'))
        self.source.cache_data = True
        self.source._init_cache('dragonmasher-tests', 10)
        self.assertTrue(isinstance(self.source.data, dict))
        self.assertTrue(self.source.cache_data)
        self.assertTrue(isinstance(self.source.cache, TimeoutShelf))

    def test_remote_source_download(self):
        """Tests that BaseRemoteSource.download works correctly."""
        self.source.download()
        self.assertTrue(hasattr(self.source, 'temp_dir'))
        self.assertEqual(1, len(self.source.files))
        self.assertTrue(os.path.exists(self.source.files[0]))

    def test_remote_source_read_(self):
        """Tests that BaseRemoteSource.read works correctly."""
        self.assertRaises(OSError, self.source.read)
        self.source.download()
        self.source.read()
        self.assertEqual(None, self.source.temp_dir)
        self.assertEqual(None, self.source.files)
        self.assertEqual('Hello world!\n', self.source.data['test'])

    def test_remote_source_cache(self):
        """Tests that BaseRemoteSource caching features work correctly."""
        self.source.cache_data = True
        self.source._init_cache('dragonmasher-tests', 10)
        self.source.download()
        files = self.source.files
        temp_dir = self.source.temp_dir
        self.source.download()
        self.assertEqual(files, self.source.files)
        self.assertEqual(temp_dir, self.source.temp_dir)
        self.source.read()
        self.assertEqual('Hello world!\n', self.source.data['test'])
        del self.source
        self.setUp()
        self.source.cache_data = True
        self.source._init_cache('dragonmasher-tests', 10)
        self.source.download()
        self.assertEqual(None, self.source.files)
        self.assertEqual('Hello world!\n', self.source.data['test'])


class BaseRemoteArchiveSourceTestCase(unittest.TestCase):
    """Tests for the BaseRemoteArchiveSource class."""

    def __init__(self, *args, **kwargs):
        """Finds data file."""
        data_dir = os.path.join(os.path.dirname(__file__), 'data')
        self.data_file = os.path.join(data_dir, 'remote_archive_test.zip')
        self.filename = 'remote_source_test.txt'
        super(BaseRemoteArchiveSourceTestCase, self).__init__(*args, **kwargs)

    def setUp(self):
        """Creates a RemoteArchiveSource instance."""
        data_file = self.data_file

        class RemoteArchiveSource(sources.BaseRemoteArchiveSource):
            name = 'RemoteArchiveSource'
            download_url = 'http://foo.com/remote_archive_test.zip'

            def _download(self, url, filename):
                with open(data_file, 'rb') as f:
                    data = f.read()
                with open(filename, 'wb') as f:
                    f.write(data)

        self.source = RemoteArchiveSource(cache_data=False)

    def tearDown(self):
        """Deletes cache files and temporary files."""
        if self.source.cache_data:
            self.source.cache.dict.delete()
        if hasattr(self.source, 'temp_dir'):
            self.source._cleanup()

    def test_remote_archive_source_download(self):
        """Tests that BaseRemoteArchiveSource.download works correctly."""
        self.source.download()
        self.assertTrue(hasattr(self.source, 'temp_dir'))
        self.assertEqual(1, len(self.source.files))
        self.assertTrue(os.path.exists(self.source.files[0]))
        self.assertTrue(self.filename in self.source.files[0])


class SUBTLEXTestCase(unittest.TestCase):
    """Tests for the SUBTLEX data source class."""

    def __init__(self, *args, **kwargs):
        """Sets the data_dir attribute."""
        self.data_dir = os.path.join(os.path.dirname(__file__), 'data')
        self.data_file = os.path.join(self.data_dir, 'subtlex_words_test.txt')
        super(SUBTLEXTestCase, self).__init__(*args, **kwargs)

    def setUp(self):
        """Reads data file."""
        self.subtlex = sources.SUBTLEX(cache_data=False)
        self.subtlex.files = (self.data_file,)
        self.subtlex.whitelist = ('subtlex_words_test.txt',)

        def _cleanup():
            pass

        self.subtlex._cleanup = _cleanup

    def test_subtlex_words_read(self):
        """Tests that SUBTLEXWords processes the data correctly."""
        self.subtlex.read()
        self.assertEqual(4, len(self.subtlex.data))
        self.assertEqual('1', self.subtlex.data['的']['SUBTLEX-length'])


class CSVMixinTestCase(unittest.TestCase):
    """Unit tests for the CSVMixin class."""

    class CSVMixinTest(sources.CSVMixin):
        key_prefix = 'CSV-'

    def test_update(self):
        """Tests that CSVMixin.update works correctly."""
        csvmixin = self.CSVMixinTest()

        d1 = {'1': {'1': '1'}}
        d2 = {'2': {'2': '2'}}
        d12 = {'1': {'1': '1'}, '2': {'2': '2'}}
        d3 = {'3': {'3': '4'}}
        d4 = {'3': {'3': '5'}}
        d34 = {'3': {'3': ['4', '5']}}

        csvmixin.update(d1, d2)
        self.assertEqual(d12, d1)
        csvmixin.update(d3, d4)
        self.assertEqual(d34, d3)

        d22 = d2.copy()
        csvmixin.update(d2, d22)
        self.assertEqual(d22, d2)

    def test_split_line(self):
        """Tests that CSVMixin.split_line works correctly."""
        csvmixin = self.CSVMixinTest()
        line = 'Hello,world'
        sline = ['Hello', 'world']
        self.assertEqual(sline, csvmixin.split_line(line, ','))

    def test_process_row(self):
        """Tests that CSVMixin.process_row works correctly."""
        csvmixin = self.CSVMixinTest()
        row = ['Hello', 'world']
        prow = row[:]
        self.assertEqual(prow, csvmixin.process_row(row))
