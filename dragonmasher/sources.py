"""Chinese data source classes and methods."""

import contextlib
import logging
import os
import pkgutil
import shutil
import sys
import tempfile

is_python3 = sys.version_info[0] > 2

if is_python3:
    from urllib.request import urlopen
else:
    from urllib2 import urlopen
    from codecs import open

from fcache.cache import FileCache
from ticktock import TimeoutShelf

from dragonmasher.unpack import unpack_archive

logger = logging.getLogger(__name__)

DEFAULT_ENCODING = 'utf-8'
DEFAULT_TIMEOUT = 12096000


class BaseSource(object):
    """Base class for Chinese data sources."""

    def __init__(self, encoding=DEFAULT_ENCODING):
        self.files = self.files if hasattr(self, 'files') else None
        self.whitelist = self.whitelist if hasattr(self, 'whitelist') else None
        self.data = self.data if hasattr(self, 'data') else {}
        self.encoding = encoding
        self.key_prefix = self.name + '-'

    def read(self):
        """Reads and processes the data, then stores data in self.data."""
        raise NotImplemented


class BaseLocalSource(BaseSource):
    """Base class for local Chinese data sources."""

    def read(self):
        """Reads and processes the data, then stores data in self.data."""
        for name in self.files:
            logger.debug("Opening file for reading: '%s'." % name)
            contents = pkgutil.get_data('dragonmasher',
                                        name).decode(self.encoding)
            logger.debug("Processing file: '%s'." % name)
            self._read_file(name, contents)
        return self

    def _read_file(self, name, contents):
        """Processes and stores the file contents into self.data."""
        raise NotImplemented


class BaseRemoteSource(BaseSource):
    """Base class for remote Chinese data sources."""

    def __init__(self, cache_data=True, cache_name='dragonmasher',
                 timeout=DEFAULT_TIMEOUT, encoding=DEFAULT_ENCODING):
        """Opens and reads cache data."""
        self.cache_data = cache_data
        if self.cache_data:
            self._init_cache(cache_name, timeout)
        super(BaseRemoteSource, self).__init__(encoding=encoding)

    def _init_cache(self, cache_name, timeout):
        """Opens a cache for the processed source data."""
        cache = FileCache(cache_name, serialize=False)
        self.cache = TimeoutShelf(cache, writeback=True, timeout=timeout)
        self.data = self.cache.setdefault(self.name, {})

    def _reset_cache(self):
        """Deletes the cached data."""
        del self.cache[self.name]
        self.cache.sync()
        self.data = self.cache.setdefault(self.name, {})

    @property
    def has_data(self):
        """Checks if the source data is already processed or not."""
        return bool(self.data)

    @property
    def has_files(self):
        """Checks if the source files are downloaded already or not."""
        return bool(self.files)

    def download(self, force_download=False, filename=None):
        """Download the file and save it to a temporary directory."""
        if self.has_data and not force_download:
            logger.info("Source has cached data. Cancelling download.")
            return self
        elif self.has_files and not force_download:
            logger.info("Source has unprocessed files. Cancelling download.")
            return self
        if force_download:
            self._reset_cache()
        url = self.download_url
        logger.debug("Creating temporary directory for downloaded file.")
        self.temp_dir = tempfile.mkdtemp()
        rel_fname = os.path.basename(url) if filename is None else filename
        abs_fname = os.path.join(self.temp_dir, rel_fname)
        self._download(url, abs_fname)
        self.files = (abs_fname,)
        return self

    def _download(self, url, filename):
        logger.debug("Opening the URL: '%s'." % url)
        with contextlib.closing(urlopen(self.download_url)) as page:
            with open(filename, 'wb') as f:
                logger.debug("Saving file: '%s'." % filename)
                f.write(page.read())

    def read(self):
        """Reads and processes the data, then stores data in self.data."""
        if self.has_data:
            return self
        elif not self.has_files:
            raise OSError("Download was not successful, no files to read.")
        for fname in self.files:
            rel_fname = os.path.basename(fname)
            if (self.whitelist is not None and
                    rel_fname not in self.whitelist):
                logger.debug("Ignoring file: '%s'." % rel_fname)
                continue
            logger.debug("Opening file for reading: '%s'." % fname)
            with open(fname, 'r', encoding=self.encoding) as f:
                contents = f.read()
                logger.debug("Processing file: '%s'." % fname)
                self._read_file(fname, contents)
        if self.cache_data:
            logger.debug("Writing processed data to cache.")
            self.cache.sync()
        self._cleanup()
        return self

    def _cleanup(self):
        logger.debug("Cleaning up temporary files.")
        shutil.rmtree(self.temp_dir)
        del self.temp_dir
        self.files = None


class BaseRemoteArchiveSource(BaseRemoteSource):
    """Base class for remote archive Chinese data sources."""

    def download(self, force_download=False, filename=None):
        """Download the file and save it to a temporary directory."""
        if self.has_data and not force_download:
            return self
        super(BaseRemoteArchiveSource, self).download(force_download, filename)
        self._extract()
        return self

    def _extract(self):
        """Extract the contents of the archive file.

        ReadError is raised when an archive cannot be read.

        """
        if not self.has_files:
            raise OSError("Download was not successful, no files to extract.")
        logger.debug("Unpacking archive file: '%s'." % self.files[0])
        unpack_archive(self.files[0], self.temp_dir)
        os.remove(self.files[0])
        _files = os.listdir(self.temp_dir)
        self.files = tuple([os.path.join(self.temp_dir, f) for f in _files])


class CSVMixin(object):
    """A mixin class that reads CSV data directly into the source class."""

    def __init__(self, index_column=0, **kwargs):
        super(CSVMixin, self).__init__(**kwargs)
        self.index_column = index_column

    def _read_file(self, name, contents):
        """Processes and stores the file contents into self.data."""
        headers = list(self.headers)
        del headers[self.index_column]
        for line in contents.splitlines():
            if line[0] == '#':
                continue  # Skip all comments.
            row = line.split(',')
            key = row.pop(self.index_column)
            value = dict(zip([self.key_prefix + h for h in headers], row))
            self.data.setdefault(key, {})
            self.data[key].update(value)


class HSK(CSVMixin, BaseLocalSource):
    """A class for reading local HSK data."""

    name = 'HSK'
    files = ('data/hsk.csv',)
    headers = ('word', 'level')


class TOCFL(CSVMixin, BaseLocalSource):
    """A class for reading local TOCFL data."""

    name = 'TOCFL'
    files = ('data/tocfl.csv',)
    headers = ('word', 'level', 'pos', 'category')


class XianDaiChangYongZi(CSVMixin, BaseLocalSource):
    """A class for reading local XianDaiChangYongZi data."""

    name = 'XDCYZ'
    files = ('data/xdcyz.csv',)
    headers = ('character', 'level', 'strokes')


class SUBTLEX(BaseRemoteArchiveSource):
    """A class for downloading and reading remote SUBTLEX data."""

    download_url = ('http://expsy.ugent.be/subtlex-ch/'
                    'SUBTLEX_CH_131210_CE.utf8.zip')
    name = 'SUBTLEX'
    whitelist = (
        'SUBTLEX_CH_131210_CE.utf8',
    )
    headers = (
        'word', 'length', 'pinyin', 'pinyin.input', 'wcount', 'w.million',
        'log10w', 'w-cd', 'w-cd%', 'log10cd', 'dominant.pos',
        'dominant.pos.freq', 'all.pos', 'all.pos.freq', 'english'
    )

    def _read_file(self, filename, contents):
        """Processes and stores the file contents into self.data."""
        lines = contents.splitlines()
        for line in lines:
            if line.startswith('Word'):
                continue  # Skip the header.
            row = line.split('\t')
            key = row.pop(0)
            row = row[:-1]
            headers = self.headers[1:-1]
            value = dict(zip([self.key_prefix + h for h in headers], row))
            self.data.setdefault(key, {})
            self.data[key].update(value)
