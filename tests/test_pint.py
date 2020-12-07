from pint import UndefinedUnitError

try:
    import importlib.resources as pkg_resources
except ImportError:
    # Try backported to PY<37 `importlib_resources`.
    import importlib_resources as pkg_resources

import haystackapi

from .pint_enable import _enable_pint

units = []


def get_units():
    _enable_pint(True)
    with pkg_resources.open_text(__package__, 'project_haystack_units.txt', encoding='UTF-8') as file:
        for line in file:
            if '--' not in line and line != '':
                res = line.rstrip().split(',')
                if res[0] != '':
                    units.append(res[0])
                if len(res) > 1:
                    units.append(res[1])
    assert len(units) > 0


def test_all_units():
    _enable_pint(True)
    get_units()
    not_defined = []
    defined = []
    for each in units:
        try:
            # if to_haystack(each) != each:
            #     assert to_pint(to_haystack(each)) == each
            quantity = haystackapi.Quantity(1, each)
            defined.append(each)
            print(each, quantity)
        except UndefinedUnitError as error:
            not_defined.append(each)
            print(error, each)
    assert (len(not_defined)) == 0
