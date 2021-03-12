# -*- coding: utf-8 -*-
# SQL Provider
# See the accompanying LICENSE file.
# (C) 2021 Engie Digital
#
# vim: set ts=4 sts=4 et tw=78 sw=4 si:
# pylint: disable=line-too-long
"""
Tools to convert haystack filter to mongo request
"""
from datetime import datetime
from typing import Optional, Dict, Any, List, Union, cast

from shaystack import parse_filter, HaystackType, Quantity
from shaystack.filter_ast import FilterNode, FilterUnary, FilterPath, FilterBinary
from ..jsondumper import dump_scalar as json_dump_scalar

_simple_ops = {
    "==": "$eq",
    "!=": "$ne",
}
_logical_ops = {
    "and": "$and",
    "or": "$or",
}
_relative_ops = {
    "<": "$lt",
    "<=": "$lte",
    ">": "$gt",
    ">=": "$gte",
}


def _to_float(scalar: HaystackType) -> float:
    if isinstance(scalar, Quantity):
        return scalar.magnitude
    if isinstance(scalar, (int, float)):
        return scalar
    raise ValueError("impossible to compare with anything other than a number")


def _conv_filter(node: Union[FilterNode, HaystackType]) -> Union[Dict[str, Any], str]:
    if isinstance(node, FilterUnary):
        if node.operator == "has":
            return {"$cond": {"if": _conv_filter(node.right), "then": 1, "else": 0}}
        if node.operator == "not":
            if isinstance(node, FilterNode):
                return {"$not": _conv_filter(node.right)}
            return {"$cond": {"if": _conv_filter(node.right), "then": 0, "else": 1}}
    if isinstance(node, FilterPath):
        return '$entity.' + node.paths[0]
    if isinstance(node, FilterBinary):
        if node.operator in _simple_ops:
            return {_simple_ops[node.operator]: [
                _conv_filter(node.left),
                _conv_filter(node.right)[1:-1],
            ]}
        if node.operator in _logical_ops:
            return {_logical_ops[node.operator]: [
                _conv_filter(node.left),
                _conv_filter(node.right),
            ]}
        if node.operator in _relative_ops:
            path = _conv_filter(node.left)
            var = cast(FilterPath, node.left).paths[0]
            to_double = {
                "$let": {
                    "vars": {
                        f"{var}_": {
                            "$regexFind": {
                                "input": f"{path}",
                                "regex": "n:([-+]?([0-9]*[.])?[0-9]+([eE][-+]?\\d+)?)"
                            }
                        }
                    },
                    "in": {"$toDouble": {
                        "$arrayElemAt": [f"${var}_.captures", 0]
                    }}
                }
            }

            return {_relative_ops[node.operator]: [
                to_double,
                _to_float(node.right),
            ]}
        assert 0, "Invalid operator"
        return None
    return json_dump_scalar(node)


def _mongo_filter(grid_filter: Optional[str],
                  version: datetime,
                  limit: int = 0,
                  customer_id: str = '') -> List[Dict[str, Any]]:
    if not grid_filter:
        return [
            {
                "$match":
                    {
                        "customer_id": customer_id,
                        "start_datetime": {"$lte": version},
                        "end_datetime": {"$gt": version},
                    }
            },
            {"$replaceRoot": {"newRoot": "$entity"}}
        ]
    stages = [
        {
            "$match":
                {
                    "customer_id": customer_id,
                    "start_datetime": {"$lte": version},
                    "end_datetime": {"$gt": version},
                    "$expr":
                        _conv_filter(parse_filter(grid_filter).head)
                }
        },
        {"$replaceRoot": {"newRoot": "$entity"}}
    ]
    if limit:
        stages.append(
            {"$limit": limit}
        )
    return stages
