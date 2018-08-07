# -*- coding: utf-8 -*-
# Zinc dumping and parsing module
# (C) 2016 VRT Systems
#
# vim: set ts=4 sts=4 et tw=78 sw=4 si:

# If `pint` is not installed or available, skip the relevant tests.
try:
    import pint
    import hszinc
    from hszinc.pintutil import to_pint
    def _enable_pint(pint_en):
        hszinc.use_pint(pint_en)

except ImportError:
    import logging
    logging.warning(
        '`pint` was not available for import.  Tests requiring `pint` will '
        'be skipped.', exc_info=1)

    from nose import SkipTest
    def _enable_pint(pint_en):
        if pint_en:
            raise SkipTest('pint not available')
    def to_pint(*a, **kwa):
        raise SkipTest('pint not available')
