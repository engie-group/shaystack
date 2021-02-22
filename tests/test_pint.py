import importlib.resources as pkg_resources

import shaystack


def _load_haystack_units():
    haystack_unit = []
    with pkg_resources.open_text(__package__,
                                 'project_haystack_std_units.txt', encoding='UTF-8') as file:
        for line in file:
            if '--' not in line and line != '':
                if line.startswith("#"):
                    continue
                canonical, *alias = line.rstrip().split(',')
                if not alias:
                    haystack_unit.append((canonical, [canonical]))
                else:
                    haystack_unit.append((canonical, alias))
    assert len(haystack_unit) > 0
    return haystack_unit


def test_all_units():
    haystack_unit = _load_haystack_units()
    not_defined = []
    for _, alias in haystack_unit:
        for symbol in alias:
            try:
                shaystack.Quantity(1, symbol)  # Try to convert
            except Exception as error:  # pylint: disable=broad-except
                not_defined.append(symbol)
                print("***", error, symbol)
    assert (len(not_defined)) == 0
