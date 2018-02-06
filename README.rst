HSZinc
======

.. image:: https://travis-ci.org/vrtsystems/hszinc.svg?branch=master
    :target: https://travis-ci.org/vrtsystems/hszinc
.. image:: https://coveralls.io/repos/vrtsystems/hszinc/badge.svg?branch=master&service=github
    :target: https://coveralls.io/github/vrtsystems/hszinc?branch=master

HSZinc is an implementation of the `ZINC`_ grid serialisation format used in
`Project Haystack`_.  Additionally, the module implements code for parsing and
dumping grids in the JSON format.

The aim of this project is to provide a simple Python module that allows easy
manipulation of Project Haystack grids in both ZINC and JSON formats.

REQUIREMENTS
============

- `pyparsing`_
- `pytz`_
- `iso8601`_
- `six`_

TYPICAL USAGE
=============

Making a grid
-------------

::

  Python 2.7.10 (default, Dec 26 2015, 09:36:51)
  Type "copyright", "credits" or "license" for more information.

  IPython 2.2.0 -- An enhanced Interactive Python.
  ?         -> Introduction and overview of IPython's features.
  %quickref -> Quick reference.
  help      -> Python's own help system.
  object?   -> Details about 'object', use 'object??' for extra details.

  In [1]: import hszinc

  In [2]: import datetime

  In [3]: g = hszinc.Grid()

  In [4]: g.metadata['aMarker'] = hszinc.MARKER

  In [5]: g.metadata['today'] = datetime.date.today()

  In [6]: g.column['firstColumn'] = {'metaData':'in no particular order', 'abc': 123}

  In [7]: g.column['secondColumn'] = {}

  In [8]: g.extend([
    {'firstColumn': hszinc.Quantity(154, 'commits'), 'secondColumn': 'and counting'},
    {'firstColumn': hszinc.MARKER, 'secondColumn': 'supported on Python 2.7 and 3.x'},
    {'firstColumn': hszinc.Coordinate(-27.4725,153.003), 'secondColumn': 'Made in Australia from local and imported ingredients'},
  ])

  In [9]: print hszinc.dump(g)
  ver:"2.0" aMarker today:2016-01-18
  firstColumn abc:123 metaData:"in no particular order",secondColumn
  154commits,"and counting"
  M,"supported on Python 2.7 and 3.x"
  C(-27.472500,153.003000),"Made in Australia from local and imported ingredients"


  In [10]: print hszinc.dump(g, mode=hszinc.MODE_JSON)
  {"rows": [{"secondColumn": "s:and counting", "firstColumn": "n:154.000000 commits"}, {"secondColumn": "s:supported on Python 2.7 and 3.x", "firstColumn": "m:"}, {"secondColumn": "s:Made in Australia from local and imported ingredients", "firstColumn": "c:-27.472500,153.003000"}], "meta": {"ver": "2.0", "aMarker": "m:", "today": "d:2016-01-18"}, "cols": [{"abc": "n:123.000000", "name": "firstColumn", "metaData": "s:in no particular order"}, {"name": "secondColumn"}]}

Parsing a grid in ZINC format
-----------------------------

`parse` returns a list of grids found in the input text.  Since there can be
more than one grid in a block of text, we process all grids found and return
a list.

::

  Python 2.7.10 (default, Dec 26 2015, 09:36:51)
  Type "copyright", "credits" or "license" for more information.

  IPython 2.2.0 -- An enhanced Interactive Python.
  ?         -> Introduction and overview of IPython's features.
  %quickref -> Quick reference.
  help      -> Python's own help system.
  object?   -> Details about 'object', use 'object??' for extra details.

  In [1]: import hszinc

  In [2]: grids = hszinc.parse('''ver:"2.0" database:"test" dis:"Site Energy Summary"
  siteName dis:"Sites", val dis:"Value" unit:"kW"
  "Site 1", 356.214kW
  "Site 2", 463.028kW''')

  In [3]: grids
  Out[3]: [<hszinc.grid.Grid at 0x7fb9eb7ee990>]

  In [4]: g = grids.pop(0)

  In [5]: g.metadata
  Out[5]: MetadataObject{'database'=u'test', 'dis'=u'Site Energy Summary'}

  In [6]: g.column
  Out[6]: SortableDict{'siteName'=MetadataObject{'dis'=u'Sites'}, 'val'=MetadataObject{'dis'=u'Value', 'unit'=u'kW'}}

  In [7]: g[:]
  Out[7]:
  [{'siteName': u'Site 1', 'val': Quantity(356.214, 'kW')},
   {'siteName': u'Site 2', 'val': Quantity(463.028, 'kW')}]

Parsing a grid in JSON format
-----------------------------

The Project Haystack site only defines how individual grids are handled, and
when given a single grid, we return just that grid.  Otherwise if multiple grids
are placed in a JSON array, they will be returned as a list:

::

  In [1]: import hszinc

  In [2]: grids = hszinc.parse('''{
    "meta": {"ver":"2.0", "projName":"test"},
    "cols":[
      {"name":"dis", "dis":"Equip Name"},
      {"name":"equip"},
      {"name":"siteRef"},
      {"name":"installed"}
    ],
    "rows":[
      {"dis":"RTU-1", "equip":"m:", "siteRef":"r:153c-699a HQ", "installed":"d:2005-06-01"},
      {"dis":"RTU-2", "equip":"m:", "siteRef":"r:153c-699a HQ", "installed":"d:999-07-12"}
    ]
  }''', mode=hszinc.MODE_JSON)

  In [3]: grids
  Out[3]: <hszinc.grid.Grid at 0x7f2ce556f990>

  In [4]: grids.metadata
  Out[4]: MetadataObject{u'projName'=u'test'}

  In [5]: grids.column
  Out[5]: SortableDict{u'dis'={u'dis': u'Equip Name'}, u'equip'={}, u'siteRef'={}, u'installed'={}}

  In [6]: grids[:]
  Out[6]:
  [{u'dis': u'RTU-1',
    u'equip': MARKER,
    u'installed': datetime.date(2005, 6, 1),
    u'siteRef': Ref(u'153c-699a', u'HQ', True)},
   {u'dis': u'RTU-2',
    u'equip': MARKER,
    u'installed': u'd:999-07-12',
    u'siteRef': Ref(u'153c-699a', u'HQ', True)}]

Working with grids
------------------

The grid itself behaves like a `list` containing `dict` objects, one per row.
The usual insert/append/extend methods as well as the `del`, `len` and `[]`
operators work the way the ones in `list` do.  Iterating over the grid iterates
over its rows.

Grid metadata is represented by the `MetadataObject` class, a subclass of
`SortableDict`.  `SortableDict` behaves like a regular `dict`, except that it
maintains the order of keys.  New values can be `insert`-ed at any point in the
`SortableDict`, or the entire set of keys may be `sort()`-ed or `reverse()`-d
in-place.  `MetadataObject` supports appending and insertion of strings, which
get stored as `MARKER` objects to create markers.

Data types
----------

`hszinc` converts the common Python data types:

Null, Boolean, Date, Time, Date/Time and strings.
  Standard Python types.  In the case of Date/Time, the `tzinfo` parameter is
  set to the equivalent timezone provided by the `pytz` library where possible.

Numbers
  Numbers without a unit are represented as `float` objects.
  Numbers with a unit are represented by the `hszinc.Quantity` custom type which
  has two attributes: `value` and `unit`.

Marker and Remove
  These are singletons, represented by `hszinc.MARKER` and `hszinc.REMOVE`.
  They behave and are intended to be used like the `None` object.

URI and Bin
  These are represented as subclasses of `unicode` type (Python 2.7; `str` in
  Python 3.x).

Ref
  Represented by the custom type `hszinc.Ref` which has `name` (`str`),
  `has_value` (`bool`) and `value` (any type) attributes.

Coord
  Represented by the custom type `hszinc.Coordinate`, which has `latitude` and
  `longitude` types (both `float`)

STATUS
======

This is early days, absolutely nothing is guaranteed.

.. _`Project Haystack`: http://www.project-haystack.org/
.. _`ZINC`: http://project-haystack.org/doc/Zinc
.. _`pyparsing`: https://pypi.python.org/pypi/pyparsing/
.. _`pytz`: http://pytz.sourceforge.net/
.. _`iso8601`: http://pyiso8601.readthedocs.org/en/latest/
.. _`six`: https://pythonhosted.org/six/
