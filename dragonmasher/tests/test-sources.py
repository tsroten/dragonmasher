# -*- coding: utf-8 -*-
"""Unit tests for the dragonmasher.sources module."""

from __future__ import unicode_literals
import os
import shutil
import sys
import types
import unittest

from ticktock import TimeoutShelf

from dragonmasher import sources

is_python3 = sys.version_info[0] > 2

if not is_python3:
    str = unicode


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
            shutil.rmtree(os.path.dirname(self.source.cache.dict.cache_dir))
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
            shutil.rmtree(os.path.dirname(self.source.cache.dict.cache_dir))
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
        self.assertEqual('1', self.subtlex.data['的']['SUBTLEX-number'])


class CSVMixinTestCase(unittest.TestCase):
    """Unit tests for the CSVMixin class."""

    def setUp(self):
        self.csvmixin = sources.CSVMixin()

    def test_process_row(self):
        """Tests that CSVMixin.process_row works correctly."""
        row = ['Hello', 'world']
        prow = row[:]
        self.assertEqual(prow, self.csvmixin.process_row(row, ('#',)))

        row = ['#Comment', 'here']
        self.assertEqual(None, self.csvmixin.process_row(row, ('#',)))

    def test_get_rows(self):
        """Tests that CSVMixin.get_rows works correctly."""
        lines = ['A,B,C', 'D,E,F']
        erows = [['A', 'B', 'C'], ['D', 'E', 'F']]
        rows = self.csvmixin.get_rows(lines)
        self.assertEqual(erows, list(rows))

    def test_process_file(self):
        """Tests that CSVMixin.process_file works correctly."""
        self.csvmixin.headers = ('Letter', 'Number', 'Foo')
        self.csvmixin.key_prefix = 'CSV-'
        contents = 'a,1,bar\nb,2,bar\nc,3,bar\nd,4,bar\n'
        edata = {'a': {'CSV-Number': '1'}, 'b': {'CSV-Number': '2'},
                 'c': {'CSV-Number': '3'}, 'd': {'CSV-Number': '4'}}
        data = self.csvmixin.process_file('foo.txt', contents, exclude=(2,))
        self.assertEqual(edata, data)


class CEDICTTestCase(unittest.TestCase):
    """Tests for the CEDICT data source class."""

    def __init__(self, *args, **kwargs):
        """Sets the data_dir attribute."""
        self.data_dir = os.path.join(os.path.dirname(__file__), 'data')
        self.data_file = os.path.join(self.data_dir, 'cedict_test.txt')
        super(CEDICTTestCase, self).__init__(*args, **kwargs)

    def setUp(self):
        """Reads data file."""
        self.cedict = sources.CEDICT(cache_data=False)
        self.cedict.files = (self.data_file,)
        self.cedict.whitelist = ('cedict_test.txt',)

        def _cleanup():
            pass

        self.cedict._cleanup = _cleanup

    def test_get_rows(self):
        """Tests that CEDICT.get_rows works correctly."""
        contents = ('钃 钃 [shu3] /metal/\n'
                    '長 长 [chang2] /length/long/forever/always/constantly/\n')
        rows = self.cedict.get_rows(contents.splitlines())
        self.assertTrue(isinstance(rows, types.GeneratorType))
        rows_list = list(rows)
        self.assertEqual(2, len(rows_list))
        self.assertEqual(['钃', '钃', 'shu3', 'metal'], rows_list[0])
        self.assertEqual(['長', '长', 'chang2',
                          'length/long/forever/always/constantly'],
                         rows_list[1])

    def test_cedict_process_row(self):
        """Tests that CEDICT.process_row works correctly."""
        row = ['長', '长', 'chang2', 'length/long/forever/always/constantly']
        prow = self.cedict.process_row(row, ('#',))
        self.assertEqual('cháng', prow[2])
        self.assertTrue(isinstance(prow[3], list))

        row = ['#foo', 'bar', 'bar', 'bar']
        prow = self.cedict.process_row(row, ('#',))
        self.assertEqual(None, prow)

    def test_cedict_read(self):
        """Tests that CEDICT processes the data correctly."""
        self.cedict.read()
        self.assertEqual(3, len(self.cedict.data))
        self.assertEqual('shǔ', self.cedict.data['钃']['CEDICT-entry'][0][2])
        self.assertEqual('长', self.cedict.data['長']['CEDICT-entry'][0][1])


class BaseJunDaTestCase(unittest.TestCase):
    """Tests for the BaseJunDa data source class."""

    def __init__(self, *args, **kwargs):
        """Sets the data_dir attribute."""
        self.data_dir = os.path.join(os.path.dirname(__file__), 'data')
        self.data_file = os.path.join(self.data_dir, 'junda_test.txt')
        super(BaseJunDaTestCase, self).__init__(*args, **kwargs)

    def setUp(self):
        """Reads data file."""
        self.junda = sources.BaseJunDa('IM', cache_data=False)
        self.junda.files = (self.data_file,)
        self.junda.whitelist = ('junda_test.txt',)

        def _cleanup():
            pass

        self.junda._cleanup = _cleanup

    def test_init(self):
        """Tests that the BaseJunDa.__init__ function works as expected."""
        download_url = ('http://lingua.mtsu.edu/chinese-computing/statistics'
                        '/char/download.php?Which=IM')
        self.assertEqual(download_url, self.junda.download_url)
        self.assertEqual('JUNDA-IM', self.junda.name)

    def test_read(self):
        """Tests that JunDa's data is read correctly."""
        self.junda.read()
        self.assertEqual(5, len(self.junda.data))
        self.assertEqual('1', self.junda.data['的']['JUNDA-IM-number'])
        self.assertEqual('7.18753757539',
                         self.junda.data['了']['JUNDA-IM-percentile'])
        self.assertFalse('JUNDA-IM-pinyin' in self.junda.data['了'])
        self.assertFalse('JUNDA-IM-definition' in self.junda.data['了'])


class LWCWordsTestCase(unittest.TestCase):
    """Tests for the LWC words data source class."""

    def __init__(self, *args, **kwargs):
        """Sets the data_dir attribute."""
        self.data_dir = os.path.join(os.path.dirname(__file__), 'data')
        self.data_file = os.path.join(self.data_dir, 'lwc_words_test.txt')
        super(self.__class__, self).__init__(*args, **kwargs)

    def setUp(self):
        """Reads data file."""
        self.lwc = sources.LWCWords(cache_data=False)
        self.lwc.files = (self.data_file,)
        self.lwc.whitelist = ('lwc_words_test.txt',)

        def _cleanup():
            pass

        self.lwc._cleanup = _cleanup

    def test_read(self):
        """Tests that LWCWords' data is read correctly."""
        self.lwc.read()
        self.assertEqual(1, len(self.lwc.data))
        self.assertEqual('33', self.lwc.data['揭露']['LWC-word-id'])
        self.assertEqual('318', self.lwc.data['揭露']['LWC-count'])
        self.assertEqual('1', self.lwc.data['揭露']['LWC-number'])
        self.assertFalse('LWC-reverse-of-word' in self.lwc.data['揭露'])


class UnihanTestCase(unittest.TestCase):
    """Tests for the Unihan data source class."""

    def __init__(self, *args, **kwargs):
        """Sets the data_dir attribute."""
        self.data_dir = os.path.join(os.path.dirname(__file__), 'data')
        self.data_files = [os.path.join(self.data_dir, f) for f in
                           ('unihan_variants_test.txt',
                            'unihan_readings_test.txt')]
        super(self.__class__, self).__init__(*args, **kwargs)

    def setUp(self):
        """Reads data file."""
        self.unihan = sources.Unihan(cache_data=False)
        self.unihan.files = self.data_files

        def _cleanup():
            pass

        self.unihan._cleanup = _cleanup

    def test_read(self):
        """Tests that Unihan's data is read correctly."""
        self.unihan.read()
        self.assertEqual(2, len(self.unihan.data))
        self.assertEqual('cí', self.unihan.data['\u34E8']['UNIHAN-kMandarin'])
        self.assertEqual('ci3',
                         self.unihan.data['\u34E8']['UNIHAN-kCantonese'])
        self.assertEqual(
            '\u523E', self.unihan.data['\u34E8']['UNIHAN-kSimplifiedVariant'])
