import random
from io import open

from hszinc.pintutil import to_haystack

_RAW_UNIT_DATA = None

def get_units():
    global _RAW_UNIT_DATA
    if _RAW_UNIT_DATA is None:
        unit_data = {}

        for raw_row in open(
                'tests/project_haystack_units.txt',
                mode='r', encoding='utf-8'):
            row = raw_row.split(u',')
            if not bool(row):
                continue
            if row[0].startswith('--'):
                continue

            if len(row) == 1:
                unit_data[row[0]] = row[0]
            else:
                unit_data[row[0]] = row[1]
        _RAW_UNIT_DATA = unit_data
    return _RAW_UNIT_DATA.copy()

def get_random_unit():
    return random.choice(list(get_units().values()))
