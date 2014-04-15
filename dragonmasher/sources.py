# -*- coding: utf-8 -*-
"""Chinese data source classes and methods."""

from __future__ import unicode_literals
import contextlib
import logging
import os
import pkgutil
import re
import shutil
import sys
import tempfile

is_python3 = sys.version_info[0] > 2
is_python2 = not is_python3

if is_python3:
    import csv
    from urllib.request import urlopen
else:
    from codecs import open
    from urllib2 import urlopen

    from . import unicodecsv as csv

from dragonmapper import transcriptions
from fcache.cache import FileCache
from ticktock import TimeoutShelf
import zhon.hanzi

from dragonmasher.unpack import unpack_archive
from dragonmasher.utils import hex_to_chr, trim_list, update_dict

logger = logging.getLogger(__name__)

PACKAGE = __name__.rpartition('.')[0]

#: The default timeout value for cached data (in seconds).
DEFAULT_TIMEOUT = 12096000


class BaseSource(object):
    """Base class for Chinese data sources."""

    def __init__(self, encoding='utf-8'):
        """Sets up instance variables.

        :param str encoding: The file encoding to use when opening the source's
            files.

        """
        #: A dictionary containing the processed source data.
        self.data = self.data if hasattr(self, 'data') else {}

        #: The file encoding to use when opening the source's files.
        self.encoding = encoding

        #: A tuple containing the paths to the source's files.
        self.files = self.files if hasattr(self, 'files') else None

        #: A string containing the name/abbreviation for this source.
        self.name = self.name if hasattr(self, 'name') else None

        super(BaseSource, self).__init__()

    @property
    def key_prefix(self):
        """A string that is prefixed to the source's data keys."""
        return self.name + '-'

    def read(self):
        """Reads and processes the source's files.

        The processed data is stored in :attr:`data`.

        For each file to be read and processed, this method calls
        :meth:`read_file` and :meth:`process_file`.

        """
        for filename in self.files:
            contents = self.read_file(filename)
            if contents is not None:
                data = self.process_file(filename, contents)
                update_dict(self.data, data)

    def read_file(self, filename):
        """Reads a source file's contents.

        .. NOTE:: This method is not implemented in this class and should be
            implemented in child classes.

        :param str filename: The filename of the file to be read.
        :return: The file's contents.
        :rtype: :class:`str`

        """
        raise NotImplemented

    def process_file(self, filename, contents):
        """Processes a source file's contents.

        .. NOTE:: This method is not implemented in this class and should be
            implemented in child classes.

        :param str filename: The filename of the file to be processed.
        :param str contents: The contents to be processed.
        :return: The processed data.
        :rtype: :class:`dict`

        """
        raise NotImplemented


class BaseLocalSource(BaseSource):
    """Base class for local Chinese data sources."""

    def read_file(self, filename):
        """Reads a source file's contents.

        :param str filename: The filename of the file to be read.
        :return: The file's contents.
        :rtype: :class:`str`

        """
        logger.debug("Opening file for reading: '%s'." % filename)
        with open(filename, 'r') as f:
            return f.read()


class BasePackageResourceSource(BaseLocalSource):
    """Base class for Chinese data sources that are package resources."""

    def read_file(self, resource):
        """Reads a package resource's contents.

        :param str resource: The relative filename of the resource.
        :return: The resource's contents.
        :rtype: :class:`str`

        """
        logger.debug("Opening package resource for reading: '%s'." % resource)
        return pkgutil.get_data(PACKAGE, resource).decode(self.encoding)


class BaseRemoteSource(BaseSource):
    """Base class for remote Chinese data sources.

    This class is designed to work with plaintext data sources (i.e. source
    files that are not packed in an archive file like ZIP or tar).

    """

    def __init__(self, cache_data=True, cache_name='dragonmasher',
                 timeout=DEFAULT_TIMEOUT, encoding='utf-8'):
        """Sets up caching for remote data sources.

        If *cache_data* is ``True``, the processed source data will be stored
        in a file cache so calls to :meth:`download` and :meth:`read` via
        future instances can be ignored. The cache is associated with the
        *cache_name*. The cached data is retained for *timeout* number of
        seconds (defaults to the module-level constant
        :data:`DEFAULT_TIMEOUT`). If *cache_data* is ``False``, then the
        processed data is only stored in memory -- future instances will
        need to redownload and reprocess the data.

        :param bool cache_data: Whether or not to cache the processed data
            (defaults to ``True``).
        :param str cache_name: The cache's name (defaults to
            ``'dragonmasher'``).
        :param int timeout: How long in seconds until the cached data expires
            (defaults to :data:`DEFAULT_TIMEOUT`).
        :param str encoding: The file encoding to use when opening the source's
            files.

        """
        #: A boolean value indicating whether or not to cache processed data.
        self.cache_data = cache_data

        #: A string indicating the path to this instance's temporary directory.
        self.temp_dir = None

        if self.cache_data:
            self._init_cache('%s.%s' % (cache_name, self.name), timeout)

        super(BaseRemoteSource, self).__init__(encoding=encoding)

    def _init_cache(self, cache_name, timeout):
        """Opens a cache for the processed source data."""
        fcache = FileCache(cache_name, serialize=False)
        self.cache = TimeoutShelf(fcache, writeback=True, timeout=timeout)
        self.data = self.cache.setdefault(self.name, {})

    def _reset_cache(self):
        """Deletes the cached data."""
        del self.data
        del self.cache[self.name]
        self.cache.sync()
        self.data = self.cache.setdefault(self.name, {})

    @property
    def has_data(self):
        """Boolean value indicating if the source data is already processed."""
        return bool(self.data)

    @property
    def has_files(self):
        """Boolean value indicating if the source object has local files.

        This is useful to determine if the source's files have been already
        been downloaded/extracted. Once the files have been processed, they are
        deleted and this value is ``False``.

        """
        return bool(self.files)

    def download(self, force_download=False, filename=None):
        """Downloads the source data and saves it to a temporary directory.

        The temporary directory's path is accessible through
        :attr:`temp_dir`.

        :attr:`files` is set to a tuple containing the absolute filename
        of the file downloaded.

        If *force_download* is ``True``, then downloaded files and cached data
        will be deleted and the source data will be downloaded again. If
        *force_download* is ``False``, then the download will be cancelled if
        the files have already been downloaded or the processed data has been
        cached.

        :param bool force_download: Whether or not to download the source files
            even if the data is cached.
        :param str filename: A filename to use when downloading the source's
            files.

        """
        if self.has_data and not force_download:
            logger.info("Source has cached data. Cancelling download.")
            return
        elif self.has_files and not force_download:
            logger.info("Source has unprocessed files. Cancelling download.")
            return
        if force_download:
            self._reset_cache()
        url = self.download_url
        logger.debug("Creating temporary directory for downloaded file.")
        self.temp_dir = tempfile.mkdtemp()
        rel_fname = os.path.basename(url) if filename is None else filename
        abs_fname = os.path.join(self.temp_dir, rel_fname)
        self._download(url, abs_fname)
        self.files = (abs_fname,)

    def _download(self, url, filename):
        """Opens *url* and saves it to *filename*."""
        logger.debug("Opening the URL: '%s'." % url)
        with contextlib.closing(urlopen(self.download_url)) as page:
            with open(filename, 'wb') as f:
                logger.debug("Saving file: '%s'." % filename)
                f.write(page.read())

    def read(self):
        """Reads and processes the source's files.

        The processed data is stored in :attr:`data`.

        For each file to be read and processed, this method calls
        :meth:`read_file` and :meth:`process_file`.

        """
        if self.has_data:
            return
        elif not self.has_files:
            raise OSError("Download was not successful, no files to read.")

        super(BaseRemoteSource, self).read()

        if self.cache_data:
            logger.debug("Writing processed data to cache.")
            self.cache.sync()

        self._cleanup()

    def read_file(self, filename):
        """Reads a source file's contents.

        :param str filename: The filename of the file to be read.
        :return: The resource's contents (:data:`None` if no contents are to be
            retured, e.g. the file was ignored).
        :rtype: :class:`str` or :data:`None`

        """
        logger.debug("Opening file for reading: '%s'." % filename)
        with open(filename, 'r', encoding=self.encoding) as f:
            return f.read()

    def _cleanup(self):
        """Deletes downloaded files and the temporary directory."""
        logger.debug("Cleaning up temporary files.")
        shutil.rmtree(self.temp_dir)
        self.temp_dir = None
        self.files = None


class BaseRemoteArchiveSource(BaseRemoteSource):
    """Base class for remote archive Chinese data sources."""

    #: A tuple containing names of files that should be processed. If
    #: empty, then all files are processed.
    whitelist = ()

    def download(self, force_download=False, filename=None):
        """Downloads the source data and saves it to a temporary directory.

        The temporary directory's path is accessible through
        :attr:`temp_dir`.

        After downloading the source archive, the contents are then extracted.
        :attr:`files` is set to a tuple containing the absolute filenames
        of the files extracted.

        If *force_download* is ``True``, then downloaded files and cached data
        will be deleted and the source data will be downloaded again. If
        *force_download* is ``False``, then the download will be cancelled if
        the files have already been downloaded or the processed data has been
        cached.

        :param bool force_download: Whether or not to download the source files
            even if the data is cached.
        :param str filename: A filename to use when downloading the source's
            files.

        """
        super(BaseRemoteArchiveSource, self).download(force_download, filename)
        if self.has_data and not force_download:
            return
        self.extract()

    def extract(self):
        """Extracts the contents of the archive file.

        This method is called automatically by :meth:`download`.

        :exc:`dragonmasher.unpack.ReadError` is raised when an archive
        cannot be read.

        """
        if not self.has_files:
            raise OSError("Download was not successful, no files to extract.")
        logger.debug("Unpacking archive file: '%s'." % self.files[0])
        unpack_archive(self.files[0], self.temp_dir)
        os.remove(self.files[0])
        _files = os.listdir(self.temp_dir)
        self.files = tuple([os.path.join(self.temp_dir, f) for f in _files])

    def read_file(self, filename):
        """Reads a source file's contents.

        :param str filename: The filename of the file to be read.
        :return: The resource's contents (:data:`None` if no contents are to be
            retured, e.g. the file was ignored).
        :rtype: :class:`str` or :data:`None`

        """
        basename = os.path.basename(filename)
        if len(self.whitelist) > 0 and basename not in self.whitelist:
            logger.debug("Ignoring file: '%s'." % filename)
            return None
        logger.debug("Opening file for reading: '%s'." % filename)
        with open(filename, 'r', encoding=self.encoding) as f:
            return f.read()


class CSVMixin(object):
    """A mixin that processes simple CSV data.

    This mixin implements the required :meth:`process_file` method for Chinese
    data source classes.

    :data:`headers` should be defined by child classes and is used
    to create dictionary keys (each header is prepended with
    :data:`BaseSource.key_prefix`). The values are read directly from each
    column of the CSV file.

    :data:`index_column` defaults to ``0``, but should be overridden by child
    classes if a different index column value is needed.

    :meth:`get_rows` and :meth:`process_row` can be overridden to provide
    further customization.

    See :class:`HSK`, :class:`TOCFL`, :class:`XianDaiChangYongZi`, or
    :class:`SUBTLEX` for an example of how to use this mixin.

    """

    #: A tuple containing the CSV file's header.
    headers = ()

    #: The column number to use as a dictionary key when processing the data
    #: (counting from zero).
    index_column = 0

    def process_file(self, filename, contents, delimiter=',', comments=('#',),
                     exclude=()):
        """Processes a CSV file's contents.

        :param str filename: The filename of the file to be processed.
        :param str contents: The contents to be processed.
        :param str delimiter: The field delimiter (defaults to ``','``).
        :param tuple comments: A sequence of one-character strings that are
            used to designate a line as a comment (defaults to ``('#',)``.
        :param tuple exclude: A sequence of column numbers to exclude from the
            data (counting from zero).
        :return: The processed data.
        :rtype: :class:`dict`

        """
        logger.debug("Processing file: '%s'." % filename)
        excluded_columns = exclude + (self.index_column,)
        data = {}
        headers = trim_list(self.headers, excluded_columns)
        if is_python2:
            contents = contents.encode('utf-8')
        rows = self.get_rows(contents.splitlines(), delimiter=delimiter)
        for row in rows:
            prow = self.process_row(row, comments)
            if prow is None:
                logger.debug("Skipping row: '%s'" % row)
                continue
            key = row[self.index_column]
            trow = trim_list(row, excluded_columns)
            value = dict(zip([self.key_prefix + h for h in headers], trow))
            update_dict(data, {key: value})
        return data

    def get_rows(self, csvfile, delimiter=','):
        if is_python2 and not isinstance(delimiter, str):
            delimiter = delimiter.encode('utf-8')
        return csv.reader(csvfile, delimiter=delimiter)

    def process_row(self, row, comments):
        """Processes the fields in *row*."""
        if row[0][0] in comments:
            return None
        return row


class HSK(CSVMixin, BasePackageResourceSource):
    """A class for reading local HSK data.

    See parent classes :class:`CSVMixin` and :class:`BasePackageResourceSource`
    for more information.

    """

    #: A tuple containing this source's package resource name.
    files = ('data/hsk.csv',)

    #: A tuple containing the CSV file's header.
    headers = ('word', 'level')

    #: A unique name/abbreviation for this source.
    name = 'HSK'

    def __init__(self):
        super(HSK, self).__init__(encoding='utf-8')

    def read(self):
        """Reads and processes the HSK data file.

        The processed data is stored in :attr:`HSK.data`.

        """
        super(HSK, self).read()


class TOCFL(CSVMixin, BasePackageResourceSource):
    """A class for reading local TOCFL data.

    See parent classes :class:`CSVMixin` and :class:`BasePackageResourceSource`
    for more information.

    """

    #: A tuple containing this source's filenames.
    files = ('data/tocfl.csv',)

    #: A tuple containing the CSV file's header.
    headers = ('word', 'level', 'pos', 'category')

    #: A unique name/abbreviation for this source.
    name = 'TOCFL'

    def __init__(self):
        super(TOCFL, self).__init__(encoding='utf-8')

    def read(self):
        """Reads and processes the TOCFL data file.

        The processed data is stored in :attr:`TOCFL.data`.

        """
        super(TOCFL, self).read()


class XianDaiChangYongZi(CSVMixin, BasePackageResourceSource):
    """A class for reading local XianDaiChangYongZi data.

    See parent classes :class:`CSVMixin` and :class:`BasePackageResourceSource`
    for more information.

    """

    #: A tuple containing this source's filenames.
    files = ('data/xdcyz.csv',)

    #: A tuple containing the CSV file's header.
    headers = ('character', 'level', 'strokes')

    #: A unique name/abbreviation for this source.
    name = 'XDCYZ'

    def __init__(self):
        super(XianDaiChangYongZi, self).__init__(encoding='utf-8')

    def read(self):
        """Reads and processes the XianDaiChangYongZi data file.

        The processed data is stored in :attr:`XianDaiChangYongZi.data`.

        """
        super(XianDaiChangYongZi, self).read()


class SUBTLEX(CSVMixin, BaseRemoteArchiveSource):
    """A class for downloading and reading remote SUBTLEX-CH data.

    If *cache_data* is ``True``, the processed source data will be stored
    in a file cache so calls to :meth:`download` and :meth:`read` via
    future instances can be ignored. The cache is associated with the
    *cache_name*. The cached data is retained for *timeout* number of
    seconds (defaults to the module-level constant
    :data:`DEFAULT_TIMEOUT`). If *cache_data* is ``False``, then the
    processed data is only stored in memory -- future instances will
    need to redownload and reprocess the data.

    See parent classes :class:`BaseRemoteArchiveSource` and :class:`CSVMixin`
    for more information.

    :param bool cache_data: Whether or not to cache the processed data.
    :param str cache_name: The cache's name.
    :param int timeout: How long in seconds until the cached data expires).

    """

    #: The URL for this data source.
    download_url = ('http://expsy.ugent.be/subtlex-ch/'
                    'SUBTLEX_CH_131210_CE.utf8.zip')

    #: A tuple containing the CSV file's header.
    headers = (
        'word', 'length', 'pinyin', 'pinyin.input', 'wcount', 'w.million',
        'log10w', 'w-cd', 'w-cd%', 'log10cd', 'dominant.pos',
        'dominant.pos.freq', 'all.pos', 'all.pos.freq', 'english'
    )

    #: A unique name/abbreviation for this source.
    name = 'SUBTLEX'

    #: A tuple containing names of files that should be processed. If empty,
    #: then all extracted files are processed.
    whitelist = (
        'SUBTLEX_CH_131210_CE.utf8',
    )

    def __init__(self, cache_data=True, cache_name='dragonmasher',
                 timeout=DEFAULT_TIMEOUT):
        super(SUBTLEX, self).__init__(cache_data=cache_data,
                                      cache_name=cache_name, timeout=timeout,
                                      encoding='utf-8')

    def download(self, force_download=False):
        """Downloads the SUBTLEX-CH data and saves it to a temporary directory.

        The temporary directory's path is accessible through
        :attr:`SUBTLEX.temp_dir`.

        After downloading the source archive, the contents are then extracted.
        :attr:`SUBTLEX.files` is set to a tuple containing the absolute
        filenames of the files extracted.

        If *force_download* is ``True``, then downloaded files and cached data
        will be deleted and the source data will be downloaded again. If
        *force_download* is ``False``, then the download will be cancelled if
        the files have already been downloaded or the processed data has been
        cached.

        :param bool force_download: Whether or not to download the source files
            even if the data is cached.

        """
        super(SUBTLEX, self).download(force_download=force_download)

    def process_file(self, filename, contents):
        """Processes the SUBTLEX-CH word and word frequency data.

        :param str filename: The filename of the file to be processed.
        :param str contents: The contents to be processed.
        :return: The processed data.
        :rtype: :class:`dict`

        """
        delimiter = '\t'
        exclude = (14,)
        comments = ('\ufeff', 'W',)
        logger.debug("Processing file: '%s'." % filename)
        excluded_columns = exclude + (self.index_column,)
        data = {}
        headers = trim_list(self.headers, excluded_columns)
        if is_python2:
            contents = contents.encode('utf-8')
        rows = self.get_rows(contents.splitlines(), delimiter=delimiter)
        prows = []
        for row in rows:
            prow = self.process_row(row, comments)
            if prow is None:
                logger.debug("Skipping row: '%s'" % row)
                continue
            prows.append(prow)
        del contents
        del rows
        prows.sort(key=lambda x: int(x[4]), reverse=True)
        headers.append('number')
        for n, prow in enumerate(prows, start=1):
            key = prow[self.index_column]
            trow = trim_list(prow, excluded_columns)
            trow.append(str(n))
            value = dict(zip([self.key_prefix + h for h in headers], trow))
            update_dict(data, {key: value})
        del prows
        return data

    def read(self):
        """Reads and processes the downloaded SUBTLEX-CH files.

        The processed data is stored in :attr:`SUBTLEX.data`.

        After reading and processing the source files, they are deleted.

        """
        super(SUBTLEX, self).read()

    def process_row(self, row, comments):
        """Processes the fields in *row*."""
        if row[0][0] in comments:
            return None
        return row


class BaseJunDa(CSVMixin, BaseRemoteSource):
    """A base data source class for Jun Da's character frequency lists.

    Child classes must simply pass the desired download option via
    :meth:`__init__`'s *name* argument. The rest of the data source
    functionality is handled by this class.

    See parent classes :class:`BaseRemoteSource` and :class:`CSVMixin` for more
    information.

    """

    _download_url_base = ('http://lingua.mtsu.edu/chinese-computing/statistics'
                          '/char/download.php?Which=')

    #: A tuple containing the CSV file's header.
    headers = ('number', 'character', 'count', 'percentile', 'pinyin',
               'definition')

    #: The column number to use as a dictionary key when processing the data
    #: (counting from zero).
    index_column = 1

    def __init__(self, name, cache_data=True, cache_name='dragonmasher',
                 timeout=DEFAULT_TIMEOUT):
        """Creates the :attr:`download_url` and :attr:`name` attributes.

        :param str name: The download option for this data source (e.g.
            ``'CL'`` or ``'MO'``).
        :param bool cache_data: Whether or not to cache the processed data.
        :param str cache_name: The cache's name.
        :param int timeout: How long in seconds until the cached data expires).

        """
        #: The URL for this data source.
        self.download_url = self._download_url_base + name

        #: A unique name/abbreviation for this source.
        self.name = 'JUNDA-' + name

        super(BaseJunDa, self).__init__(cache_data=cache_data,
                                        cache_name=cache_name, timeout=timeout,
                                        encoding='gb18030')

    def download(self, force_download=False):
        """Downloads Jun Da's data and saves it to a temporary directory.

        The temporary directory's path is accessible through the
        :attr:`temp_dir` attribute.

        After downloading the source archive, the contents are then extracted.
        The attribute :attr:`files` is set to a tuple containing the absolute
        filenames of the files extracted.

        If *force_download* is ``True``, then downloaded files and cached data
        will be deleted and the source data will be downloaded again. If
        *force_download* is ``False``, then the download will be cancelled if
        the files have already been downloaded or the processed data has been
        cached.

        :param bool force_download: Whether or not to download the source files
            even if the data is cached.

        """
        super(BaseJunDa, self).download(force_download=force_download,
                                        filename='CharFreq.txt')

    def process_file(self, filename, contents):
        """Processes the Jun Da character frequency file.

        :param str filename: The filename of the file to be processed.
        :param str contents: The contents to be processed.
        :return: The processed data.
        :rtype: :class:`dict`

        """
        return super(BaseJunDa, self).process_file(filename, contents,
                                                   delimiter='\t',
                                                   comments=('/',),
                                                   exclude=(4, 5))

    def read(self):
        """Reads and processes the downloaded Jun Da character frequency file.

        The processed data is stored in :attr:`data`.

        After reading and processing the source file, it is deleted.

        """
        super(BaseJunDa, self).read()


class JunDaClassicalCharacterList(BaseJunDa):
    """A class for processing Jun Da's Classical Character Frequency data.

    This data comes from Jun Da's character frequency lists and is titled
    `Classical Chinese Character Frequency List`_ (古汉语单字频率列表).

    The English and Pinyin data columns are dropped when processing this data
    source.

    See parent class :class:`BaseJunDa` for more information.

    :param bool cache_data: Whether or not to cache the processed data.
    :param str cache_name: The cache's name.
    :param int timeout: How long in seconds until the cached data expires).

    .. _Classical Chinese Character Frequency List:
        http://lingua.mtsu.edu/chinese-computing/statistics/char/list.php?
        Which=CL

    """

    def __init__(self, cache_data=True, cache_name='dragonmasher',
                 timeout=DEFAULT_TIMEOUT):
        super(self.__class__, self).__init__('CL', cache_data=cache_data,
                                             cache_name=cache_name,
                                             timeout=timeout)


class JunDaModernCharacterList(BaseJunDa):
    """A class for processing Jun Da's Modern Character Frequency data.

    This data comes from Jun Da's character frequency lists and is titled
    `Modern Chinese Character Frequency List`_ (现代汉语单字频率列表).

    The English and Pinyin data columns are dropped when processing this data
    source.

    See parent class :class:`BaseJunDa` for more information.

    :param bool cache_data: Whether or not to cache the processed data.
    :param str cache_name: The cache's name.
    :param int timeout: How long in seconds until the cached data expires).

    .. _Modern Chinese Character Frequency List:
        http://lingua.mtsu.edu/chinese-computing/statistics/char/list.php?
        Which=MO

    """

    def __init__(self, cache_data=True, cache_name='dragonmasher',
                 timeout=DEFAULT_TIMEOUT):
        super(self.__class__, self).__init__('MO', cache_data=cache_data,
                                             cache_name=cache_name,
                                             timeout=timeout)


class JunDaImaginativeCharacterList(BaseJunDa):
    """A class for processing Jun Da's imaginative texts character data.

    This data comes from Jun Da's character frequency lists and is titled
    `Character frequency list of imaginative texts in Modern Chinese`_
    (现代汉语文学类文本单字列表).

    The English and Pinyin data columns are dropped when processing this data
    source.

    See parent class :class:`BaseJunDa` for more information.

    :param bool cache_data: Whether or not to cache the processed data.
    :param str cache_name: The cache's name.
    :param int timeout: How long in seconds until the cached data expires).

    .. _Character frequency list of imaginative texts in Modern Chinese:
        http://lingua.mtsu.edu/chinese-computing/statistics/char/list.php?
        Which=IM

    """

    def __init__(self, cache_data=True, cache_name='dragonmasher',
                 timeout=DEFAULT_TIMEOUT):
        super(self.__class__, self).__init__('IM', cache_data=cache_data,
                                             cache_name=cache_name,
                                             timeout=timeout)


class JunDaInformativeCharacterList(BaseJunDa):
    """A class for processing Jun Da's informative texts character data.

    This data comes from Jun Da's character frequency lists and is titled
    `Character frequency list of informative texts in Modern Chinese`_
    (现代汉语信息类文本单字列表).

    The English and Pinyin data columns are dropped when processing this data
    source.

    See parent class :class:`BaseJunDa` for more information.

    :param bool cache_data: Whether or not to cache the processed data.
    :param str cache_name: The cache's name.
    :param int timeout: How long in seconds until the cached data expires).

    .. _Character frequency list of informative texts in Modern Chinese:
        http://lingua.mtsu.edu/chinese-computing/statistics/char/list.php?
        Which=IN

    """

    def __init__(self, cache_data=True, cache_name='dragonmasher',
                 timeout=DEFAULT_TIMEOUT):
        super(self.__class__, self).__init__('IN', cache_data=cache_data,
                                             cache_name=cache_name,
                                             timeout=timeout)


class JunDaCombinedCharacterList(BaseJunDa):
    """A class for processing Jun Da's Combined Character Frequency data.

    This data comes from Jun Da's character frequency lists and is titled
    `Combined character frequency list of Classical and Modern Chinese`_
    (汉字单字字频总表).

    The English and Pinyin data columns are dropped when processing this data
    source.

    See parent class :class:`BaseJunDa` for more information.

    :param bool cache_data: Whether or not to cache the processed data.
    :param str cache_name: The cache's name.
    :param int timeout: How long in seconds until the cached data expires).

    .. _Combined character frequency list of Classical and Modern Chinese:
        http://lingua.mtsu.edu/chinese-computing/statistics/char/list.php?
        Which=TO

    """

    def __init__(self, cache_data=True, cache_name='dragonmasher',
                 timeout=DEFAULT_TIMEOUT):
        super(self.__class__, self).__init__('TO', cache_data=cache_data,
                                             cache_name=cache_name,
                                             timeout=timeout)


class CEDICT(CSVMixin, BaseRemoteArchiveSource):
    """Fetches and processes the CC-CEDICT dictionary data.

    See parent class :class:`BaseRemoteArchiveSource` for more information.

    :param bool cache_data: Whether or not to cache the processed data.
    :param str cache_name: The cache's name.
    :param int timeout: How long in seconds until the cached data expires).

    """

    #: The URL for this data source.
    download_url = ('http://www.mdbg.net/chindict/export/cedict/'
                    'cedict_1_0_ts_utf-8_mdbg.zip')

    #: A tuple containing the CSV file's header.
    headers = ('traditional', 'simplified', 'pinyin', 'definition')

    #: A unique name/abbreviation for this source.
    name = 'CEDICT'

    #: A tuple containing names of files that should be processed. If empty,
    #: then all extracted files are processed.
    whitelist = (
        'cedict_ts.u8',  # This file is in the ZIP version.
    )

    def __init__(self, cache_data=True, cache_name='dragonmasher',
                 timeout=DEFAULT_TIMEOUT):
        super(self.__class__, self).__init__(cache_data=cache_data,
                                             cache_name=cache_name,
                                             timeout=timeout,
                                             encoding='utf-8')

    def process_file(self, filename, contents):
        """Processes the CC-CEDICT dictionary file's contents.

        :param str filename: The filename of the file to be processed.
        :param str contents: The contents to be processed.
        :return: The processed data.
        :rtype: :class:`dict`

        """
        logger.debug("Processing file: '%s'." % filename)
        data = {}
        rows = self.get_rows(contents.splitlines())
        for row in rows:
            if len(row) != 4:
                logger.warning("Skipping line: '%s'." % row)
                continue
            prow = self.process_row(row, comments=('#',))
            if prow is None:
                # Skip lines that process_row couldn't parse or are comments.
                logger.warning("Skipping row: '%s'." % row)
                continue
            value = {self.key_prefix + 'entry': [prow]}
            update_dict(data, {prow[0]: value})
            if prow[0] != prow[1]:
                # Add Simplified if it differs from Traditional.
                update_dict(data, {prow[1]: value})
        return data

    def get_rows(self, lines):
        for line in lines:
            m = re.match('^(?P<t>.+) (?P<s>.+) \[(?P<p>.+)\] /(?P<d>.+)/$',
                         line)
            if m is None:
                logger.warning("Unable to parse line: '%s'." % line)
                yield [line]
                continue
            t, s, p, d = m.group('t'), m.group('s'), m.group('p'), m.group('d')
            yield [t, s, p, d]

    def process_row(self, row, comments):
        """Processes the fields in *row*."""
        if row[0][0] in comments:
            logger.info("Skipping comment: '%s'." % row[0])
            return None
        pinyin_re = re.compile('(?:[a-zA-Z]+[1-5](?: (?=[a-zA-Z]+[1-5]))?)+')
        row[2] = row[2].replace('u:', 'v')
        if ' ' in row[2]:
            for p in pinyin_re.findall(row[2]):
                row[2] = row[2].replace(p, p.replace(' ', ''))
        row[2] = transcriptions.numbered_to_accented(row[2])
        if '[' in row[3]:
            for pinyin in re.findall('\[[A-Za-z1-5 ]+\]', row[3]):
                npinyin = pinyin
                if ' ' in pinyin:
                    for p in pinyin_re.findall(pinyin):
                        npinyin = npinyin.replace(p, p.replace(' ', ''))
                npinyin = transcriptions.numbered_to_accented(npinyin)
                row[3] = row[3].replace(pinyin, npinyin)
        row[3] = row[3].split('/')
        return row


class LWCWords(CSVMixin, BaseRemoteArchiveSource):
    """Fetches and processes the LWC words data.

    See parent class :class:`BaseRemoteArchiveSource` for more information.

    :param bool cache_data: Whether or not to cache the processed data.
    :param str cache_name: The cache's name.
    :param int timeout: How long in seconds until the cached data expires).

    """

    #: The URL for this data source.
    download_url = 'http://lwc.daanvanesch.nl/download.php?file=words'

    #: A tuple containing the CSV file's header.
    headers = ('word-id', 'word', 'reverse-of-word', 'count')

    #: The column number to use as a dictionary key when processing the data
    #: (counting from zero).
    index_column = 1

    #: A unique name/abbreviation for this source.
    name = 'LWC'

    #: A tuple containing names of files that should be processed. If empty,
    #: then all extracted files are processed.
    whitelist = (
        'words_types.txt',
    )

    def __init__(self, cache_data=True, cache_name='dragonmasher',
                 timeout=DEFAULT_TIMEOUT):
        super(self.__class__, self).__init__(cache_data=cache_data,
                                             cache_name=cache_name,
                                             timeout=timeout,
                                             encoding='utf-8')

    def download(self, force_download=False):
        """Downloads the LWC words file and saves it to a temporary directory.

        The temporary directory's path is accessible through the
        :attr:`temp_dir` attribute.

        After downloading the source archive, the contents are then extracted.
        The attribute :attr:`files` is set to a tuple containing the absolute
        filenames of the files extracted.

        If *force_download* is ``True``, then downloaded files and cached data
        will be deleted and the source data will be downloaded again. If
        *force_download* is ``False``, then the download will be cancelled if
        the files have already been downloaded or the processed data has been
        cached.

        :param bool force_download: Whether or not to download the source files
            even if the data is cached.

        """
        super(self.__class__, self).download(force_download=force_download,
                                             filename='LWC-words.zip')

    def process_file(self, filename, contents):
        """Processes a CSV file's contents.

        :param str filename: The filename of the file to be processed.
        :param str contents: The contents to be processed.
        :return: The processed data.
        :rtype: :class:`dict`

        """
        delimiter = ','
        exclude = (2,)
        comments = ('#',)
        logger.debug("Processing file: '%s'." % filename)
        excluded_columns = exclude + (self.index_column,)
        data = {}
        headers = trim_list(self.headers, excluded_columns)
        if is_python2:
            contents = contents.encode('utf-8')
        rows = self.get_rows(contents.splitlines(), delimiter=delimiter)
        prows = []
        for row in rows:
            prow = self.process_row(row, comments)
            if prow is None:
                logger.debug("Skipping row: '%s'" % row)
                continue
            prows.append(prow)
        del contents
        del rows
        prows.sort(key=lambda x: int(x[3]), reverse=True)
        headers.append('number')
        for n, prow in enumerate(prows, start=1):
            key = prow[self.index_column]
            trow = trim_list(prow, excluded_columns)
            trow.append(str(n))
            value = dict(zip([self.key_prefix + h for h in headers], trow))
            update_dict(data, {key: value})
        del prows
        return data

    def process_row(self, row, comments):
        """Processes the fields in *row*."""
        if row[0][0] in comments:
            return None
        if not re.search('[%s]' % zhon.hanzi.cjk_ideographs, row[1]):
            # Skip words that don't have Chinese characters.
            return None
        return row


class Unihan(CSVMixin, BaseRemoteArchiveSource):
    """Fetches and processes Unihan data.

    See parent class :class:`BaseRemoteArchiveSource` for more information.

    :param bool cache_data: Whether or not to cache the processed data.
    :param str cache_name: The cache's name.
    :param int timeout: How long in seconds until the cached data expires).

    """

    #: The URL for this data source.
    download_url = 'http://www.unicode.org/Public/UCD/latest/ucd/Unihan.zip'

    #: A tuple containing the CSV file's header.
    headers = ('character', 'field', 'value')

    #: A unique name/abbreviation for this source.
    name = 'UNIHAN'

    def __init__(self, cache_data=True, cache_name='dragonmasher',
                 timeout=DEFAULT_TIMEOUT):
        super(self.__class__, self).__init__(cache_data=cache_data,
                                             cache_name=cache_name,
                                             timeout=timeout,
                                             encoding='utf-8')

    def download(self, force_download=False):
        """Downloads the Unihan file and saves it to a temporary directory.

        The temporary directory's path is accessible through the
        :attr:`temp_dir` attribute.

        After downloading the source archive, the contents are then extracted.
        The attribute :attr:`files` is set to a tuple containing the absolute
        filenames of the files extracted.

        If *force_download* is ``True``, then downloaded files and cached data
        will be deleted and the source data will be downloaded again. If
        *force_download* is ``False``, then the download will be cancelled if
        the files have already been downloaded or the processed data has been
        cached.

        :param bool force_download: Whether or not to download the source files
            even if the data is cached.

        """
        super(self.__class__, self).download(force_download=force_download)

    def process_file(self, filename, contents):
        """Processes a Unihan data file.

        :param str filename: The filename of the file to be processed.
        :param str contents: The contents to be processed.
        :return: The processed data.
        :rtype: :class:`dict`

        """
        logger.debug("Processing file: '%s'." % filename)
        excluded_columns = (self.index_column,)
        data = {}
        if is_python2:
            contents = contents.encode('utf-8')
        rows = self.get_rows(contents.splitlines(), delimiter='\t')
        for row in rows:
            prow = self.process_row(row, ('#',))
            if prow is None:
                logger.debug("Skipping row: '%s'" % row)
                continue
            key = row[self.index_column]
            trow = trim_list(row, excluded_columns)
            value = {self.key_prefix + trow[0]: trow[1]}
            update_dict(data, {key: value})
        return data

    def process_row(self, row, comments):
        """Processes the fields in *row*."""
        if not row or row[0][0] in comments:
            return None
        row[0] = hex_to_chr(row[0][2:])
        if 'U+' in row[-1]:
            row[-1] = re.sub('U\+[A-F0-9]*', hex_to_chr, row[-1])
        return row
