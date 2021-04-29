# -*- coding: utf-8 -*-
# Filter AST
# See the accompanying LICENSE file.
# (C) 2021 Engie Digital
#
# vim: set ts=4 sts=4 et tw=78 sw=4 si:

"""
Abstract Syntax Tree for the filter syntax (See https://project-haystack.org/doc/docHaystack/Filters)
"""
from typing import List, Optional


class FilterNode:  # pylint: disable=too-few-public-methods
    """Top type of all filter nodes."""


class FilterPath(FilterNode):  # pylint: disable=too-few-public-methods
    """A filter path (a->b->c)"""
    __slots__ = ("paths",)

    def __init__(self, paths: List[str]):
        """
        Models a path in the filter request
        Args:
            paths: An ordered list of string
        """
        self.paths = paths

    def __repr__(self) -> str:
        return "->".join(self.paths)


class FilterBinary(FilterNode):  # pylint: disable=too-few-public-methods
    """A filter binary operator"""

    __slots__ = "operator", "left", "right"

    def __init__(self, operator: str, left: FilterNode, right: FilterNode):
        """
        Models a binary operation in the filter request
        Args:
            operator: The operator
            left: The left node for the operator.
            right: The right node for the operator.
        """
        self.operator = operator
        self.left = left
        self.right = right

    def __repr__(self) -> str:
        return "%s %s %s" % (self.left, self.operator, self.right)


class FilterUnary(FilterNode):  # pylint: disable=too-few-public-methods
    """A filter unary operator"""

    __slots__ = "operator", "right"

    def __init__(self, operator: str, right: FilterNode):
        """
        Models an unary operation in the filter request
        Args:
            operator: The operator
            right: The right part of the operator
        """
        self.operator = operator
        self.right = right

    def __repr__(self) -> str:
        return "%s %s" % (self.operator, self.right)


class FilterAST:  # pylint: disable=too-few-public-methods
    """The root of AST"""

    __slots__ = ("head",)

    def __init__(self, head: Optional[FilterNode]):
        """
        Model a parsing filter request.
        Args:
            head: The to node
        """
        self.head = head

    def __repr__(self) -> str:
        return "AST:" + repr(self.head)
