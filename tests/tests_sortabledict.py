# -*- coding: utf-8 -*-
# Zinc dumping and parsing module
# See the accompanying LICENSE file.
# (C) 2016 VRT Systems
# (C) 2021 Engie Digital
#
# vim: set ts=4 sts=4 et tw=78 sw=4 si:

from shaystack.sortabledict import SortableDict


def test_set_get():
    a_dict = SortableDict()
    a_dict[1] = 'a'
    a_dict[2] = 'b'
    a_dict[3] = 'c'
    assert a_dict[1] == 'a'
    assert a_dict[2] == 'b'
    assert a_dict[3] == 'c'


def test_iter():
    a_dict = SortableDict()
    a_dict[3] = 'a'
    a_dict[2] = 'b'
    a_dict[1] = 'c'
    iter_items = list(a_dict)
    assert iter_items == [3, 2, 1]


def test_len():
    a_dict = SortableDict()
    a_dict[1] = 'a'
    a_dict[2] = 'b'
    a_dict[3] = 'c'
    assert len(a_dict) == 3


def test_del():
    a_dict = SortableDict()
    a_dict[1] = 'a'
    a_dict[2] = 'b'
    a_dict[3] = 'c'
    del a_dict[2]
    assert a_dict[1] == 'a'
    assert a_dict[3] == 'c'
    assert len(a_dict) == 2


def test_initial_dict_constructor():
    a_dict = {
        1: 'abcd',
        "a": 1234,
    }
    assert dict(SortableDict(a_dict)) == a_dict


def test_initial_items_constructor():
    a_list = [
        (1, 'abcd'),
        ("a", 1234),
    ]
    assert list(SortableDict(a_list).items()) == a_list


def test_repr():
    a_dict = SortableDict()
    a_dict[1] = 'a'
    a_dict[2] = 'b'
    a_dict[3] = 'c'
    assert repr(a_dict) == "SortableDict{1='a', 2='b', 3='c'}"


def test_add_item_with_index_and_pos_key():
    try:
        SortableDict(dict(foobar=123)).add_item('a key', 'a value', index=0, pos_key='foobar')
        assert False, 'No error raised for both key and index given'
    except ValueError:
        pass


def test_add_item_with_invalid_pos_key():
    try:
        SortableDict().add_item('a key', 'a value', pos_key='doesnotexist')
        assert False, 'No error raised for invalid key'
    except KeyError:
        pass


def test_add_item_after():
    a_dict = SortableDict()
    a_dict[1] = 'a'
    a_dict[2] = 'b'
    a_dict.add_item(3, 'c', after=True, pos_key=1)
    assert list(a_dict.items()) == [(1, 'a'), (3, 'c'), (2, 'b')]


def test_add_item_noreplace_duplicate():
    a_dict = SortableDict()
    a_dict[1] = 'a'
    try:
        a_dict.add_item(1, 'a2', replace=False)
        assert False, 'Replaced/inserted duplicate key'
    except KeyError:
        pass


def test_add_item_move():
    a_dict = SortableDict()
    a_dict[1] = 'a'
    a_dict[2] = 'b'
    a_dict[3] = 'c'
    a_dict.add_item(1, 'a', after=True, pos_key=3)
    assert list(a_dict.items()) == [(2, 'b'), (3, 'c'), (1, 'a')]


def test_add_item_replace():
    a_dict = SortableDict()
    a_dict[1] = 'a'
    a_dict[2] = 'b'
    a_dict[3] = 'c'
    a_dict.add_item(1, 'd', replace=True)
    assert list(a_dict.items()) == [(1, 'd'), (2, 'b'), (3, 'c')]


def test_at():
    a_dict = SortableDict()
    a_dict['a'] = 1
    a_dict['b'] = 2
    a_dict['c'] = 3
    assert a_dict.at(0) == 'a'
    assert a_dict.at(1) == 'b'
    assert a_dict.at(2) == 'c'


def test_index():
    a_dict = SortableDict()
    a_dict['a'] = 1
    a_dict['b'] = 2
    a_dict['c'] = 3
    assert a_dict.index('a') == 0
    assert a_dict.index('b') == 1
    assert a_dict.index('c') == 2


def test_reverse():
    a_dict = SortableDict()
    a_dict['a'] = 1
    a_dict['b'] = 2
    a_dict['c'] = 3
    a_dict.reverse()
    assert list(a_dict.items()) == [('c', 3), ('b', 2), ('a', 1)]


def test_sort():
    a_dict = SortableDict()
    a_dict['t'] = 1
    a_dict['d'] = 2
    a_dict['h'] = 3
    a_dict['x'] = 4
    a_dict.sort()
    assert list(a_dict.items()) == [('d', 2), ('h', 3), ('t', 1), ('x', 4)]


def test_value_at():
    a_dict = SortableDict()
    a_dict['a'] = 1
    a_dict['b'] = 2
    a_dict['c'] = 3
    assert a_dict.value_at(0) == 1
    assert a_dict.value_at(1) == 2
    assert a_dict.value_at(2) == 3


def test_pop_at():
    a_dict = SortableDict()
    a_dict['a'] = 1
    a_dict['b'] = 2
    a_dict['c'] = 3
    assert a_dict.pop_at(1) == 2
    assert list(a_dict.items()) == [('a', 1), ('c', 3)]
