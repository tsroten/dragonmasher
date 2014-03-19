# -*- coding: utf-8 -*-
"""Unit tests for the dragonmasher.data module."""

from __future__ import unicode_literals
import unittest

from dragonmasher import data
from dragonmasher.sources import BaseSource


class DataFunctionsTestCase(unittest.TestCase):
    """Unit tests for data processing functions."""

    def test_mash(self):
        """Tests that data.mash() works correctly."""
        class Source(BaseSource):
            def __init__(self, data):
                self.data = data
                super(self.__class__, self).__init__()

        data1 = {1: {'a': 1, 'b': 2, 'c': 3}}
        source1 = Source(data1)
        data2 = {2: {'g': 7, 'h': 8, 'i': 9}}
        source2 = Source(data2)
        data3 = {1: {'d': 4, 'e': 5, 'f': 6}}
        source3 = Source(data3)
        data13 = {1: {'a': 1, 'b': 2, 'c': 3, 'd': 4, 'e': 5, 'f': 6}}

        mash12na = data.mash(source1, source2, annotate=True)
        self.assertEqual(data1, mash12na)
        mash12a = data.mash(source1, source2, annotate=False)
        self.assertTrue(2 in mash12a)
        mash13 = data.mash(source1, source3)
        self.assertEqual(data13, mash13)
