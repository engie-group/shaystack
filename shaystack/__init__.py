# -*- coding: utf-8 -*-
# Haystack module
# See the accompanying LICENSE file.
# (C) 2016 VRT Systems
# (C) 2021 Engie Digital
#
# vim: set ts=4 sts=4 et tw=78 sw=4 si:
"""
Implementation of Haystack project https://www.project-haystack.org/
Propose API :

- to read or write Haystack file (Zinc, JSon, CSV)
- to manipulate ontology in memory (Grid class)
- to implement REST API (https://project-haystack.org/doc/docHaystack/HttpApi)
- to implement GraphQL API

With some sample provider:

- Import ontology on S3 bucket
- Import ontology on SQLite or Postgres
- and expose the data via Flask or AWS Lambda
"""
from .datatypes import Quantity, Coordinate, Uri, Bin, MARKER, NA, \
    REMOVE, Ref, XStr
from .dumper import dump, dump_scalar
from .grid import Grid
from .grid_filter import parse_filter, parse_hs_datetime_format
from .metadata import MetadataObject
from .ops import *
from .parser import parse, parse_scalar, MODE_HAYSON, MODE_JSON, MODE_TRIO, MODE_ZINC, MODE_CSV, \
    suffix_to_mode, mode_to_suffix
from .pintutil import unit_reg
from .providers import HaystackInterface
from .type import HaystackType, Entity
from .version import Version, VER_2_0, VER_3_0, LATEST_VER

__all__ = ['Grid', 'dump', 'parse', 'dump_scalar', 'parse_scalar', 'parse_filter',
           'MetadataObject', 'unit_reg', 'zoneinfo',
           'HaystackType', 'Entity',
           'Coordinate', 'Uri', 'Bin', 'XStr', 'Quantity', 'MARKER', 'NA', 'REMOVE', 'Ref',
           'MODE', 'MODE_JSON', 'MODE_HAYSON', 'MODE_ZINC', 'MODE_TRIO', 'MODE_CSV',
           'suffix_to_mode', 'mode_to_suffix',
           'parse_hs_datetime_format',
           'VER_2_0', 'VER_3_0', 'LATEST_VER', 'Version',

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

__pdoc__ = {
    "csvdumper": False,
    "csvparser": False,
    "datatypes": False,
    "dumper": False,
    "filter_ast": False,
    "grid": False,
    "grid_diff": False,
    "grid_filter": False,
    "jsondumper": False,
    "jsonparser": False,
    "metadata": False,
    "ops": False,
    "parser": False,
    "pintutil": False,
    "sortabledict": False,
    "triodumper": False,
    "trioparser": False,
    "version": False,
    "zincdumper": False,
    "zincparser": False,
    "zoneinfo": False,
}
__author__ = 'Engie Digital, VRT Systems'
__copyright__ = 'Copyright 2016-2020, Engie Digital & VRT System'
__credits__ = ['See AUTHORS']
__license__ = 'BSD'
__maintainer__ = 'Philippe PRADOS'
__email__ = 'shaystack@prados.fr'
