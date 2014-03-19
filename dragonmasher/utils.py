# -*- coding: utf-8 -*-
"""Utility functions for dragonmasher."""

from __future__ import unicode_literals
import sys

is_python3 = sys.version_info[0] > 2

if not is_python3:
    str = unicode


def hex_to_chr(h):
    """Covert strings like 'U+4E5D' to corresponding Unicode characters.

    This function also works with regular expression match objects.

    """
    if hasattr(h, 'group'):
        h = h.group()
    ordinal = int(h.strip('U+'), 16)
    return chr(ordinal) if is_python3 else unichr(ordinal)


def trim_list(L, excluded):
    """Removes unwanted itmes from a list."""
    return [item for i, item in enumerate(L) if i not in excluded]


def update_dict(d, other, allow_duplicates=False, annotate=False):
    """Updates a dict *d* with the key/value pairs from *other*.

    *d* and *other* are dictionaries that contain dictionaries. It is the
    second layer of dictionaries that are updated.

    Existing keys are not overwritten, but instead their values are
    converted to a list and the new value is appended. Duplicate values are
    ignored (if *allow_duplicates* is ``False``).

    :param dict d: A base dictionary that should be updated.
    :param dict other: A dictionary whose key/value pairs should be added
        to *d*.
    :param bool allow_duplicates: Whether or not to add duplicate values to
        *d*.
    :param bool annotate: Whether or not to ignore keys present in *other* that
        aren't present in *d*. In other words, if ``True``, *other*'s values
        are used to annotate *d*'s existing values.

    """
    for key, value in other.items():
        if key not in d and annotate is True:
            continue
        d.setdefault(key, {})
        overlap = bool(set(list(d[key])).intersection(set(list(value))))
        if not overlap:
            if isinstance(value, dict):
                d[key].update(value)
            else:
                d[key] = value
            continue
        for k, v in value.items():
            if k not in d[key]:
                d[key][k] = v
                continue
            dvalue = d[key][k]
            if (((isinstance(dvalue, list) and v in dvalue) or
                    (isinstance(dvalue, str) and v == dvalue)) and
                    allow_duplicates is False):
                continue
            elif not isinstance(dvalue, list):
                d[key][k] = [dvalue]
            if isinstance(v, list):
                d[key][k].extend(v)
            else:
                d[key][k].append(v)
