"""Data functions and classes for dragonmasher."""

from __future__ import unicode_literals

from dragonmasher.sources import BaseSource
from dragonmasher.utils import update_dict


def mash(*args, **kwargs):
    """Mashes data sources together.

    :param dragonmasher.sources.BaseSource *args: Two or more child classes of
        :class:`dragonmasher.sources.BaseSource` (e.g.
        :class:`dragonmasher.sources.HSK` or
        :class:`dragonmasher.sources.SUBTLEX`).
    :param bool annotate: Whether or not to ignore keys not present in the
        first data source. In other words, if ``True``, the first source's data
        is annotated with data from the other sources.

    """
    annotate = kwargs.pop('annotate', False)
    if len(args) < 2:
        return ValueError("mash expects at least 2 data sources.")
    for arg in args:
        if not (isinstance(arg, dict) or isinstance(arg, BaseSource)):
            raise TypeError("arguments must be of type dict or BaseSource.")

    mashed = {}
    first_mash = True
    for arg in args:
        if isinstance(arg, BaseSource):
            arg = arg.data
        update_dict(mashed, arg, annotate=False if first_mash else annotate)
        first_mash = False
    return mashed
