# (C) 2020 Philippe PRADOS
# -*- coding: utf-8 -*-
# vim: set ts=4 sts=4 et tw=78 sw=4 si:
# pylint: skip-file

from shaystack import Grid, REMOVE, VER_2_0, VER_3_0, Ref
from shaystack.grid_diff import grid_diff, grid_merge

def test_diff_version():
    left = Grid(version=VER_2_0)
    right = Grid(version=VER_3_0)

    diff = grid_diff(left, right)

    assert diff.version == VER_3_0
    assert grid_merge(left, diff) == right  # A + (B - A) == B


def test_diff_metadata_change_value():
    left = Grid(metadata={"a": 1, "b": 2})
    right = Grid(metadata={"a": 3, "b": 4})

    diff = grid_diff(left, right)
    assert len(diff) == 0
    assert diff.metadata["a"] == 3
    assert diff.metadata["b"] == 4

    assert grid_merge(left, diff) == right


def test_diff_metadata_remove_value():
    left = Grid(metadata={"a": 1, "b": 2})
    right = Grid(metadata={"b": 2})

    diff = grid_diff(left, right)
    assert len(diff) == 0
    assert diff.metadata["a"] == REMOVE
    assert "b" not in diff.metadata

    assert grid_merge(left, diff) == right


def test_diff_metadata_add_value():
    left = Grid(metadata={"a": 1, "b": 2})
    right = Grid(metadata={"a": 1, "b": 2, "c": 3})

    diff = grid_diff(left, right)
    assert len(diff) == 0
    assert diff.metadata["c"] == 3
    assert "a" not in diff.metadata
    assert "b" not in diff.metadata

    assert grid_merge(left, diff) == right


def test_diff_cols_change_value_in_map():
    left = Grid(columns={"a": {'m': 1, 'n': 2}, "b": {'m': 2}})
    right = Grid(columns={"a": {'m': 3, 'n': 2}, "b": {'m': 4}})

    diff = grid_diff(left, right)
    assert len(diff) == 0
    assert diff.column["a"] == {"m": 3}
    assert diff.column["b"] == {"m": 4}

    assert grid_merge(left, diff) == right


def test_diff_cols_add_value_in_map():
    left = Grid(columns={"a": {'m': 1}, "b": {'m': 2}})
    right = Grid(columns={"a": {'m': 1, 'n': 2}, "b": {'m': 4}})

    diff = grid_diff(left, right)
    assert len(diff) == 0
    assert diff.column["a"] == {"n": 2}
    assert diff.column["b"] == {"m": 4}

    assert grid_merge(left, diff) == right


def test_diff_cols_remove_value_in_map():
    left = Grid(columns={"a": {'m': 1, 'n': 2}, "b": {'m': 2}})
    right = Grid(columns={"a": {'n': 2}, "b": {'m': 2}})

    diff = grid_diff(left, right)
    assert len(diff) == 0
    assert diff.column["a"] == {"m": REMOVE}
    assert diff.column["b"] == {}

    assert grid_merge(left, diff) == right


def test_diff_cols_remove_first_col():
    left = Grid(columns={"a": {'m': 1}, "b": {'m': 2}, "c": {'m': 3}})
    right = Grid(columns={"b": {'m': 4}, "c": {'m': 3}})

    diff = grid_diff(left, right)
    assert len(diff) == 0
    assert diff.column["a"] == {'remove_': REMOVE}
    assert len(diff.column) == 3

    assert grid_merge(left, diff) == right


def test_diff_cols_remove_middle_col():
    left = Grid(columns={"a": {'m': 1}, "b": {'m': 2}, "c": {'m': 3}})
    right = Grid(columns={"a": {'m': 1}, "c": {'m': 3}})

    diff = grid_diff(left, right)
    assert len(diff) == 0
    assert len(diff.column) == 3
    assert diff.column["b"] == {'remove_': REMOVE}

    assert grid_merge(left, diff) == right


def test_diff_cols_remove_last_col():
    left = Grid(columns={"a": {'m': 1}, "b": {'m': 2}, "c": {'m': 3}})
    right = Grid(columns={"a": {'m': 1}, "b": {'m': 2}})

    diff = grid_diff(left, right)
    assert len(diff) == 0
    assert len(diff.column) == 3
    assert diff.column["c"] == {'remove_': REMOVE}

    assert grid_merge(left, diff) == right


def test_diff_cols_move_col():
    left = Grid(columns={"a": {'m': 1}, "b": {'m': 2}, "c": {'m': 3}})
    right = Grid(columns={"b": {'m': 2}, "a": {'m': 1}, "c": {'m': 3}})

    diff = grid_diff(left, right)
    assert len(diff) == 0
    assert len(diff.column) == 3

    assert grid_merge(left, diff) == right


def test_diff_change_value_with_id():
    left = Grid(columns={"id": {}, "a": {}, "b": {}})
    left.append({"id": Ref("my_id"), "a": 1, "b": 2})
    right = Grid(columns={"id": {}, "a": {}, "b": {}})
    right.append({"id": Ref("my_id"), "a": 3, "b": 4})

    diff = grid_diff(left, right)
    assert len(diff) == 1
    assert len(diff[0].keys()) == 3
    assert diff[0]['id'] == Ref("my_id")
    assert diff[0]['a'] == 3
    assert diff[0]['b'] == 4

    assert 'id' in diff.column
    assert 'a' in diff.column
    assert 'b' in diff.column
    assert 'remove_' not in diff.column

    assert grid_merge(left, diff) == right


def test_diff_add_empty_value_with_id():
    left = Grid(columns={"id": {}, "a": {}, "b": {}})
    left.append({"id": Ref("my_id"), "a": 1})
    right = Grid(columns={"id": {}, "a": {}, "b": {}})
    right.append({"id": Ref("my_id"), "a": 3, "b": 4})

    diff = grid_diff(left, right)
    assert len(diff) == 1
    assert len(diff[0].keys()) == 3
    assert diff[0]['id'] == Ref("my_id")
    assert diff[0]['a'] == 3
    assert diff[0]['b'] == 4

    assert 'id' in diff.column
    assert 'a' in diff.column
    assert 'b' in diff.column
    assert 'remove_' not in diff.column

    assert grid_merge(left, diff) == right


def test_diff_add_value_with_id():
    left = Grid(columns={"id": {}, "a": {}})
    left.append({"id": Ref("my_id"), "a": 1})
    right = Grid(columns={"id": {}, "a": {}, "b": {}})
    right.append({"id": Ref("my_id"), "a": 3, "b": 4})

    diff = grid_diff(left, right)
    assert len(diff) == 1
    assert len(diff[0].keys()) == 3
    assert diff[0]['id'] == Ref("my_id")
    assert diff[0]['a'] == 3
    assert diff[0]['b'] == 4

    assert 'id' in diff.column
    assert 'a' in diff.column
    assert 'b' in diff.column

    assert grid_merge(left, diff) == right


def test_diff_remove_value_with_id():
    left = Grid(columns={"id": {}, "a": {}, "b": {}})
    left.append({"id": Ref("my_id"), "a": 1, "b": 2})
    right = Grid(columns={"id": {}, "a": {}, "b": {}})
    right.append({"id": Ref("my_id"), "a": 3})

    diff = grid_diff(left, right)
    assert len(diff) == 1
    assert len(diff[0].keys()) == 3
    assert diff[0]['id'] == Ref("my_id")
    assert diff[0]['a'] == 3
    assert diff[0]['b'] == REMOVE

    assert 'id' in diff.column
    assert 'a' in diff.column
    assert 'b' in diff.column

    assert grid_merge(left, diff) == right


def test_diff_remove_record_with_id():
    left = Grid(columns={"id": {}, "a": {}, "b": {}})
    left.append({"id": Ref("my_id"), "a": 1, "b": 2})
    right = Grid(columns={"id": {}, "a": {}, "b": {}})
    right.append({"id": Ref("other_id"), "a": 3})

    diff = grid_diff(left, right)
    assert len(diff) == 2
    assert len(diff[0].keys()) == 2
    assert diff[0]['id'] == Ref("my_id")
    assert diff[0]['remove_'] == REMOVE
    assert len(diff[1].keys()) == 2
    assert diff[1]['id'] == Ref("other_id")
    assert diff[1]['a'] == 3

    assert 'id' in diff.column
    assert 'a' in diff.column
    assert 'b' in diff.column
    assert 'remove_' in diff.column

    assert grid_merge(left, diff) == right


def test_diff_change_value_without_id():
    left = Grid(columns={"a": {}, "b": {}})
    left.append({"a": 1, "b": 2})
    right = Grid(columns={"a": {}, "b": {}})
    right.append({"a": 3, "b": 4})

    diff = grid_diff(left, right)
    assert len(diff) == 2
    assert len(diff[0].keys()) == 3
    assert diff[0]['a'] == 1
    assert diff[0]['b'] == 2
    assert diff[0]['remove_'] == REMOVE
    assert diff[1]['a'] == 3
    assert diff[1]['b'] == 4
    assert 'remove_' not in diff[1]

    assert 'a' in diff.column
    assert 'b' in diff.column

    assert grid_merge(left, diff) == right


def test_diff_remove_value_without_id():
    left = Grid(columns={"a": {}, "b": {}})
    left.append({"a": 1, "b": 2})
    right = Grid(columns={"a": {}, "b": {}})
    right.append({"a": 1})

    diff = grid_diff(left, right)
    assert len(diff) == 2
    assert len(diff[0].keys()) == 3
    assert diff[0]['a'] == 1
    assert diff[0]['b'] == 2
    assert diff[0]['remove_'] == REMOVE
    assert diff[1]['a'] == 1
    assert 'b' not in diff[1]
    assert 'remove_' not in diff[1]

    assert 'id' not in diff.column
    assert 'a' in diff.column
    assert 'b' in diff.column

    assert grid_merge(left, diff) == right


def test_diff_remove_record_without_id():
    left = Grid(columns={"a": {}, "b": {}})
    left.append({"a": 1, "b": 2})
    left.append({"a": 3, "b": 4})
    right = Grid(columns={"a": {}, "b": {}})
    right.append({"a": 5, "b": 6})

    diff = grid_diff(left, right)
    assert len(diff) == 3
    assert len(diff[0].keys()) == 3
    assert diff[0]['a'] == 1
    assert diff[0]['b'] == 2
    assert diff[0]['remove_'] == REMOVE
    assert len(diff[1].keys()) == 3
    assert diff[1]['a'] == 3
    assert diff[1]['b'] == 4
    assert diff[1]['remove_'] == REMOVE
    assert len(diff[2].keys()) == 2
    assert diff[2]['a'] == 5
    assert diff[2]['b'] == 6

    assert 'id' not in diff.column
    assert 'a' in diff.column
    assert 'b' in diff.column

    assert grid_merge(left, diff) == right


def test_diff_remove_all_records_without_id():  # pylint: disable-next=invalid-sequence-index

    left = Grid(columns={"a": {}, "b": {}})
    left.append({"a": 1, "b": 2})
    right = Grid(columns={"a": {}, "b": {}})

    diff = grid_diff(left, right)

    assert len(diff) == 1
    assert len(diff[0].keys()) == 3
    assert diff[0]['a'] == 1
    assert diff[0]['b'] == 2
    assert diff[0]['remove_'] == REMOVE

    assert 'id' not in diff.column
    assert 'a' in diff.column
    assert 'b' in diff.column

    assert grid_merge(left, diff) == right


def test_diff_same_record_without_id_in_source():
    left = Grid(columns={"a": {}, "b": {}})
    left.append({"a": 1, "b": 2})
    left.append({"a": 1, "b": 2})
    left.append({"a": 3, "b": 4})

    right = Grid(columns={"a": {}, "b": {}})
    right.append({"a": 1, "b": 2})
    right.append({"a": 3, "b": 4})
    right.append({"a": 3, "b": 4})

    diff = grid_diff(left, right)
    assert len(diff) == 2
    assert diff[0]['remove_'] is REMOVE
    assert diff[1] == {"a": 3, "b": 4}
    assert grid_merge(left, diff) == right


def test_diff_same_record_with_empty_map():
    left = Grid(columns={"a": {}, "b": {}})
    left.append({})
    left.append({})
    left.append({"a": 3, "b": 4})

    right = Grid(columns={"a": {}, "b": {}})
    right.append({})
    right.append({"a": 3, "b": 4})
    right.append({"a": 3, "b": 4})

    assert left != right
    diff = grid_diff(left, right)
    assert len(diff) == 2
    assert diff[0]['remove_'] is REMOVE
    assert diff[1] == {"a": 3, "b": 4}
    assert grid_merge(left, diff) == right


def test_diff_same_record_without_id_in_target():
    left = Grid(columns={"a": {}, "b": {}})
    left.append({"a": 1, "b": 2})
    left.append({"a": 3, "b": 4})

    right = Grid(columns={"a": {}, "b": {}})
    right.append({"a": 1, "b": 2})
    right.append({"a": 3, "b": 4})
    right.append({"a": 3, "b": 4})

    diff = grid_diff(left, right)
    assert len(diff) == 1


def test_diff_with_same_grid():
    left = Grid(columns={"a": {}, "b": {}})
    left.append({"a": 1, "b": 2})
    left.append({"a": 3, "b": 4})

    diff = grid_diff(left, left)
    assert len(diff) == 0

    assert grid_merge(left.copy(), diff) == left


def test_diff_with_no_column():
    left = Grid(columns={"a": {}, "b": {}})
    left.append({"a": 1, "b": 2})
    left.append({"a": 3, "b": 4})
    left.append({"a": 1, "b": 2})
    left.append({"a": 1, "b": 2})
    right = Grid()

    diff = grid_diff(left, right)
    assert len(diff) == 4

    assert grid_merge(left.copy(), diff) == right
