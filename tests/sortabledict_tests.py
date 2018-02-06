# -*- coding: utf-8 -*-
# Zinc dumping and parsing module
# (C) 2016 VRT Systems
#
# vim: set ts=4 sts=4 et tw=78 sw=4 si:

from hszinc.sortabledict import SortableDict

def test_set_get():
    d = SortableDict()
    d[1] = 'a'
    d[2] = 'b'
    d[3] = 'c'
    assert d[1] == 'a'
    assert d[2] == 'b'
    assert d[3] == 'c'

def test_iter():
    d = SortableDict()
    d[3] = 'a'
    d[2] = 'b'
    d[1] = 'c'
    iter_items = list(d)
    assert iter_items == [3, 2, 1]

def test_len():
    d = SortableDict()
    d[1] = 'a'
    d[2] = 'b'
    d[3] = 'c'
    assert len(d) == 3

def test_del():
    d = SortableDict()
    d[1] = 'a'
    d[2] = 'b'
    d[3] = 'c'
    del d[2]
    assert d[1] == 'a'
    assert d[3] == 'c'
    assert len(d) == 2

def test_initial_dict_constructor():
    d = {
            1: 'abcd',
            "a": 1234,
    }
    assert dict(SortableDict(d)) == d

def test_initial_items_constructor():
    il = [
           (1, 'abcd'),
           ("a", 1234),
    ]
    assert list(SortableDict(il).items()) == il

def test_repr():
    d = SortableDict()
    d[1] = 'a'
    d[2] = 'b'
    d[3] = 'c'
    assert repr(d) == "SortableDict{1='a', 2='b', 3='c'}"

def test_additem_with_index_and_pos_key():
    try:
        SortableDict(dict(foobar=123)).add_item('a key', 'a value', index=0, pos_key='foobar')
        assert False, 'No error raised for both key and index given'
    except ValueError as e:
        pass

def test_additem_with_invalid_pos_key():
    try:
        SortableDict().add_item('a key', 'a value', pos_key='doesnotexist')
        assert False, 'No error raised for invalid key'
    except KeyError:
        pass

def test_additem_after():
    d = SortableDict()
    d[1] = 'a'
    d[2] = 'b'
    d.add_item(3, 'c', after=True, pos_key=1)
    assert list(d.items()) == [(1, 'a'), (3, 'c'), (2, 'b')]

def test_additem_noreplace_duplicate():
    d = SortableDict()
    d[1] = 'a'
    try:
        d.add_item(1, 'a2', replace=False)
        assert False, 'Replaced/inserted duplicate key'
    except KeyError:
        pass

def test_additem_move():
    d = SortableDict()
    d[1] = 'a'
    d[2] = 'b'
    d[3] = 'c'
    d.add_item(1, 'a', after=True, pos_key=3)
    assert list(d.items()) == [(2,'b'), (3,'c'), (1,'a')]

def test_additem_replace():
    d = SortableDict()
    d[1] = 'a'
    d[2] = 'b'
    d[3] = 'c'
    d.add_item(1, 'd', replace=True)
    assert list(d.items()) == [(1, 'd'), (2,'b'), (3,'c')]

def test_at():
    d = SortableDict()
    d['a'] = 1
    d['b'] = 2
    d['c'] = 3
    assert d.at(0) == 'a'
    assert d.at(1) == 'b'
    assert d.at(2) == 'c'

def test_index():
    d = SortableDict()
    d['a'] = 1
    d['b'] = 2
    d['c'] = 3
    assert d.index('a') == 0
    assert d.index('b') == 1
    assert d.index('c') == 2

def test_reverse():
    d = SortableDict()
    d['a'] = 1
    d['b'] = 2
    d['c'] = 3
    d.reverse()
    assert list(d.items()) == [('c',3), ('b',2), ('a',1)]

def test_sort():
    d = SortableDict()
    d['t'] = 1
    d['d'] = 2
    d['h'] = 3
    d['x'] = 4
    d.sort()
    assert list(d.items()) == [('d',2), ('h',3), ('t',1), ('x',4)]

def test_value_at():
    d = SortableDict()
    d['a'] = 1
    d['b'] = 2
    d['c'] = 3
    assert d.value_at(0) == 1
    assert d.value_at(1) == 2
    assert d.value_at(2) == 3

def test_pop_at():
    d = SortableDict()
    d['a'] = 1
    d['b'] = 2
    d['c'] = 3
    assert d.pop_at(1) == 2
    assert list(d.items()) == [('a',1), ('c',3)]
