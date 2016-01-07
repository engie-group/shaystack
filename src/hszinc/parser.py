#!/usr/bin/python
# -*- coding: utf-8 -*-
# Zinc Grid Metadata
# (C) 2016 VRT Systems
#
# vim: set ts=4 sts=4 et tw=78 sw=4 si:

from grid import Grid
from metadata import Item, ItemPair
from grammar import zinc_grammar
from sortabledict import SortableDict
from datatypes import Quantity, Coordinate, Ref, Bin, Uri, MARKER
from zoneinfo import timezone
import datetime
import iso8601

def parse(zinc_str):
    '''
    Parse the given Zinc text and return the equivalent data.
    '''
    # Split the separate grids up, the grammar definition has trouble splitting
    # them up normally.  This will truncate the newline off the end of the last
    # row.
    return map(parse_grid, zinc_str.split('\n\n'))

def parse_grid(grid_str):
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
    meta_items = parse_meta(meta.children[1].children[0])

    # The last thing in the list should be a newline
    assert meta.children[2].expr_name == 'nl'

    # The next item should be the columns
    columns = parse_columns(parsed.children[1])

    # This is enough to construct the base grid.
    grid = Grid(version=version, metadata=meta_items, columns=columns)

    # Now to parse the rows
    parse_rows(grid, parsed.children[2])
    return grid

def parse_meta(meta):
    assert meta.expr_name == 'meta'
    items = []

    for item_parent in meta.children:
        # There'll probably be a space beforehand
        for node in item_parent.children:
            if node.expr_name == 'metaItem':
                items.append(parse_meta_item(node))
                break
    return items

def parse_meta_item(item):
    # This could be an 'id' or a 'metaPair'
    assert len(item.children) == 1
    item_child = item.children[0]
    if item_child.expr_name == 'id':
        # This is a marker
        return Item(parse_id(item_child))
    elif item_child.expr_name == 'metaPair':
        # This is a metadata pair
        assert len(item_child.children) == 3
        item_id = parse_id(item_child.children[0])
        item_value = parse_scalar(item_child.children[2])
        return ItemPair(item_id, item_value)
    else:
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
        col_meta = []
    return (col_id, col_meta)

def parse_rows(grid, rows):
    map(lambda r : parse_row(grid, r),
            filter(lambda r : r.expr_name == 'row', rows.children))

def parse_row(grid, row):
    assert row.expr_name == 'row'
    # Cell names
    columns = grid.column.keys()
    if not bool(row.children):
        # Empty row?  Shouldn't happen, but just in case.
        return {}

    # First cell
    cell_id = columns.pop(0)
    cell_value = parse_cell(row.children[0])
    data = {cell_id: cell_value}

    # Remaining cells
    if bool(row.children[1].children):
        for node in row.children[1].children:
            for nchild in node.children:
                if nchild.expr_name == 'valueSep':
                    continue
                cell_id = columns.pop(0)
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

def parse_scalar(scalar):
    # Should have a child which is the type of scalar.
    assert scalar.expr_name == 'scalar'
    assert len(scalar.children) == 1
    scalar_child = scalar.children[0]
    if scalar_child.expr_name == 'null':
        return None
    elif scalar_child.expr_name == 'marker':
        return parse_marker(scalar_child)
    elif scalar_child.expr_name == 'bool':
        return parse_bool(scalar_child)
    elif scalar_child.expr_name == 'ref':
        return parse_ref(scalar_child)
    elif scalar_child.expr_name == 'bin':
        return parse_bin(scalar_child)
    elif scalar_child.expr_name == 'str':
        return parse_str(scalar_child)
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
    else:
        raise NotImplementedError('Unhandled case: %s' \
                % scalar_child.prettily())

def parse_id(id_node):
    assert id_node.expr_name == 'id'
    return id_node.text

def parse_str(str_node):
    assert str_node.expr_name == 'str'
    assert len(str_node.children) == 3
    return str_node.children[1].text

def parse_uri(uri_node):
    assert uri_node.expr_name == 'uri'
    assert len(uri_node.children) == 3
    return Uri(uri_node.children[1].text)

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
    raise NotImplementedError('Unhandled case: %s' % value.prettily())

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
    return float(decimal_node.text)

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
    sf = float(ss)
    si = int(sf)
    sf -= si
    return datetime.time(hour=int(hs),
                        minute=int(ms),
                        second=si,
                        microseconds=int(sf*1e6))

def parse_date_time(date_time_node):
    assert date_time_node.expr_name == 'dateTime'
    assert len(date_time_node.children) == 2
    # Made up of parts: ISO8601 Date/Time, time zone label
    # (with proceeding space)
    isodt = iso8601.parse_date(date_time_node.children[0].text)
    tzname = date_time_node.children[1].text[1:]

    if (isodt.tzinfo is None) and bool(tzname):
        return timezone(tzname).localise(isodt)
    elif bool(tzname):
        try:
            tz = timezone(tzname)
            return isodt.astimezone(tz)
        except:
            return isodt    # Failed, leave alone
    else:
        return isodt
