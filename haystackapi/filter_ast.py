# -*- coding: utf-8 -*-
# Filter AST
# See the accompanying LICENSE Apache V2.0 file.
# (C) 2021 Engie Digital
#
# vim: set ts=4 sts=4 et tw=78 sw=4 si:

"""
Abstract Syntax Tree for the filter syntax (See https://www.project-haystack.org/doc/Filters)
"""
from typing import List, Optional


class FilterNode:  # pylint: disable=too-few-public-methods
    """ Top type of all filter nodes. """


class FilterPath(FilterNode):  # pylint: disable=too-few-public-methods
    """ A filter path (a->b->c) """

    def __init__(self, paths: List[str]):
        self.paths = paths

    def __repr__(self) -> str:
        return "->".join(self.paths)


class FilterBinary(FilterNode):  # pylint: disable=too-few-public-methods
    """ A filter binary operator """

    def __init__(self, operator: str, left: FilterNode, right: FilterNode):
        self.operator = operator
        self.left = left
        self.right = right

    def __repr__(self) -> str:
        return "%s %s %s" % (self.left, self.operator, self.right)


class FilterUnary(FilterNode):  # pylint: disable=too-few-public-methods
    """ A filter unary operator """

    def __init__(self, operator: str, right: FilterNode):
        self.operator = operator
        self.right = right

    def __repr__(self) -> str:
        return "%s %s" % (self.operator, self.right)


class FilterAST:  # pylint: disable=too-few-public-methods
    """ The root of AST """

    def __init__(self, head: Optional[FilterNode]):
        self.head = head

    def __repr__(self) -> str:
        return "AST:" + repr(self.head)
