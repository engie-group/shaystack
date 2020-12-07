HSZinc
======

.. image:: https://travis-ci.org/widesky/hszinc.svg?branch=master
    :target: https://travis-ci.org/widesky/hszinc
.. image:: https://coveralls.io/repos/widesky/hszinc/badge.svg?branch=master&service=github
    :target: https://coveralls.io/github/widesky/hszinc?branch=master

HSZinc is an implementation of the `ZINC`_ grid serialisation format used in
`Project Haystack`_.  Additionally, the module implements code for parsing and
dumping grids in the JSON and CSV format.

The aim of this project is to provide a simple Python module that allows easy
manipulation of Project Haystack grids in both ZINC, JSON and CSV formats.

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

    Python 3.6.9 (?, Apr 10 2020, 19:47:05)
    Type 'copyright', 'credits' or 'license' for more information
    IPython 7.16.1 -- An enhanced Interactive Python. Type '?' for help.

    In [1]: import hszinc

    In [2]: import datetime

    In [3]: grid = hszinc.Grid()

    In [4]: grid.metadata['aMarker'] = hszinc.MARKER

    In [5]: grid.metadata['today'] = datetime.date.today()

    In [6]: grid.column['firstColumn'] = {'metaData':'in no particular order', 'abc': 123}

    In [7]: grid.column['secondColumn'] = {}

    In [8]: grid.extend([
       ...: {'firstColumn': hszinc.Quantity(154, 'commits'), 'secondColumn': 'and counting'},
       ...: {'firstColumn': hszinc.MARKER, 'secondColumn': 'supported on Python 2.7 and 3.x'},
       ...: {'firstColumn': hszinc.Coordinate(-27.4725,153.003), 'secondColumn': 'Made in Australia from local and imported ingredients'},
       ...: ])

    In [9]: print(hszinc.dump(grid))
    ver:"2.0" aMarker today:2020-09-09
    firstColumn metaData:"in no particular order" abc:123,secondColumn
    154commits,"and counting"
    M,"supported on Python 2.7 and 3.x"
    C(-27.472500,153.003000),"Made in Australia from local and imported ingredients"


    In [10]: print(hszinc.dump(grid, mode=hszinc.MODE_JSON))
    {"meta": {"aMarker": "m:", "today": "d:2020-09-09", "ver": "2.0"}, "cols": [{"metaData": "s:in no particular order", "abc": "n:123.000000", "name": "firstColumn"}, {"name": "secondColumn"}], "rows": [{"firstColumn": "n:154.000000 commits", "secondColumn": "s:and counting"}, {"firstColumn": "m:", "secondColumn": "s:supported on Python 2.7 and 3.x"}, {"firstColumn": "c:-27.472500,153.003000", "secondColumn": "s:Made in Australia from local and imported ingredients"}]}

    In [11]: print(hszinc.dump(grid, mode=hszinc.MODE_CSV))
    firstColumn,secondColumn
    154commits,"and counting"
    ✓,"supported on Python 2.7 and 3.x"
    "C(-27.472500,153.003000)","Made in Australia from local and imported ingredients"

Parsing a grid in ZINC format
-----------------------------

`parse` returns a list of grids found in the input text.  Since there can be
more than one grid in a block of text, we process all grids found and return
a list.

::

    Python 3.6.9 (?, Apr 10 2020, 19:47:05)
    Type 'copyright', 'credits' or 'license' for more information
    IPython 7.16.1 -- An enhanced Interactive Python. Type '?' for help.

    In [1]: import hszinc

    In [2]: grid = hszinc.parse('''ver:"3.0" database:"test" dis:"Site Energy Summary"
       ...: id dis:"Id" siteName dis:"Sites", val dis:"Value" unit:"kW"
       ...: "site1", "Site 1", 356.214kW
       ...: "site2", "Site 2", 463.028kW
       ...: ''')

    In [3]: grid
    Out[3]:
    <Grid>
            Version: 3.0
            Metadata: MetadataObject{'database'='test', 'dis'='Site Energy Summary'}
            Columns:
                    id: MetadataObject{'dis'='Sites', 'siteName'=MARKER}
                    val: MetadataObject{'dis'='Value', 'unit'='kW'}
            Row    0:
            id='site1'
            val='Site 1'
            Row    1:
            id='site2'
            val='Site 2'
    </Grid>

    In [4]: grid.metadata
    Out[4]: MetadataObject{'database'='test', 'dis'='Site Energy Summary'}

    In [5]: grid.column
    Out[5]: SortableDict{'id'=MetadataObject{'dis'='Sites', 'siteName'=MARKER}, 'val'=MetadataObject{'dis'='Value', 'unit'='kW'}}

    In [6]: grid[0]
    Out[6]: {'id': 'site1', 'val': 'Site 1'}

    In [7]: grid["site2"]
    Out[7]: {'id': 'site2', 'val': 'Site 2'}

Parsing a grid in JSON format
-----------------------------

The Project Haystack site only defines how individual grids are handled, and
when given a single grid, we return just that grid.

::
    Python 3.6.9 (?, Apr 10 2020, 19:47:05)
    Type 'copyright', 'credits' or 'license' for more information
    IPython 7.16.1 -- An enhanced Interactive Python. Type '?' for help.

    In [1]: import hszinc

    In [2]: grid = hszinc.parse('''{
       ...: "meta": {"ver":"2.0", "projName":"test"},
       ...: "cols":[
       ...: {"name":"id", "dis":"Uniq id"},
       ...: {"name":"dis", "dis":"Equip Name"},
       ...: {"name":"equip"},
       ...: {"name":"siteRef"},
       ...: {"name":"installed"}
       ...: ],
       ...: "rows":[
       ...: {"id":"eq1","dis":"RTU-1", "equip":"m:", "siteRef":"r:153c-699a HQ", "installed":"d:2005-06-01"},
       ...: {"id":"eq2","dis":"RTU-2", "equip":"m:", "siteRef":"r:153c-699a HQ", "installed":"d:999-07-12"}
       ...: ]
       ...: }''', mode=hszinc.MODE_JSON)

    In [3]: grid
    Out[3]:
    <Grid>
            Version: 2.0
            Metadata: MetadataObject{'projName'='test'}
            Columns:
                    id: {'dis': 'Uniq id'}
                    dis: {'dis': 'Equip Name'}
                    equip
                    siteRef
                    installed
            Row    0:
            id='eq1'
            dis='RTU-1'
            equip=MARKER
            siteRef=Ref('153c-699a', 'HQ', True)
            installed=datetime.date(2005, 6, 1)
            Row    1:
            id='eq2'
            dis='RTU-2'
            equip=MARKER
            siteRef=Ref('153c-699a', 'HQ', True)
            installed='d:999-07-12'
    </Grid>

    In [4]: grid.metadata
    Out[4]: MetadataObject{'projName'='test'}

    In [5]: grid.column
    Out[5]: SortableDict{'id'={'dis': 'Uniq id'}, 'dis'={'dis': 'Equip Name'}, 'equip'={}, 'siteRef'={}, 'installed'={}}

    In [6]: grid[0]
    Out[6]:
    {'id': 'eq1',
     'dis': 'RTU-1',
     'equip': MARKER,
     'siteRef': Ref('153c-699a', 'HQ', True),
     'installed': datetime.date(2005, 6, 1)}

    In [7]: grid["eq1"]
    Out[7]:
    {'id': 'eq1',
     'dis': 'RTU-1',
     'equip': MARKER,
     'siteRef': Ref('153c-699a', 'HQ', True),
     'installed': datetime.date(2005, 6, 1)}


Parsing a grid in CSV format
-----------------------------

:
    Python 3.6.9 (?, Apr 10 2020, 19:47:05)
    Type 'copyright', 'credits' or 'license' for more information
    IPython 7.16.1 -- An enhanced Interactive Python. Type '?' for help.

    In [1]: import hszinc

    In [2]: grid = hszinc.parse('''id,firstName,bday
       ...: "user1","Jack",1973-07-23
       ...: "user2","Jill",1975-11-15
       ...: ''',mode=hszinc.MODE_CSV)

    In [3]: grid
    Out[3]:
    <Grid>
            Version: 3.0
            Columns:
                    id
                    firstName
                    bday
            Row    0:
            id='user1'
            firstName='Jack'
            bday=datetime.date(1973, 7, 23)
            Row    1:
            id='user2'
            firstName='Jill'
            bday=datetime.date(1975, 11, 15)
    </Grid>

    In [4]: grid.metadata
    Out[4]: MetadataObject{}

    In [5]: grid.column
    Out[5]: SortableDict{'id'=MetadataObject{}, 'firstName'=MetadataObject{}, 'bday'=MetadataObject{}}

    In [6]: grid[0]
    Out[6]: {'id': 'user1', 'firstName': 'Jack', 'bday': datetime.date(1973, 7, 23)}

    In [7]: grid["user2"]
    Out[7]: {'id': 'user2', 'firstName': 'Jill', 'bday': datetime.date(1975, 11, 15)}



Working with grids
------------------

The grid itself behaves like a `list` containing `dict` objects, one per row.
The usual insert/append/extend methods as well as the `del`, `len` and `[]`
operators work the way the ones in `list` do.  Iterating over the grid iterates
over its rows.

The grid propose a direct access to row with 'id' (grid["key"], "key" in grid, del grid["key"], ...)

Grid metadata is represented by the `MetadataObject` class, a subclass of
`SortableDict`.  `SortableDict` behaves like a regular `dict`, except that it
maintains the order of keys.  New values can be `insert`-ed at any point in the
`SortableDict`, or the entire set of keys may be `sort()`-ed or `reverse()`-d
in-place.  `MetadataObject` supports appending and insertion of strings, which
get stored as `MARKER` objects to create markers.

Grids can be compare. The resulting grid can be merge with another grid.
Use the operator minus and plus.
At all time, grid_a + (grid_b - grid_a) == grid_b

Data types
----------

`hszinc` converts the common Python data types:

Null, Boolean, Date, Time, Date/Time and strings.
  Standard Python types.  In the case of Date/Time, the `tzinfo` parameter is
  set to the equivalent timezone provided by the `pytz` library where possible.

Numbers
  Numbers without a unit are represented as `float` objects.
  Numbers with a unit are represented by the `hszinc.Quantity` custom type which
  has two attributes: `value` and `unit`.  If `pint` is installed, support exists
  for its unit conversion features.

NA, Marker and Remove
  These are singletons, represented by `hszinc.NA`, `hszinc.MARKER` and
  `hszinc.REMOVE`.  They behave and are intended to be used like the `None` object.

URI and Bin
  These are represented as subclasses of `unicode` type (Python 2.7; `str` in
  Python 3.x).

XBin
    This is represented as a bytearray, with the corresponding encoding (hex, b64)

Ref
  Represented by the custom type `hszinc.Ref` which has `name` (`str`),
  `has_value` (`bool`) and `value` (any type) attributes.

Coord
  Represented by the custom type `hszinc.Coordinate`, which has `latitude` and
  `longitude` types (both `float`)

Lists, Maps
  Represented using standard Python `list` or `dict` objects.

Grid
  A grid can be inside another grid

STATUS
======

`hszinc` has been used to implement the core grid parsing logic in `pyhaystack`
and used in production for some time now.  Project Haystack 2.0 and 3.0 compatibility
is pretty good at this time.

.. _`Project Haystack`: http://www.project-haystack.org/
.. _`ZINC`: http://project-haystack.org/doc/Zinc
.. _`JSON`: https://project-haystack.org/doc/Json
.. _`CSV`: https://project-haystack.org/doc/Csv
.. _`pyparsing`: https://pypi.python.org/pypi/pyparsing/
.. _`pytz`: http://pytz.sourceforge.net/
.. _`iso8601`: http://pyiso8601.readthedocs.org/en/latest/
.. _`six`: https://pythonhosted.org/six/
