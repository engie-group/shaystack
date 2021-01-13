import importlib.resources as pkg_resources
import random

_RAW_UNIT_DATA = None


def get_units():
    global _RAW_UNIT_DATA  # pylint: disable=global-statement
    if _RAW_UNIT_DATA is None:
        unit_data = {}

        for raw_row in pkg_resources.open_text(__package__,
                                               'project_haystack_units.txt', encoding='UTF-8'):
            row = raw_row.split(',')
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
