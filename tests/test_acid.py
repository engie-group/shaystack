# -*- coding: utf-8 -*-
# Zinc dumping and parsing module
# See the accompanying LICENSE file.
# (C) 2016 VRT Systems
# (C) 2021 Engie Digital
#
# vim: set ts=4 sts=4 et tw=78 sw=4 si:
import binascii
import datetime
import random
import string
import sys
from typing import Optional, Dict, List, Union

from shaystack import HaystackType
# noinspection PyProtectedMember
from shaystack.datatypes import Ref, Bin, Uri, Quantity, Coordinate, XStr, MARKER, REMOVE, NA, MODE_TRIO, MODE, \
    _MarkerType, _RemoveType, _NAType
from shaystack.dumper import dump
from shaystack.grid import Grid, VER_3_0
from shaystack.metadata import MetadataObject
from shaystack.parser import MODE_ZINC, parse, MODE_JSON, MODE_CSV, MODE_HAYSON
# noinspection PyProtectedMember
from shaystack.zoneinfo import _get_tz_map, timezone

STR_CHARSET = string.ascii_letters + string.digits + '\n\r\t\f\b'

# Set GENERATION_NUMBER to 1 and _FIND_BUG_END to N to detect a first random grid with error
# _GENERATION_NUMBER = 1
# _FIND_BUG_START = 1  # 0 for normal use
# _FIND_BUG_END = 30000  # 1 for normal use

_GENERATION_NUMBER = 10
_FIND_BUG_START = 0  # 0 for normal use
_FIND_BUG_END = 1  # 1 for normal use

GENERATION_NUMBER, GENERATION_COLUMN, GENERATION_ROW, PERCENT_GEN_ID, PERCENT_RECURSIVE, PERCENT_AMBIGUOUS = \
    (_GENERATION_NUMBER, 5, 10, 30, 5, 5)


def gen_random_const() -> Union[bool, _MarkerType, _RemoveType, _NAType]:
    return random.choice([True, False, MARKER, REMOVE, NA])  # type: ignore


def gen_random_ref() -> Ref:
    # Generate a randomised reference.
    name = gen_random_str(charset=string.ascii_letters + string.digits + '_:-.~')
    if random.choice([True, False]):
        value = gen_random_str(charset=string.ascii_letters + string.digits + '_')
    else:
        value = None

    return Ref(name, value)


def gen_random_bin() -> Bin:
    # Generate a randomized binary
    return Bin(random.choice([
        'text/plain',
        'text/html',
        'text/zinc',
        'application/json',
        'application/octet-stream',
        'image/png',
        'image/jpeg',
    ]))


def gen_random_xstr() -> XStr:
    # Generate a randomized binary
    b_array = bytearray(random.getrandbits(8) for _ in range(5))
    return XStr(*random.choice([  # type: ignore
        ('hex', binascii.hexlify(b_array).decode('ascii')),
        ('b64', binascii.b2a_base64(b_array)[:-1] if sys.version_info[0] <= 2
        else binascii.b2a_base64(b_array).decode("ascii")  # noqa: E128
         )
    ]))


def gen_random_uri() -> Uri:
    return Uri(gen_random_str(charset=string.ascii_letters + string.digits))


_ambiguous_str = ["T", "F", "NA", "N", "M", "R"]


def gen_random_str(min_length=1, max_length=20, charset=STR_CHARSET) -> str:
    # Generate a random 20-character string
    """
    Args:
        min_length:
        max_length:
        charset:
    """
    if random.randint(0, 100) < PERCENT_AMBIGUOUS:
        return _ambiguous_str[random.randint(0, len(_ambiguous_str) - 1)]
    while True:
        v = ''.join([random.choice(charset)
                     for _ in range(0, random.randint(min_length, max_length))])
        if v and v[0].isdigit():  # Refuse the confusion with quantity
            v = 'D' + v
        break
    return v


def gen_random_date() -> datetime.date:
    # This might generate an invalid date, we keep trying until we get one.
    while True:
        try:
            return datetime.date(random.randint(1, 3000),
                                 random.randint(1, 12), random.randint(1, 28))
        except OverflowError:
            pass


def gen_random_time() -> datetime.time:
    return datetime.time(random.randint(0, 23), random.randint(0, 59),
                         random.randint(0, 59), random.randint(0, 999999))


def gen_random_date_time() -> datetime.datetime:
    # Pick a random timezone
    tz_name = random.choice(list(_get_tz_map().keys()))
    time_zone = timezone(tz_name)
    while True:
        try:
            return time_zone.localize(datetime.datetime.combine(
                gen_random_date(), gen_random_time()))
        except OverflowError:
            pass


def gen_random_coordinate() -> Coordinate:
    return Coordinate(
        round(gen_random_num(360) - 180.0, 2),
        round(gen_random_num(360) - 180.0, 2))


def gen_random_num(scale=1000, digits=2) -> float:
    """
    Args:
        scale:
        digits:
    """
    return round(random.random() * scale, digits)


def gen_random_quantity() -> Quantity:
    return Quantity(gen_random_num(), 'degree')


def gen_random_list() -> List[HaystackType]:
    return [gen_random_scalar() for _ in range(0, random.randint(0, 2))]


def gen_random_map() -> Dict[str, HaystackType]:
    return {gen_random_name(): gen_random_scalar() for _ in range(0, random.randint(0, 2))}


RANDOM_TYPES = [
    # Only for v2.0 gen_random_bin,
    gen_random_xstr,
    gen_random_const, gen_random_ref, gen_random_uri, gen_random_xstr,
    gen_random_str,
    gen_random_date, gen_random_time, gen_random_date_time,
    gen_random_coordinate, gen_random_num, gen_random_quantity
]


def gen_random_scalar() -> HaystackType:
    if random.randint(0, 100) < PERCENT_RECURSIVE:
        return random.choice(RANDOM_RECURSIVE_TYPES)()  # type: ignore
    return random.choice(RANDOM_TYPES)()  # type: ignore


def gen_random_name(existing: Optional[Dict] = None) -> str:
    """
    Args:
        existing: Previously names
    """
    while True:
        meta = random.choice(string.ascii_lowercase) + \
               gen_random_str(min_length=0, max_length=7,
                              charset=string.ascii_letters + string.digits)
        if (existing is None) or (meta not in existing):
            return meta


def gen_random_meta() -> MetadataObject:
    meta = MetadataObject()
    for _ in range(0, random.randint(1, 5)):
        name = gen_random_name()
        value = gen_random_scalar()
        if name != "ver":
            meta[name] = value
    return meta


def gen_random_grid(metadata: bool = True, minrow: int = 0, empty_col: bool = True) -> Grid:
    # Generate a randomised grid of values and try parsing it back.
    """
    Args:
        metadata: With metadata ?
        minrow: Minimum number of rows
        empty_col: Accept empty column ?
    """
    grid = Grid(version=VER_3_0)
    if metadata:
        grid.metadata.extend(gen_random_meta())

    # Randomised columns
    for _ in range(0, random.randint(1, GENERATION_COLUMN)):
        if "id" not in grid.column and random.randint(0, 100) < PERCENT_GEN_ID:
            col_name = "id"
        else:
            col_name = gen_random_name(existing=grid.column)  # type: ignore
        if metadata and random.choice([True, False]):
            grid.column[col_name] = gen_random_meta()
        else:
            grid.column[col_name] = MetadataObject()

    # Randomised rows
    for _ in range(0, random.randint(minrow, GENERATION_ROW)):  # pylint: disable=too-many-nested-blocks
        row = {}
        while True:
            for col in grid.column.keys():
                if col == "id":
                    while True:
                        id_val = gen_random_ref()
                        if id_val not in grid:
                            row["id"] = id_val
                            break
                else:
                    if not empty_col or random.choice([True, False]):
                        row[col] = gen_random_scalar()  # type: ignore
            if not minrow or len(row):
                break
        grid.append(row)

    return grid


RANDOM_RECURSIVE_TYPES = [gen_random_list, gen_random_map, gen_random_grid]


def dump_grid(grid: Grid):
    """
    Args:
        grid:
    """
    print('Version: %s' % grid.version)
    print('Metadata:')
    for k, val in grid.metadata.items():
        print('   %s = %r' % (k, val))
    print('Columns:')
    for key, _ in grid.column.items():
        print('   %s:' % key)
        for k, val in grid.column[key].items():
            print('      %s = %r' % (k, val))
    print('Rows:')
    for row in grid:
        print('---')
        for key, val in row.items():
            print('  %s = %r' % (key, val))


def _try_dump_parse(ref_grid: Grid, mode: MODE):
    """
    Args:
        ref_grid:
        mode:
    """
    try:
        # Dump the randomised grid to a string
        grid_str = dump(ref_grid, mode=mode)
    except:  # noqa: E722
        # Dump some detail about the grid
        print('Failed to dump grid.')
        dump_grid(ref_grid)
        raise

    # Parse the grid string
    try:
        grid = parse(grid_str, mode=mode)
    except:  # noqa: E722
        print('Failed to parse dumped grid')
        dump_grid(ref_grid)
        print('--- Parsed string ---')
        print(grid_str)
        raise
    assert grid == ref_grid


def try_dump_parse_zinc():
    ref_grid = gen_random_grid()
    _try_dump_parse(ref_grid, MODE_ZINC)


def try_dump_parse_trio():
    ref_grid = gen_random_grid(metadata=False, minrow=1, empty_col=False)
    _try_dump_parse(ref_grid, MODE_TRIO)


def try_dump_parse_json():
    ref_grid = gen_random_grid()
    _try_dump_parse(ref_grid, MODE_JSON)


def try_dump_parse_hayson():
    ref_grid = gen_random_grid()
    _try_dump_parse(ref_grid, MODE_HAYSON)


def try_dump_parse_csv():
    ref_grid = gen_random_grid(metadata=False)
    _try_dump_parse(ref_grid, MODE_CSV)


def test_loopback_zinc():
    for i in range(_FIND_BUG_START, _FIND_BUG_END):
        if _FIND_BUG_END != 1:
            random.seed(i)
        try:
            for _ in range(0, GENERATION_NUMBER):
                try_dump_parse_zinc()
        except:  # noqa: E722
            print(i)
            raise


def test_loopback_trio():
    for i in range(_FIND_BUG_START, _FIND_BUG_END):
        if _FIND_BUG_END != 1:
            random.seed(i)
        try:
            for _ in range(0, GENERATION_NUMBER):
                try_dump_parse_trio()
        except:  # noqa: E722
            print(i)
            raise


def test_loopback_json():
    for i in range(_FIND_BUG_START, _FIND_BUG_END):
        if _FIND_BUG_END != 1:
            random.seed(i)
        try:
            for _ in range(0, GENERATION_NUMBER):
                try_dump_parse_json()
        except:  # noqa: E722
            print(i)
            raise


def test_loopback_hayson():
    for i in range(_FIND_BUG_START, _FIND_BUG_END):
        if _FIND_BUG_END != 1:
            random.seed(i)
        try:
            for _ in range(0, GENERATION_NUMBER):
                try_dump_parse_hayson()
        except:  # noqa: E722
            print(i)
            raise


def test_loopback_csv():
    for i in range(_FIND_BUG_START, _FIND_BUG_END):
        if _FIND_BUG_END != 1:
            random.seed(i)
        try:
            for _ in range(0, GENERATION_NUMBER):
                try_dump_parse_csv()
        except:  # noqa: E722
            print(i)
            raise
