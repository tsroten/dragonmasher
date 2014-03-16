.. currentmodule:: dragonmasher.sources

``dragonmasher.sources``
========================

Ready-to-use Data Source Classes
--------------------------------

The following classes are fully implemented and ready to be used. Some of them have a :meth:`download` method because they fetch and process remote data. Others have no :meth:`download` method because they process locally-stored data that is shipped with Dragon Masher.

To use a local data source, simply create an object and call it's :meth:`read` method. For example:

.. code:: python

    >>> hsk = HSK()
    >>> hsk.read()

To use a remote data source, do the same as above, except call :meth:`download` before calling :meth:`read`:

.. code:: python

    >>> subtlex = SUBTLEX()
    >>> subtlex.download()
    >>> subtlex.read()

In both cases the processed data is accessible in the :attr:`data` attribute.

.. autoclass:: HSK

    .. attribute:: data
        :annotation:

        A dictionary containing the processed source data.

    .. automethod:: read

.. autoclass:: TOCFL

    .. attribute:: data
        :annotation:

        A dictionary containing the processed source data.

    .. automethod:: read

.. autoclass:: XianDaiChangYongZi

    .. attribute:: data
        :annotation:

        A dictionary containing the processed source data.

    .. automethod:: read

.. autoclass:: SUBTLEX

    .. attribute:: data
        :annotation:

        A dictionary containing the processed source data.

    .. automethod:: download(force_download=False)

    .. automethod:: read

.. autoclass:: JunDaClassicalCharacterList

    .. attribute:: data
        :annotation:

        A dictionary containing the processed source data.

    .. automethod:: download(force_download=False)

    .. automethod:: read

.. autoclass:: JunDaModernCharacterList

    .. attribute:: data
        :annotation:

        A dictionary containing the processed source data.

    .. automethod:: download(force_download=False)

    .. automethod:: read

.. autoclass:: JunDaImaginativeCharacterList

    .. attribute:: data
        :annotation:

        A dictionary containing the processed source data.

    .. automethod:: download(force_download=False)

    .. automethod:: read

.. autoclass:: JunDaInformativeCharacterList

    .. attribute:: data
        :annotation:

        A dictionary containing the processed source data.

    .. automethod:: download(force_download=False)

    .. automethod:: read

.. autoclass:: JunDaCombinedCharacterList

    .. attribute:: data
        :annotation:

        A dictionary containing the processed source data.

    .. automethod:: download(force_download=False)

    .. automethod:: read

.. autoclass:: CEDICT

    .. attribute:: data
        :annotation:

        A dictionary containing the processed source data.

    .. automethod:: download(force_download=False)

    .. automethod:: read

.. autoclass:: LWCWords

    .. attribute:: data
        :annotation:

        A dictionary containing the processed source data.

    .. automethod:: download(force_download=False)

    .. automethod:: read
 
.. autoclass:: Unihan

    .. attribute:: data
        :annotation:

        A dictionary containing the processed source data.

    .. automethod:: download(force_download=False)

    .. automethod:: read


Base Data Source Classes
------------------------

The following constants and classes can be used to create your own Chinese data source classes like those above. When creating a data source class, be sure that your class (or a parent class) fully implements :meth:`read_file` and :meth:`process_file`.

In general, unless you need to customize the class extensively, it's best not to directly inherit from :class:`BaseSource` since the other base classes provide you with further built-in functionality.

.. autodata:: DEFAULT_TIMEOUT

.. autoclass:: BaseSource

    .. automethod:: __init__

    .. autoinstanceattribute:: data
        :annotation:

    .. autoinstanceattribute:: encoding
        :annotation:

    .. autoinstanceattribute:: files
        :annotation:

    .. autoattribute:: key_prefix

    .. autoinstanceattribute:: name
        :annotation:

    .. automethod:: process_file

    .. automethod:: read

    .. automethod:: read_file

.. autoclass:: BaseLocalSource

    .. automethod:: __init__

    .. attribute:: data
        :annotation:

        A dictionary containing the processed source data.

    .. attribute:: encoding
        :annotation:

        The file encoding to use when opening the source's files.

    .. attribute:: files
        :annotation:

        A tuple containing the paths to the source's files.

    .. autoattribute:: key_prefix

    .. attribute:: name
        :annotation:

        A string containing the name/abbreviation for this source.

    .. automethod:: process_file

    .. automethod:: read

    .. automethod:: read_file

.. autoclass:: BasePackageResourceSource

    .. automethod:: __init__

    .. attribute:: data
        :annotation:

        A dictionary containing the processed source data.

    .. attribute:: encoding
        :annotation:

        The file encoding to use when opening the source's files.

    .. attribute:: files
        :annotation:

        A tuple containing the paths to the source's files.

    .. autoattribute:: key_prefix

    .. attribute:: name
        :annotation:

        A string containing the name/abbreviation for this source.

    .. automethod:: process_file

    .. automethod:: read

    .. automethod:: read_file

.. autoclass:: BaseRemoteSource

    .. automethod:: __init__

    .. attribute:: cache

        A :class:`~fcache.cache.FileCache` object for storing data. This
        attribute is only set if :attr:`cache_data` is ``True``.

    .. autoinstanceattribute:: cache_data
        :annotation:

    .. attribute:: data
        :annotation:

        A dictionary containing the processed source data.

    .. automethod:: download

    .. attribute:: encoding
        :annotation:

        The file encoding to use when opening the source's files.

    .. attribute:: files
        :annotation:

        A tuple containing the paths to the source's files.

    .. autoattribute:: has_data

    .. autoattribute:: has_files

    .. autoattribute:: key_prefix

    .. attribute:: name
        :annotation:

        A string containing the name/abbreviation for this source.

    .. automethod:: process_file

    .. automethod:: read

    .. automethod:: read_file

    .. autoinstanceattribute:: temp_dir
        :annotation:

.. autoclass:: BaseRemoteArchiveSource

    .. automethod:: __init__

    .. attribute:: cache

        A :class:`~fcache.cache.FileCache` object for storing data. This
        attribute is only set if :attr:`cache_data` is ``True``.

    .. attribute:: cache_data
        :annotation:

        A boolean value indicating whether or not to cache processed data.

    .. attribute:: data
        :annotation:

        A dictionary containing the processed source data.

    .. automethod:: download

    .. attribute:: encoding
        :annotation:

        The file encoding to use when opening the source's files.

    .. automethod:: extract

    .. attribute:: files
        :annotation:

        A tuple containing the paths to the source's files.

    .. autoattribute:: has_data

    .. autoattribute:: has_files

    .. autoattribute:: key_prefix

    .. attribute:: name
        :annotation:

        A string containing the name/abbreviation for this source.

    .. automethod:: process_file

    .. automethod:: read

    .. automethod:: read_file

    .. attribute:: temp_dir
        :annotation:

        A string indicating the path to this instance’s temporary directory.

    .. autoinstanceattribute:: whitelist
        :annotation:

.. autoclass:: CSVMixin
    :members:
    :exclude-members: headers, index_column

    .. autoattribute:: headers
        :annotation:

    .. autoattribute:: index_column
        :annotation:

.. autoclass:: BaseJunDa

    .. automethod:: __init__

    .. attribute:: cache

        A :class:`~fcache.cache.FileCache` object for storing data. This
        attribute is only set if :attr:`cache_data` is ``True``.

    .. attribute:: cache_data
        :annotation:

        A boolean value indicating whether or not to cache processed data.

    .. attribute:: data
        :annotation:

        A dictionary containing the processed source data.

    .. automethod:: download

    .. attribute:: encoding
        :annotation:

        The file encoding to use when opening the source's files.

    .. attribute:: files
        :annotation:

        A tuple containing the paths to the source's files.

    .. autoattribute:: has_data

    .. autoattribute:: has_files

    .. autoattribute:: headers
        :annotation:

    .. autoattribute:: index_column
        :annotation:

    .. autoattribute:: key_prefix

    .. attribute:: name
        :annotation:

        A string containing the name/abbreviation for this source.

    .. automethod:: process_file

    .. automethod:: read

    .. automethod:: read_file

    .. attribute:: temp_dir
        :annotation:

        A string indicating the path to the object’s temporary directory.
    

``dragonmasher.unpack``
=======================

.. automodule:: dragonmasher.unpack
    :members:
