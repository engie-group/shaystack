#!/usr/bin/python
# -*- coding: utf-8 -*-
# Zinc Grid Metadata
# (C) 2016 VRT Systems
#
# vim: set ts=4 sts=4 et tw=78 sw=4 si:

from sortabledict import SortableDict

class MetadataObject(SortableDict):
    '''
    An object that contains some metadata fields.  Used as a convenience
    base-class for grids and columns, both of which have metadata.
    '''

    def insert(self, index, item, replace=True):
        '''
        Insert the metadata item at 'index'
        '''
        item = Item.make_item(item)
        if isinstance(index, str):
            return self.add_item(item.name, item,
                    pos_key=index, replace=replace)
        else:
            return self.add_item(item.name, item,
                    index=index, replace=replace)

    def append(self, item, replace=True):
        '''
        Append the item to the metadata.
        '''
        item = Item.make_item(item)
        return self.add_item(item.name, item, replace=replace)

    def extend(self, items, replace=True):
        '''
        Append the items to the metadata.
        '''
        map(lambda i : self.append(i, replace=replace),
                map(Item.make_item, items))


class Item(object):
    '''
    Base class for metadata items.  This class also represents Markers.
    '''
    def __init__(self, name):
        self.name = name

    def __repr__(self):
        return '<%s(%r)>' % (self.__class__.__name__, self.name)

    @classmethod
    def make_item(self, item):
        if isinstance(item, Item):
            return item
        if isinstance(item, str):
            return Item(item)
        if isinstance(item, dict):
            if len(item) != 1:
                raise ValueError('dict must have exactly one item')
            return ItemPair(*(item.items()[0]))


class ItemPair(Item):
    '''
    A metadata item that has an associated value.
    '''
    def __init__(self, name, value):
        self.value = value
        super(ItemPair, self).__init__(name)

    def __repr__(self):
        return '<%s(%r = %r)>' % (self.__class__.__name__,
                self.name, self.value)
