# -*- coding: utf-8 -*-
"""Unit tests for the dragonmasher.sources module."""

from __future__ import unicode_literals
import unittest

from dragonmasher import sources


class LocalSourceTestCase(unittest.TestCase):
    """Tests for the local source classes.

    This tests the BaseLocalSource class and the CSVMixin class.

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
