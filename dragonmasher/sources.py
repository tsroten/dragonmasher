"""Chinese data source classes and methods."""

import logging
import pkgutil

logger = logging.getLogger(__name__)


class BaseSource(object):
    """Base class for Chinese data sources."""

    def __init__(self, encoding='utf-8'):
        self.files = None if not hasattr(self, 'files') else self.files
        self.data = None if not hasattr(self, 'data') else self.data
        self.encoding = encoding
        self.key_prefix = self.name + '-'

    def read(self):
        """Reads and processes the data, then stores data in self.data."""
        raise NotImplemented


class BaseLocalSource(BaseSource):
    """Base class for local Chinese data sources."""

    def __init__(self, encoding=None):
        super(BaseLocalSource, self).__init__()
        self.data = {}

    def read(self):
        """Reads and processes the data, then stores data in self.data."""
        for name in self.files:
            logger.debug("Opening file for reading: '%s'." % name)
            contents = pkgutil.get_data('dragonmasher',
                                        name).decode(self.encoding)
            logger.debug("Processing file: '%s'." % name)
            self._read_file(name, contents)

    def _read_file(self, name, contents):
        """Processes and stores the file contents into self.data."""
        raise NotImplemented


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

    def __init__(self, index_column=0, encoding='utf-8'):
        self.files = ('data/hsk.csv',)
        self.headers = ('word', 'level')
        self.name = 'HSK'
        super(HSK, self).__init__(index_column=index_column, encoding=encoding)


class TOCFL(CSVMixin, BaseLocalSource):
    """A class for reading local TOCFL data."""

    def __init__(self, index_column=0, encoding='utf-8'):
        self.files = ('data/tocfl.csv',)
        self.headers = ('word', 'level', 'pos', 'category')
        self.name = 'TOCFL'
        super(TOCFL, self).__init__(index_column=index_column,
                                    encoding=encoding)


class XianDaiChangYongZi(CSVMixin, BaseLocalSource):
    """A class for reading local XianDaiChangYongZi data."""

    def __init__(self, index_column=0, encoding='utf-8'):
        self.files = ('data/xdcyz.csv',)
        self.headers = ('character', 'level', 'strokes')
        self.name = 'XDCYZ'
        super(XianDaiChangYongZi, self).__init__(index_column=index_column,
                                                 encoding=encoding)
