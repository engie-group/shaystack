# -*- coding: utf-8 -*-
# Grid CSV dumper
# See the accompanying LICENSE file.
# (C) 2021 Engie Digital
#
# vim: set ts=4 sts=4 et tw=78 sw=4 si:
"""
Generate date period based on period with a start and an end date and return
- All years in this period
- All months in this period
- All days in this period
"""
import calendar
from typing import List
from datetime import datetime


class InvalidDateRange(ValueError):
    """Error when a date range is invalid"""


def check_data_range(values):
    start, end = values.get("start"), values.get("end")
    if start and end and start >= end:
        raise InvalidDateRange("Start date must be lower than end date")
    return values


class Period:
    """Class that represent a period with a start and an end date."""

    def __init__(self, start: datetime, end: datetime):
        """

        Args:
            start (datetime): the start date
            end (datetime): the end date
        """
        self.start = start
        self.end = end

    def __str__(self):
        return f"{self.start} - {self.end}"

    @property
    def years(self) -> List[int]:
        """
        All years in period.
        :return: all years in period
        """
        return list(range(self.start.year, self.end.year + 1))

    @property
    def months(self) -> List[int]:
        """
        All months in period.
        :return: all months in period
        """
        year_nr = self.end.year - self.start.year

        if year_nr == 0:
            return list(range(self.start.month, self.end.month + 1))

        if year_nr == 1 and self.start.month > self.end.month:
            res = list(range(1, self.end.month + 1)) + list(range(self.start.month, 13))
            return res

        return list(range(1, 13))

    @property
    def days(self) -> List[int]:
        """
        All days in period
        :return: all days in period
        """
        month_nr = (
                self.end.month - self.start.month + 12 * (self.end.year - self.start.year)
        )

        if month_nr == 0:
            return list(range(self.start.day, self.end.day + 1))
        if month_nr == 1 and self.start.day > self.end.day:
            last_day_month = calendar.monthrange(self.start.year, self.start.month)[1]
            res = list(range(1, self.end.day + 1)) + list(
                range(self.start.day, last_day_month + 1)
            )
            return res
        if month_nr >= 12:
            return list(range(1, 32))

        max_days = max(
            [calendar.monthrange(self.start.year, month)[1] for month in self.months]
        )
        return list(range(1, max_days + 1))
