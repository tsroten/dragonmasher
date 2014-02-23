"""Unit tests for dragonmasher.unpack."""

import os
import shutil
import tempfile
import unittest

from dragonmasher.unpack import unpack_archive


class UnpackArchiveTestCase(unittest.TestCase):
    """Tests for the dragonmasher.unpack module."""

    expected_file_name = 'unpack_test.txt'
    expected_contents = 'Hello world!\n'

    def __init__(self, *args, **kwargs):
        """Sets the data_dir attribute."""
        self.data_dir = os.path.join(os.path.dirname(__file__), 'data')
        super(UnpackArchiveTestCase, self).__init__(*args, **kwargs)

    def setUp(self):
        """Creates a temporary directory."""
        self.temp_dir = tempfile.mkdtemp()

    def tearDown(self):
        """Removes the temporary directory and its contents."""
        shutil.rmtree(self.temp_dir)

    def _test_unpack_archive(self, file_extension):
        archive_file = os.path.join(self.data_dir, 'unpack_test' +
                                    file_extension)
        unpack_archive(archive_file, self.temp_dir)
        files = os.listdir(self.temp_dir)
        self.assertTrue(self.expected_file_name in files)
        with open(os.path.join(self.temp_dir, self.expected_file_name)) as f:
            contents = f.read()
        self.assertEqual(self.expected_contents, contents)

    def test_unpack_archive_gztar(self):
        """Tests that unpack_archive correctly unpacks a gztar archive file."""
        self._test_unpack_archive('.tar.gz')

    def test_unpack_archive_tar(self):
        """Tests that unpack_archive correctly unpacks a tar archive file."""
        self._test_unpack_archive('.tar')

    def test_unpack_archive_zip(self):
        """Tests that unpack_archive correctly unpacks a zip archive file."""
        self._test_unpack_archive('.zip')
