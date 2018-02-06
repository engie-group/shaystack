# -*- coding: utf-8 -*-
# Zinc dumping and parsing module
# (C) 2016 VRT Systems
#
# vim: set ts=4 sts=4 et tw=78 sw=4 si:

import warnings

# First verify if pint is available
PINT_AVAILABLE = False
try:
    from pint import UnitRegistry
    PINT_AVAILABLE = True
    from .pintutil import define_haystack_units
    ureg = define_haystack_units()
except ImportError: # pragma: no cover
    # For setup.py to interrogate the version information.  This should *NOT*
    # get executed in production, and if it did, things wouldn't work anyway.
    ureg = {'Quantity': None}

try:
    from .grid import Grid
    from .dumper import dump, dump_scalar
    from .parser import parse, parse_scalar, MODE_JSON, MODE_ZINC
    from .metadata import MetadataObject
    from .datatypes import Quantity, Coordinate, Uri, Bin, MARKER, REMOVE, Ref, use_pint
    from .version import Version, VER_2_0, VER_3_0, LATEST_VER
    Q_ = Quantity
    __all__ = ['Grid', 'dump', 'parse', 'dump_scalar', 'parse_scalar',
            'MetadataObject', 'ureg',
            'Coordinate', 'Uri', 'Bin', 'MARKER', 'REMOVE', 'Ref',
            'MODE_JSON', 'MODE_ZINC',
            'VER_2_0', 'VER_3_0', 'LATEST_VER', 'Version']
except ImportError as e: # pragma: no cover
    # For setup.py to interrogate the version information.  This should *NOT*
    # get executed in production, and if it did, things wouldn't work anyway.
    warnings.warn(
        'Failed to import libraries: %s, dependencies may be missing' \
                % e)

__author__ = 'VRT Systems'
__copyright__ = 'Copyright 2016, VRT Systems'
__credits__ = ['VRT Systems']
__license__ = 'BSD'
__version__ = '1.2.0'
__maintainer__ = 'VRT Systems'
__email__ = 'support@vrt.com.au'
