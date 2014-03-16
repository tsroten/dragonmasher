# -*- coding: utf-8 -*-
"""Unit tests for the dragonmasher.utils module."""

from __future__ import unicode_literals
import re
import unittest

from dragonmasher import utils


class UtilsFunctionsTestCase(unittest.TestCase):
    """Unit Tests for helper functions."""

    def test_hex_to_chr(self):
        """Tests that hex_to_chr works correctly."""
        self.assertEqual('㓨', utils.hex_to_chr('U+34E8'))
        self.assertEqual('㓨',
                         re.sub('U\+[A-F0-9]*', utils.hex_to_chr, 'U+34E8'))

    def test_trim_list(self):
        """Tests that trim_list works correctly."""
        L1 = [0, 1, 2, 3, 4, 5, 6]
        L1_expected = [1, 2, 4, 6]
        excluded = [0, 3, 5]

        L1_actual = utils.trim_list(L1, excluded)
        self.assertEqual(L1_expected, L1_actual)

    def test_update_dict(self):
        """Tests that update_dict works correctly."""
        d1 = {'1': {'1': '1'}}
        d2 = {'2': {'2': '2'}}
        d12 = {'1': {'1': '1'}, '2': {'2': '2'}}
        d3 = {'3': {'3': '4'}}
        d4 = {'3': {'3': '5'}}
        d34 = {'3': {'3': ['4', '5']}}

        utils.update_dict(d1, d2)
        self.assertEqual(d12, d1)
        utils.update_dict(d3, d4)
        self.assertEqual(d34, d3)

        # Check duplicates
        d22 = {'2': {'2': '2'}}
        d22copy = {'2': {'2': '2'}}
        utils.update_dict(d22, d22copy, allow_duplicates=False)
        self.assertEqual(d22copy, d22)
        utils.update_dict(d22, d22copy, allow_duplicates=True)
        self.assertEqual({'2': {'2': ['2', '2']}}, d22)

    def test_update_dict_annotate(self):
        """Tests that update_dict handles the *annotate* argument correctly."""
        d1 = {'1': {'1': '1'}}
        d2 = {'2': {'2': '2'}}

        utils.update_dict(d1, d2, annotate=True)
        self.assertEqual({'1': {'1': '1'}}, d1)
        utils.update_dict(d1, d2, annotate=False)
        self.assertEqual({'1': {'1': '1'}, '2': {'2': '2'}}, d1)
