# -*- coding: utf-8 -*-
import collections
import locale
from collections.abc import Callable

if not hasattr(collections, 'Callable'):
    collections.Callable = Callable

if not hasattr(locale, 'format'):
    locale.format = locale.format_string

__version__ = '0.0.1'
