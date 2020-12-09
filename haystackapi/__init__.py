# -*- coding: utf-8 -*-
# Zinc dumping and parsing module
# (C) 2016 VRT Systems
#
# vim: set ts=4 sts=4 et tw=78 sw=4 si:

from .pintutil import define_haystack_units

unit_reg = define_haystack_units()

from .grid import Grid
from .dumper import dump, dump_scalar
from .parser import parse, parse_scalar, MODE_JSON, MODE_ZINC, MODE_CSV, suffix_to_mode, mode_to_suffix
from .grid_filter import parse_filter, parse_date_format
from .metadata import MetadataObject
from .datatypes import Quantity, Coordinate, Uri, Bin, MARKER, NA, \
    REMOVE, Ref, XStr
from .version import Version, VER_2_0, VER_3_0, LATEST_VER
from .ops import *
from .providers import HaystackInterface

__all__ = ['Grid', 'dump', 'parse', 'dump_scalar', 'parse_scalar', 'parse_filter',
           'MetadataObject', 'unit_reg', 'zoneinfo',
           'Coordinate', 'Uri', 'Bin', 'XStr', 'Quantity', 'MARKER', 'NA', 'REMOVE', 'Ref',
           'MODE_JSON', 'MODE_ZINC', 'MODE_CSV', 'suffix_to_mode', 'mode_to_suffix',
           'parse_date_format',
           'VER_2_0', 'VER_3_0', 'LATEST_VER', 'Version', '__version__',

           "HaystackInterface",
           "about",
           "ops",
           "formats",
           "read",
           "nav",
           "watch_sub",
           "watch_unsub",
           "watch_poll",
           "point_write",
           "his_read",
           "his_write",
           "invoke_action",
           ]

__author__ = 'Ph. Prados, VRT Systems'
__copyright__ = 'Copyright 2016-2020, Ph. Prados & VRT System'
__credits__ = ['Philippe PRADOS',
               'VRT Systems',
               'Engie digital'
               'Christian Tremblay',
               'SamuelToh',
               'Stuart Longland',
               'joyfun'
               ]
__license__ = 'BSD'
__version__ = '0.1'
__maintainer__ = 'Philippe PRADOS'
__email__ = 'haystackapi@prados.fr'
