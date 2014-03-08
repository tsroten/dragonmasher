"""Unpack tar/zip archives.

This module is copied from the Python 3.2 standard library.

"""

import os


class ReadError(EnvironmentError):
    """Raised when an archive cannot be read."""


def _ensure_directory(path):
    """Ensure that the parent directory of `path` exists"""
    dirname = os.path.dirname(path)
    if not os.path.isdir(dirname):
        os.makedirs(dirname)


def _unpack_zipfile(filename, extract_dir):
    """Unpack zip `filename` to `extract_dir`"""
    try:
        import zipfile
    except ImportError:
        raise ReadError('zlib not supported, cannot unpack this archive.')

    if not zipfile.is_zipfile(filename):
        raise ReadError("%s is not a zip file" % filename)

    zip = zipfile.ZipFile(filename)
    try:
        for info in zip.infolist():
            name = info.filename

            # don't extract absolute paths or ones with .. in them
            if name.startswith('/') or '..' in name:
                continue

            target = os.path.join(extract_dir, *name.split('/'))
            if not target:
                continue

            _ensure_directory(target)
            if not name.endswith('/'):
                # file
                data = zip.read(info.filename)
                f = open(target, 'wb')
                try:
                    f.write(data)
                finally:
                    f.close()
                    del data
    finally:
        zip.close()


def _unpack_tarfile(filename, extract_dir):
    """Unpack tar/tar.gz/tar.bz2 `filename` to `extract_dir`"""
    import tarfile

    try:
        tarobj = tarfile.open(filename)
    except tarfile.TarError:
        raise ReadError(
            "%s is not a compressed or uncompressed tar file" % filename)
    try:
        tarobj.extractall(extract_dir)
    finally:
        tarobj.close()


_UNPACK_FORMATS = {
    'gztar': (['.tar.gz', '.tgz'], _unpack_tarfile, [], "gzip'ed tar-file"),
    'tar':   (['.tar'], _unpack_tarfile, [], "uncompressed tar file"),
    'zip':   (['.zip'], _unpack_zipfile, [], "ZIP file")
    }


def _find_unpack_format(filename):
    for name, info in _UNPACK_FORMATS.items():
        for extension in info[0]:
            if filename.endswith(extension):
                return name
    return None


def unpack_archive(filename, extract_dir=None, format=None):
    """Unpack an archive.

    If *format* is not provided, :func:`unpack_archive` will use the filename
    extension and see if an unpacker was registered for that extension. In case
    none is found, a :exc:`ValueError` is raised.

    :param str filename: The the full path of the archive file.
    :param str extract_dir: The name of the target directory where the archive
        is unpacked. If not provided, the current working directory is used.
    :param str format: The archive format (one of ``'zip'``, ``'tar'``, or
        ``'gztar'``)

    """
    if extract_dir is None:
        extract_dir = os.getcwd()

    if format is not None:
        try:
            format_info = _UNPACK_FORMATS[format]
        except KeyError:
            raise ValueError("Unknown unpack format '{0}'".format(format))

        func = format_info[1]
        func(filename, extract_dir, **dict(format_info[2]))
    else:
        # we need to look at the registered unpackers supported extensions
        format = _find_unpack_format(filename)
        if format is None:
            raise ReadError("Unknown archive format '{0}'".format(filename))

        func = _UNPACK_FORMATS[format][1]
        kwargs = dict(_UNPACK_FORMATS[format][2])
        func(filename, extract_dir, **kwargs)
