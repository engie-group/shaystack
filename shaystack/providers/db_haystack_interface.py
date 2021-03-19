# -*- coding: utf-8 -*-
# Abstract interface
# See the accompanying LICENSE file.
# (C) 2021 Engie Digital
#
# vim: set ts=4 sts=4 et tw=78 sw=4 si:
"""
Private extension of haystack implementation to add the link with DB.
"""
from abc import abstractmethod
from datetime import datetime
from typing import Optional

from . import HaystackInterface
from ..grid import Grid


class DBHaystackInterface(HaystackInterface):
    """
    Extension of HaystackInterface to add methods to manages database.
    """

    @abstractmethod
    def create_db(self) -> None:
        """
        Create the database and schema.
        """

    @abstractmethod
    def purge_db(self) -> None:
        """ Purge the current database. """

    @abstractmethod
    def import_data(self,
                    source_uri: str,
                    customer_id: str = '',
                    reset: bool = False,
                    version: Optional[datetime] = None
                    ) -> None:
        """
        Import source URI to destination URI.
        Args:
            source_uri: The source URI.
            customer_id: The current customer id to inject in each records.
            reset: Remove all the current data before import the grid.
            version: The associated version time.
        """

    @abstractmethod
    def import_ts(self,
                  source_uri: str,
                  customer_id: str = '',
                  version: Optional[datetime] = None
                  ):
        """
        Import only TS.
        Args:
            source_uri: The source URI.
            customer_id: The current customer id to inject in each records.
            version: version to save

        """

    @abstractmethod
    def update_grid(self,
                    diff_grid: Grid,
                    version: Optional[datetime],
                    customer_id: Optional[str],
                    now: Optional[datetime] = None) -> None:
        """Import the diff_grid inside the database.
        Args:
            diff_grid: The difference to apply in database.
            version: The version to save.
            customer_id: The customer id to insert in each row.
            now: The pseudo 'now' datetime.
        """

    @abstractmethod
    def read_grid(self,
                  customer_id: str = '',
                  version: Optional[datetime] = None) -> Grid:
        """
        Read all haystack data for a specific customer, from the database and return a Grid.
        Args:
            customer_id: The customer_id date to read
            version: version to load
        Returns:
            A grid with all data for a customer
        """
