# -*- coding: utf-8 -*-
# Zinc dumping and parsing module
# (C) 2016 VRT Systems
#
# vim: set ts=4 sts=4 et tw=78 sw=4 si:
import base64
import binascii
import datetime
import random
import string
import sys
import traceback

import six

import hszinc
from hszinc import VER_3_0, Grid, MODE_ZINC, MODE_JSON, XStr
from .pint_enable import to_pint

STR_CHARSET = string.ascii_letters + string.digits + '\n\r\t\f\b'

GENERATION_NUMBER = 1 # FIXME
PERCENT_RECURSIVE = 1


def gen_random_const():
    return random.choice([True, False, None, hszinc.MARKER, hszinc.REMOVE, hszinc.NA])


def gen_random_ref():
    # Generate a randomised reference.
    name = gen_random_str(charset= \
                              string.ascii_letters + string.digits \
                              + '_:-.~')
    if random.choice([True, False]):
        value = gen_random_str(charset= \
                                   string.ascii_letters + string.digits + '_')
    else:
        value = None

    return hszinc.Ref(name, value)


def gen_random_bin():
    # Generate a randomized binary
    return hszinc.Bin(random.choice([
        'text/plain',
        'text/html',
        'text/zinc',
        'application/json',
        'application/octet-stream',
        'image/png',
        'image/jpeg',
    ]))


def gen_random_xstr():
    # Generate a randomized binary
    barray = bytearray(random.getrandbits(8) for _ in range(5))
    return XStr(*random.choice([
        ('hex', binascii.hexlify(barray).decode('ascii')),
        ('b64', binascii.b2a_base64(barray)[:-1] if sys.version_info[0] <= 2
            else binascii.b2a_base64(barray).decode("ascii")
         )
    ]))


def gen_random_uri():
    return hszinc.Uri(gen_random_str(charset= \
                                         string.ascii_letters + string.digits))


def gen_random_str(min_length=1, max_length=20, charset=STR_CHARSET):
    # Generate a random 20-character string
    return ''.join([random.choice(charset) for c in range(0,
                                                          random.randint(min_length, max_length))])


def gen_random_date():
    # This might generate an invalid date, we keep trying until we get one.
    while True:
        try:
            return datetime.date(random.randint(1, 3000),
                                 random.randint(1, 12), random.randint(1, 31))
        except ValueError:
            pass


def gen_random_time():
    return datetime.time(random.randint(0, 23), random.randint(0, 59),
                         random.randint(0, 59), random.randint(0, 999999))


def gen_random_date_time():
    # Pick a random timezone
    tz_name = random.choice(list(hszinc.zoneinfo.get_tz_map().keys()))
    tz = hszinc.zoneinfo.timezone(tz_name)
    return tz.localize(datetime.datetime.combine(
        gen_random_date(), gen_random_time()))


def gen_random_coordinate():
    return hszinc.Coordinate( \
        round(gen_random_num(360) - 180.0, 2),
        round(gen_random_num(360) - 180.0, 2))


def gen_random_num(scale=1000, digits=2):
    return round(random.random() * scale, digits)


def gen_random_quantity():
    return hszinc.Quantity(gen_random_num(),
                           to_pint('percent'))


def gen_random_list():
    return [gen_random_scalar() for x in range(0, random.randint(0, 2))]


def gen_random_map():
    return {gen_random_name(): gen_random_scalar() for x in range(0, random.randint(0, 2))}


RANDOM_TYPES = [
    # Only for v2.0 gen_random_bin,
    gen_random_xstr,
    # gen_random_const, gen_random_ref, gen_random_uri, gen_random_xstr,
    # gen_random_str, gen_random_date, gen_random_time, gen_random_date_time,
    # gen_random_coordinate, gen_random_num, gen_random_quantity
]


def gen_random_scalar():
    if (random.randint(0, 100) < PERCENT_RECURSIVE):
        return random.choice(RANDOM_RECURSIVE_TYPES)()
    else:
        return random.choice(RANDOM_TYPES)()


def gen_random_name(existing=None):
    while True:
        meta = random.choice(string.ascii_lowercase) \
               + gen_random_str(min_length=0, max_length=7, \
                                charset=string.ascii_letters + string.digits)
        if (existing is None) or (meta not in existing):
            return meta


def gen_random_meta():
    meta = hszinc.MetadataObject()
    names = set()
    for n in range(0, random.randint(1, 5)):
        name = gen_random_name(existing=names)
        value = gen_random_scalar()
        meta[name] = value
    return meta


def gen_random_grid():
    # Generate a randomised grid of values and try parsing it back.
    grid = hszinc.Grid(version=VER_3_0)
    grid.metadata.extend(gen_random_meta())

    # Randomised columns
    for n in range(0, random.randint(1, 5)):
        col_name = gen_random_name(existing=grid.column)
        if random.choice([True, False]):
            grid.column[col_name] = gen_random_meta()
        else:
            grid.column[col_name] = {}

    # Randomised rows
    for n in range(0, random.randint(0, 20)):
        row = {}
        for c in grid.column.keys():
            if random.choice([True, False]):
                row[c] = gen_random_scalar()
        grid.append(row)

    return grid


RANDOM_RECURSIVE_TYPES = [gen_random_list, gen_random_map, gen_random_grid]


def dump_grid(g):
    print('Version: %s' % g.version)
    print('Metadata:')
    for k, v in g.metadata.items():
        print('   %s = %r' % (k, v))
    print('Columns:')
    for c, meta in g.column.items():
        print('   %s:' % c)
        for k, v in g.column[c].items():
            print('      %s = %r' % (k, v))
    print('Rows:')
    for row in g:
        print('---')
        for c, v in row.items():
            print('  %s = %r' % (c, v))


def approx_check(v1, v2):
    # Check types match
    if (isinstance(v1, six.string_types) \
            and isinstance(v2, six.string_types)):
        assert type(v1) == type(v2), '%s != %s' % (type(v1), type(v2))
    if isinstance(v1, datetime.time):
        assert v1.replace(microsecond=0) == v2.replace(microsecond=0)
    elif isinstance(v1, datetime.datetime):
        assert v1.tzinfo == v2.tzinfo
        assert v1.date() == v2.date()
        approx_check(v1.time(), v2.time())
    elif isinstance(v1, hszinc.Quantity):
        assert v1.unit == v2.unit
        approx_check(v1.value, v2.value)
    elif isinstance(v1, hszinc.Coordinate):
        approx_check(v1.latitude, v2.latitude)
        approx_check(v1.longitude, v2.longitude)
    elif isinstance(v1, float) or isinstance(v2, float):
        assert abs(v1 - v2) < 0.000001
    elif isinstance(v1, Grid):
        approx_check_grid(v1, v2)
    else:
        assert v1 == v2, '%r != %r' % (v1, v2)


def _try_dump_parse(ref_grid, mode):
    try:
        # Dump the randomised grid to a string
        grid_str = hszinc.dump(ref_grid, mode=mode)
    except:
        # Dump some detail about the grid
        print('Failed to dump grid.')
        dump_grid(ref_grid)
        raise

    # Parse the grid string
    try:
        parsed_grid = hszinc.parse(grid_str, mode=mode, single=True)
    except:
        print('Failed to parse dumped grid')
        dump_grid(ref_grid)
        print('--- Parsed string ---')
        print(grid_str)
        raise

    approx_check_grid(parsed_grid, ref_grid)


def try_dump_parse_json():
    ref_grid = gen_random_grid()
    _try_dump_parse(ref_grid, MODE_JSON)


def try_dump_parse_zinc():
    ref_grid = gen_random_grid()
    _try_dump_parse(ref_grid, MODE_ZINC)


def approx_check_grid(parsed_grid, ref_grid):
    # Check metadata matches
    try:
        assert set(ref_grid.metadata.keys()) \
               == set(parsed_grid.metadata.keys())
        for key in ref_grid.metadata.keys():
            approx_check(ref_grid.metadata[key], parsed_grid.metadata[key])
    except:
        print(traceback.format_exc())
        print('Mismatch in metadata')
        print('Reference grid')
        dump_grid(ref_grid)
        print('Parsed grid')
        dump_grid(parsed_grid)
        raise

    try:
        # Check column matches
        assert set(ref_grid.column.keys()) \
               == set(parsed_grid.column.keys())
    except:
        print(traceback.format_exc())
        print('Mismatch in column')
        print('Reference grid')
        dump_grid(ref_grid)
        print('Parsed grid')
        dump_grid(parsed_grid)
        raise
    for col in ref_grid.column.keys():
        try:
            for key in ref_grid.column[col].keys():
                approx_check(ref_grid.column[col][key], \
                             parsed_grid.column[col][key])
        except:
            print(traceback.format_exc())
            print('Mismatch in metadata for column %s' % col)
            print('Reference: %r' % ref_grid.column[col])
            print('Parsed:    %r' % parsed_grid.column[col])
            raise

    try:
        # Check row matches
        assert len(ref_grid) == len(parsed_grid)
    except:
        print(traceback.format_exc())
        print('Mismatch in row count')
        print('Reference grid')
        dump_grid(ref_grid)
        print('Parsed grid')
        dump_grid(parsed_grid)

    for (ref_row, parsed_row) in zip(ref_grid, parsed_grid):
        try:
            for col in ref_grid.column.keys():
                approx_check(ref_row.get(col), parsed_row.get(col))
        except:
            print(traceback.format_exc())
            print('Mismatch in row')
            print('Reference:')
            print(ref_row)
            print('Parsed:')
            print(parsed_row)
            raise
    assert parsed_grid == ref_grid


def test_loopback_zinc():
    for trial in range(0, GENERATION_NUMBER):
        try_dump_parse_zinc()


def test_loopback_json():
    for trial in range(0, GENERATION_NUMBER):
        try_dump_parse_json()
