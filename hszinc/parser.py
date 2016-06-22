#!/usr/bin/python
# -*- coding: utf-8 -*-
# Zinc Grid Metadata
# (C) 2016 VRT Systems
#
# vim: set ts=4 sts=4 et tw=78 sw=4 si:

from .grid import Grid
from .metadata import MetadataObject
from .grammar import zinc_grammar
from .sortabledict import SortableDict
from .datatypes import Quantity, Coordinate, Ref, Bin, Uri, \
        MARKER, REMOVE, STR_SUB
from .zoneinfo import timezone
import datetime
import iso8601
import re
import six
import functools
import json
import copy

URI_META = re.compile(r'\\([:/\?#\[\]@\\&=;"$`])')
GRID_SEP = re.compile(r'\n\n+')

MODE_ZINC = 'zinc'
MODE_JSON = 'json'

# Type regular expressions
MARKER_STR  = 'm:'
NUMBER_RE   = re.compile(r'^n:(-?\d+(:?\.\d+)?(:?[eE][+\-]?\d+)?)(:? (.*))?$')
REF_RE      = re.compile(r'^r:([a-zA-Z0-9_:\-.~]+)(:? (.*))?$')
STR_RE      = re.compile(r'^s:(.*)$')
DATE_RE     = re.compile(r'^d:(\d{4})-(\d{2})-(\d{2})$')
TIME_RE     = re.compile(r'^h:(\d{2}):(\d{2})(:?:(\d{2}(:?\.\d+)?))?$')
DATETIME_RE = re.compile(r'^t:(\d{4}-\d{2}-\d{2}T'\
        r'\d{2}:\d{2}(:?:\d{2}(:?\.\d+)?)'\
        r'(:?[zZ]|[+\-]\d+:?\d*))(:? ([A-Za-z\-+_0-9]+))?$')
URI_RE      = re.compile(r'u:(.+)$')
BIN_RE      = re.compile(r'b:(.+)$')
COORD_RE    = re.compile(r'c:(-?\d*\.?\d*),(-?\d*\.?\d*)$')

STR_ESC_RE  = re.compile(r'\\([bfnrt"\\$]|u[0-9a-fA-F]{4})')

def parse(grid_str, mode=MODE_ZINC):
    '''
    Parse the given Zinc text and return the equivalent data.
    '''
    # Split the separate grids up, the grammar definition has trouble splitting
    # them up normally.  This will truncate the newline off the end of the last
    # row.
    _parse = functools.partial(parse_grid, mode=mode)
    if mode == MODE_JSON:
        if isinstance(grid_str, six.string_types):
            grid_data = json.loads(grid_str)
        else:
            grid_data = grid_str
        if isinstance(grid_data, dict):
            return _parse(grid_data)
        else:
            return list(map(_parse, grid_data))
    else:
        return list(map(_parse, GRID_SEP.split(grid_str.rstrip())))

def parse_grid(grid_str, mode=MODE_ZINC):
    if mode == MODE_ZINC:
        if not grid_str.endswith('\n'):
            grid_str += '\n'

        parsed = zinc_grammar.parse(grid_str)
        assert len(parsed.children) == 3

        # First child is metadata
        meta = parsed.children[0]
        assert meta.expr_name == 'gridMeta'

        # We expect the version string next
        assert meta.children[0].expr_name == 'ver'
        version = parse_str(meta.children[0].children[1])

        # The metadata should be in a nameless node.  Parse the children.
        if bool(meta.children[1].children):
            meta_items = parse_meta(meta.children[1].children[0])
        else:
            # No metadata
            meta_items = MetadataObject()

        # The last thing in the list should be a newline
        assert meta.children[2].expr_name == 'nl'

        # The next item should be the columns
        columns = parse_columns(parsed.children[1])

        # This is enough to construct the base grid.
        grid = Grid(version=version, metadata=meta_items, columns=columns)

        # Now to parse the rows
        if bool(columns):
            parse_rows(grid, parsed.children[2])
    elif mode == MODE_JSON:
        # Grab the metadata
        if isinstance(grid_str, six.string_types):
            parsed = json.loads(grid_str)
        else:
            parsed = copy.deepcopy(grid_str)
        meta = parsed.pop('meta')
        version = meta.pop('ver')

        # Parse the remaining elements
        metadata = {}
        for name, value in meta.items():
            metadata[name] = parse_scalar(value, mode=mode)

        grid = Grid(version=version, metadata=metadata)

        # Grab the columns in the order given
        for col in parsed.pop('cols'):
            name = col.pop('name')
            meta = {}
            for key, value in col.items():
                meta[key] = parse_scalar(value, mode=mode)
            grid.column[name] = meta

        # Parse the rows
        for row in (parsed.pop('rows',[]) or []):
            parsed_row = {}
            for col, value in row.items():
                parsed_row[col] = parse_scalar(value, mode=mode)
            grid.append(parsed_row)
    else: # pragma: no cover
        raise NotImplementedError('Format not implemented: %s' % mode)

    return grid

def parse_meta(meta):
    assert meta.expr_name == 'meta'
    items = MetadataObject()

    for item_parent in meta.children:
        # There'll probably be a space beforehand
        for node in item_parent.children:
            if node.expr_name == 'metaItem':
                (item_id, item_value) = parse_meta_item(node)
                items[item_id] = item_value
                break
    return items

def parse_meta_item(item):
    # This could be an 'id' or a 'metaPair'
    assert len(item.children) == 1
    item_child = item.children[0]
    if item_child.expr_name == 'id':
        # This is a marker
        return (parse_id(item_child), MARKER)
    elif item_child.expr_name == 'metaPair':
        # This is a metadata pair
        assert len(item_child.children) == 4
        item_id = parse_id(item_child.children[0])
        item_value = parse_scalar(item_child.children[-1])
        return (item_id, item_value)
    else: # pragma: no cover
        raise NotImplementedError('Unhandled case: %s' \
                % item_child.prettily())

def parse_columns(cols):
    assert cols.expr_name == 'cols'
    assert len(cols.children) == 3
    # The first column will be the first child, remaining will be wrapped in
    # a parent.
    (col_name, col) = parse_column(cols.children[0])
    columns = SortableDict()
    columns[col_name] = col

    if bool(cols.children[1]):
        for node in cols.children[1].children:
            for nchild in node.children:
                if nchild.expr_name == 'valueSep':
                    continue
                else:
                    (col_name, col) = parse_column(nchild)
                    columns[col_name] = col
    return columns

def parse_column(col):
    assert col.expr_name == 'col'
    # We should have the ID and the metadata
    assert len(col.children) == 2
    col_id = parse_id(col.children[0])
    if bool(col.children[1].children):
        col_meta = parse_meta(col.children[1].children[0])
    else:
        col_meta = MetadataObject()
    return (col_id, col_meta)

def parse_rows(grid, rows):
    for row in [r for r in rows.children if r.expr_name == 'row']:
        parse_row(grid, row)

def parse_row(grid, row):
    assert row.expr_name == 'row'
    # Cell names
    columns = list(grid.column.keys())
    if not bool(row.children): # pragma: no cover
        # Empty row?  Shouldn't happen, but just in case.
        return {}

    # First cell
    cell_id = columns.pop(0)
    cell_value = parse_cell(row.children[0])
    data = {cell_id: cell_value}

    # Remaining cells
    if bool(row.children[1].children) and bool(columns):
        for node in row.children[1].children:
            for nchild in node.children:
                if nchild.expr_name == 'valueSep':
                    continue
                try:
                    cell_id = columns.pop(0)
                except IndexError:
                    break

                cell_value = parse_cell(nchild)
                data[cell_id] = cell_value

    grid.append(data)

def parse_cell(cell):
    assert cell.expr_name == 'cell'
    if bool(cell.children):
        assert len(cell.children) == 1
        return parse_scalar(cell.children[0])
    else:
        return None

def parse_scalar(scalar, mode=MODE_ZINC, charset='utf-8'):
    if mode == MODE_ZINC:
        # Should have a child which is the type of scalar.
        assert scalar.expr_name == 'scalar'
        assert len(scalar.children) == 1
        scalar_child = scalar.children[0]
        if scalar_child.expr_name == 'null':
            return None
        elif scalar_child.expr_name == 'marker':
            return MARKER
        elif scalar_child.expr_name == 'remove':
            return REMOVE
        elif scalar_child.expr_name == 'bool':
            return parse_bool(scalar_child)
        elif scalar_child.expr_name == 'ref':
            return parse_ref(scalar_child, charset)
        elif scalar_child.expr_name == 'bin':
            return parse_bin(scalar_child)
        elif scalar_child.expr_name == 'str':
            return parse_str(scalar_child, charset)
        elif scalar_child.expr_name == 'uri':
            return parse_uri(scalar_child)
        elif scalar_child.expr_name == 'date':
            return parse_date(scalar_child)
        elif scalar_child.expr_name == 'time':
            return parse_time(scalar_child)
        elif scalar_child.expr_name == 'dateTime':
            return parse_date_time(scalar_child)
        elif scalar_child.expr_name == 'coord':
            return parse_coord(scalar_child)
        elif scalar_child.expr_name == 'number':
            return parse_number(scalar_child)
        else: # pragma: no cover
            raise NotImplementedError('Unhandled case: %s' \
                    % scalar_child.prettily())
    elif mode == MODE_JSON:
        # Simple cases
        if scalar is None:
            return None
        elif scalar == MARKER_STR:
            return MARKER
        elif isinstance(scalar, bool):
            return scalar
        elif scalar == 'n:INF':
            return float('INF')
        elif scalar == 'n:-INF':
            return -float('INF')
        elif scalar == 'n:NaN':
            return float('nan')
        # Conversion to dict of float value turn them into float 
        # so regex won't work... better just return them
        elif isinstance(scalar, float):
            return scalar

        # Is it a number?
        match = NUMBER_RE.match(scalar)
        if match:
            # We'll get a value and a unit, amongst other tokens.
            matched = match.groups()
            value = float(matched[0])
            if matched[-1] is not None:
                # It's a quantity
                return Quantity(value, matched[-1])
            else:
                # It's a raw value
                return value

        # Is it a string?
        match = STR_RE.match(scalar)
        if match:
            return match.group(1)

        # Is it a reference?
        match = REF_RE.match(scalar)
        if match:
            matched = match.groups()
            if matched[-1] is not None:
                return Ref(matched[0], matched[-1], has_value=True)
            else:
                return Ref(matched[0])

        # Is it a date?
        match = DATE_RE.match(scalar)
        if match:
            (year, month, day) = match.groups()
            return datetime.date(year=int(year), month=int(month), day=int(day))

        # Is it a time?
        match = TIME_RE.match(scalar)
        if match:
            (hour, minute, _, second, _) = match.groups()
            # Convert second to seconds and microseconds
            if second is None:
                sec = 0
                usec = 0
            elif '.' in second:
                (whole_sec, frac_sec) = second.split('.',1)
                sec = int(whole_sec)
                usec = int(frac_sec[:6].ljust(6,'0'))
            else:
                sec = int(second)
                usec = 0
            return datetime.time(hour=int(hour), minute=int(minute),
                    second=sec, microsecond=usec)

        # Is it a date/time?
        match = DATETIME_RE.match(scalar)
        if match:
            matches = match.groups()
            # Parse ISO8601 component
            isodate = iso8601.parse_date(matches[0])
            # Parse timezone
            tzname  = matches[-1]
            if tzname is None:
                return isodate  # No timezone given
            else:
                try:
                    tz = timezone(tzname)
                    return isodate.astimezone(tz)
                except: # pragma: no cover
                    # Unlikely code path.
                    return isodate

        # Is it a URI?
        match = URI_RE.match(scalar)
        if match:
            return Uri(match.group(1))

        # Is it a Bin?
        match = BIN_RE.match(scalar)
        if match:
            return Bin(match.group(1))

        # Is it a co-ordinate?
        match = COORD_RE.match(scalar)
        if match:
            (lat,lng) = match.groups()
            return Coordinate(float(lat),float(lng))
        return scalar
    else: # pragma: no cover
        raise NotImplementedError('Format not implemented: %s' % mode)

def parse_id(id_node):
    assert id_node.expr_name == 'id'
    return id_node.text

# These *should* have coverage, but unfortunately, there's no way to
# say, "no cover on Python 2.x" or "no cover on Python 3.x"
if six.PY3: # pragma: no cover
    # This will probably need investigation... using nHastack, 
    # we need to use utf-8 instead of ascii... 
    # charset should be defined somewhere
    _str_to_bytes = lambda s, charset : six.binary_type(s, charset)
else: # pragma: no cover
    _str_to_bytes = lambda s, charset : six.text_type(s)

def _decode_escape(esc):
    esc = esc.group(1)
    if esc[0] in 'uU':
        return six.unichr(int(esc[1:], 16))
    elif esc == '"':
        return '\"'
    elif esc == 'b':
        return '\b'
    elif esc == 'f':
        return '\f'
    elif esc == 'n':
        return '\n'
    elif esc == 'r':
        return '\r'
    elif esc == 't':
        return '\t'
    else:
        return esc

def _sub_escape(str_value):
    (str_value, replacements) = STR_ESC_RE.subn(_decode_escape, str_value)
    while replacements > 0:
        (str_value, replacements) = STR_ESC_RE.subn(_decode_escape, str_value)
    return str_value


def parse_str(str_node, charset = 'utf-8'):
    assert str_node.expr_name == 'str'
    assert len(str_node.children) == 3
    return _sub_escape(str_node.children[1].text)

def parse_uri(uri_node):
    assert uri_node.expr_name == 'uri'
    assert len(uri_node.children) == 3

    uri_value = uri_node.children[1].text

    # Replace escapes.
    for orig, esc in STR_SUB:
        uri_value = uri_value.replace(esc, orig)
    return Uri(URI_META.sub(\
            lambda m : m.group(0) if m.group(1) != '`' else '`',
            uri_value))

def parse_bin(bin_node):
    assert bin_node.expr_name == 'bin'
    assert len(bin_node.children) == 3
    return Bin(bin_node.children[1].text)

def parse_number(num_node):
    assert num_node.expr_name == 'number'
    assert len(num_node.children) == 1
    value = num_node.children[0]
    if value.expr_name == 'quantity':
        return parse_quantity(value)
    elif value.expr_name == 'decimal':
        return parse_decimal(value)
    elif value.text in ('INF','-INF','NaN'):
        return float(value.text)
    else: # pragma: no cover
        raise NotImplementedError(\
                'Unhandled case: %s' % value.prettily())

def parse_quantity(quantity_node):
    assert quantity_node.expr_name == 'quantity'
    assert len(quantity_node.children) == 2
    # First child is the value, type decimal
    value = parse_decimal(quantity_node.children[0])
    # Second is the unit.
    unit = quantity_node.children[1].text
    return Quantity(value, unit)

def parse_decimal(decimal_node):
    assert decimal_node.expr_name == 'decimal'
    return float(decimal_node.text.replace('_',''))

def parse_bool(bool_node):
    assert bool_node.expr_name == 'bool'
    assert bool_node.text.upper() in 'TF'
    return bool_node.text.upper() == 'T'

def parse_coord(coordinate_node):
    assert coordinate_node.expr_name == 'coord'
    assert len(coordinate_node.children) == 7
    # Co-ordinates are in child nodes 2 and 4.
    lat = float(coordinate_node.children[2].text)
    lng = float(coordinate_node.children[4].text)
    return Coordinate(lat, lng)

def parse_ref(ref_node, charset = 'utf-8'):
    assert ref_node.expr_name == 'ref'
    assert len(ref_node.children) == 3
    # We have an @ symbol, the reference name and in a child node,
    # the value string.
    ref = ref_node.children[1].text
    has_value = bool(ref_node.children[2].children)
    if has_value:
        value = parse_str(ref_node.children[2].children[0].children[1], charset)
    else:
        value = None
    return Ref(ref, value, has_value)

def parse_date(date_node):
    assert date_node.expr_name == 'date'
    # Date is in 3 parts, separated by hyphens.
    (ys, ms, ds) = date_node.text.split('-',3)
    return datetime.date(year=int(ys),
                        month=int(ms),
                        day=int(ds))

def parse_time(time_node):
    assert time_node.expr_name == 'time'
    # Date is in 3 parts, separated by hyphens.
    (hs, ms, ss) = time_node.text.split(':',3)
    # Split seconds into whole and fractional parts
    if '.' in ss:
        (whole_sec, frac_sec) = ss.split('.',1)
        sec = int(whole_sec)
        usec = int(frac_sec[:6].ljust(6,'0'))
    else:
        sec = int(ss)
        usec = 0
    return datetime.time(hour=int(hs),
                        minute=int(ms),
                        second=sec,
                        microsecond=usec)

def parse_date_time(date_time_node):
    assert date_time_node.expr_name == 'dateTime'
    assert len(date_time_node.children) == 2
    # Made up of parts: ISO8601 Date/Time, time zone label
    # (with proceeding space)
    isodt = iso8601.parse_date(date_time_node.children[0].text)
    tzname = date_time_node.children[1].text[1:]

    if (isodt.tzinfo is None) and bool(tzname): # pragma: no cover
        # This technically shouldn't happen according to Zinc specs
        return timezone(tzname).localise(isodt)
    elif bool(tzname):
        try:
            tz = timezone(tzname)
            return isodt.astimezone(tz)
        except: # pragma: no cover
            # Unlikely to occur, might do though if Project Haystack changes
            # its timezone list or if a system doesn't recognise a particular
            # timezone.
            return isodt    # Failed, leave alone
    else:
        return isodt

