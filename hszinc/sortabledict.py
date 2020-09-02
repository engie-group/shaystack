#!/usr/bin/python
# -*- coding: utf-8 -*-
# Sortable dict helper class
# (C) 2016 VRT Systems
#
# vim: set ts=4 sts=4 et tw=78 sw=4 si:

try:
    import collections.abc as col
except ImportError:  # pragma: no cover
    import collections as col

class SortableDict(col.MutableMapping):
    """
    A dict-like object that permits value ordering/re-ordering.
    """

    def __init__(self, initial=None, validate_fn=None):
        self._values = {}
        self._order = []
        self._validate_fn = validate_fn
        super(SortableDict, self).__init__()

        # Copy initial values into dict.
        if initial is not None:
            # If we're given a dict; make it a list of items
            if isinstance(initial, dict):
                initial = list(initial.items())

            for (key, val) in initial:
                self[key] = val

    def __repr__(self):
        return '%s{%s}' % (self.__class__.__name__,
                ', '.join([
                    '%r=%r' % (k,v) for k,v in list(self.items())
                ]))

    def __getitem__(self, key):
        return self._values[key]

    def __setitem__(self, key, value):
        return self.add_item(key, value)

    def __delitem__(self, key):
        del self._values[key]
        self._order.remove(key)

    def __iter__(self):
        return iter(self._order)

    def __len__(self):
        return len(self._order)

    def add_item(self, key, value, after=False, index=None, pos_key=None,
            replace=True):
        """
        Add an item at a specific location, possibly replacing the
        existing item.

        If after is True, we insert *after* the given index, otherwise we
        insert before.

        The position is specified using either index or pos_key, the former
        specifies the position from the start of the array (base 0).  pos_key
        specifies the name of another key, and positions the new key relative
        to that key.

        When replacing, the position will be left un-changed unless a location
        is specified explicitly.
        """
        if self._validate_fn:
            self._validate_fn(value)

        if (index is not None) and (pos_key is not None):
            raise ValueError('Either specify index or pos_key, not both.')
        elif pos_key is not None:
            try:
                index = self.index(pos_key)
            except ValueError:
                raise KeyError('%r not found' % pos_key)

        if after and (index is not None):
            # insert inserts *before* index, so increment by one.
            index += 1

        if key in self._values:
            if not replace:
                raise KeyError('%r is duplicate' % key)

            if index is not None:
                # We are re-locating.
                del self[key]
            else:
                # We are updating
                self._values[key] = value
                return

        if index is not None:
            # Place at given position
            self._order.insert(index, key)
        else:
            # Place at end
            self._order.append(key)
        self._values[key] = value

    def at(self, index):
        """
        Return the key at the given index.
        """
        return self._order[index]

    def value_at(self, index):
        """
        Return the value at the given index.
        """
        return self[self.at(index)]

    def index(self, *args, **kwargs):
        return self._order.index(*args, **kwargs)

    def reverse(self, *args, **kwargs):
        return self._order.reverse(*args, **kwargs)

    def sort(self, *args, **kwargs):
        return self._order.sort(*args, **kwargs)

    def pop_at(self, index):
        """
        Remove the key at the given index and return its value.
        """
        return self.pop(self.at(index))
