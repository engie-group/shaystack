# -*- coding: utf-8 -*-
# Zinc dumping and parsing module
# (C) 2016 VRT Systems
#
# vim: set ts=4 sts=4 et tw=78 sw=4 si:
import binascii
import datetime
import random
import string
import sys

import hszinc
from hszinc import VER_3_0, MODE_ZINC, MODE_JSON, XStr, MetadataObject, MODE_CSV
from .pint_enable import to_pint

STR_CHARSET = string.ascii_letters + string.digits + '\n\r\t\f\b'

GENERATION_NUMBER, \
GENERATION_COLUMN, \
GENERATION_ROW, \
PERCENT_GEN_ID, \
PERCENT_RECURSIVE = (10, 5, 10, 30, 5)

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
    return u''.join([random.choice(charset) for c in range(0,
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
    gen_random_const, gen_random_ref, gen_random_uri, gen_random_xstr,
    gen_random_str, gen_random_date, gen_random_time, gen_random_date_time,
    gen_random_coordinate, gen_random_num, gen_random_quantity
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


def gen_random_grid(metadata=True):
    # Generate a randomised grid of values and try parsing it back.
    grid = hszinc.Grid(version=VER_3_0)
    if metadata:
        grid.metadata.extend(gen_random_meta())

    # Randomised columns
    for n in range(0, random.randint(1, GENERATION_COLUMN)):
        if "id" not in grid.column and random.randint(0, 100) < PERCENT_GEN_ID:
            col_name = "id"
        else:
            col_name = gen_random_name(existing=grid.column)
        if metadata and random.choice([True, False]):
            grid.column[col_name] = gen_random_meta()
        else:
            grid.column[col_name] = MetadataObject()

    # Randomised rows
    for n in range(0, random.randint(0, GENERATION_ROW)):
        row = {}
        for c in grid.column.keys():
            if "id" == c:
                while True:
                    id_val = gen_random_ref()
                    if id_val not in grid:
                        row["id"] = id_val
                        break
            else:
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
        grid = hszinc.parse(grid_str, mode=mode)
    except:
        print('Failed to parse dumped grid')
        dump_grid(ref_grid)
        print('--- Parsed string ---')
        print(grid_str)
        raise
    assert grid == ref_grid


def try_dump_parse_json():
    ref_grid = gen_random_grid()
    _try_dump_parse(ref_grid, MODE_JSON)


def try_dump_parse_zinc():
    ref_grid = gen_random_grid()
    _try_dump_parse(ref_grid, MODE_ZINC)


def try_dump_parse_json():
    ref_grid = gen_random_grid()
    _try_dump_parse(ref_grid, MODE_JSON)


def try_dump_parse_csv():
    ref_grid = gen_random_grid(metadata=False)
    _try_dump_parse(ref_grid, MODE_CSV)


def test_loopback_zinc():
    for trial in range(0, GENERATION_NUMBER):
        try_dump_parse_zinc()


_FIND_BUG = 1


def test_loopback_json():
    for x in range(0, _FIND_BUG):
        x = 1
        if _FIND_BUG != 1:
            random.seed(x)
        try:
            for trial in range(0, GENERATION_NUMBER):
                try_dump_parse_json()
        except:
            print(x)
            raise


def test_loopback_csv():
    for x in range(0, _FIND_BUG):
        x = 1
        if _FIND_BUG != 1:
            random.seed(x)
        try:
            for trial in range(0, GENERATION_NUMBER):
                try_dump_parse_csv()
        except:
            print(x)
            raise
