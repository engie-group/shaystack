# (C) 2020 Philippe PRADOS
# -*- coding: utf-8 -*-
# vim: set ts=4 sts=4 et tw=78 sw=4 si:

class FilterNode:
    pass


class FilterPath(FilterNode):
    def __init__(self, paths):
        self.paths = paths

    def __repr__(self):
        return "->".join(self.paths)


class FilterBinary(FilterNode):
    def __init__(self, operator, left, right):
        self.operator = operator
        self.left = left
        self.right = right

    def __repr__(self):
        return "%s %s %s" % (self.left, self.operator, self.right)


class FilterUnary(FilterNode):
    def __init__(self, operator, right):
        self.operator = operator
        self.right = right

    def __repr__(self):
        return "%s %s" % (self.operator, self.right)


class FilterAST:
    def __init__(self, head):
        self._head = head

    def __repr__(self):
        return "AST:" + repr(self._head)
