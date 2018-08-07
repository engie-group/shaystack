try:
    import pint
    def _enable_pint(pint_en):
        hszinc.use_pint(pint_en)

except ImportError:
    import logging
    logging.warning(
        '`pint` was not available for import.  Tests requiring `pint` will '
        'be skipped.', exc_info=1)

    from nose import SkipTest
    def _enable_pint(pint_en):
        raise SkipTest('pint not available')

import hszinc
import pkg_resources, os

units = []

def get_units():
    _enable_pint(True)
    file_path = os.path.join('', 'project_haystack_units.txt')
    units_file = pkg_resources.resource_string(__name__, file_path)
    global units
    with open(units_file, 'r', encoding = 'UTF-8') as file:
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
    not_defined = []
    defined = []
    for each in units:
        try:   
            q = hszinc.Q_(1,each)
            defined.append(each)
            print(each, q)
        except Exception as error:
            not_defined.append(each)
            print(error, each)
    assert (len(not_defined)) == 0
