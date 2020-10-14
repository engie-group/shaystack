# (C) 2020 Philippe PRADOS
# -*- coding: utf-8 -*-
# vim: set ts=4 sts=4 et tw=78 sw=4 si:

class FilterPath:
    def __init__(self, path):
        self.path = path

    def __repr__(self):
        return "->".join(self.path)


class FilterBinary:
    def __init__(self, operator, left, right):
        self.operator = operator
        self.left = left
        self.right = right

    def __repr__(self):
        return "%s %s %s" % (self.left, self.operator, self.right)


class FilterUnary:
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
