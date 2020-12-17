import importlib.resources as pkg_resources

from pint import UndefinedUnitError

import haystackapi

units = []


def get_units():
    with pkg_resources.open_text(__package__,
                                 'project_haystack_units.txt', encoding='UTF-8') as file:
        for line in file:
            if '--' not in line and line != '':
                res = line.rstrip().split(',')
                if res[0] != '':
                    units.append(res[0])
                if len(res) > 1:
                    units.append(res[1])
    assert len(units) > 0


def test_all_units():
    get_units()
    not_defined = []
    defined = []
    for each in units:
        try:
            # if to_haystack(each) != each:
            #     assert to_pint(to_haystack(each)) == each
            haystackapi.Quantity(1, each)
            defined.append(each)
        except UndefinedUnitError as error:
            not_defined.append(each)
            print(error, each)
    assert (len(not_defined)) == 0
