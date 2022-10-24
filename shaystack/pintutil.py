# -*- coding: utf-8 -*-
# Pint integration helpers
# See the accompanying LICENSE file.
# (C) 2016 VRT Systems
# (C) 2021 Engie Digital
#
"""
Tools to convert haystack unit to pint unit.
"""
import importlib.resources as pkg_resources
import os
from typing import Dict

from pint import UnitRegistry
from pint.converters import ScaleConverter
from pint.definitions import UnitDefinition


def _load_haystack_alias() -> Dict[str, str]:
    """
    Load the official haystack mapping
    """
    haystack_symbol_to_canonical = {}
    with pkg_resources.open_text(str(__package__),
                                 'haystack_units_mapping.txt',
                                 encoding='UTF-8') as file:  # type: ignore
        for line in file:
            if '--' not in line and line.strip() != '':
                if line.startswith('#'):
                    continue
                canonical, *alias = line.rstrip().split(',')
                if not alias:
                    haystack_symbol_to_canonical[canonical] = canonical
                else:
                    for sym in alias:
                        haystack_symbol_to_canonical[sym] = canonical
    return haystack_symbol_to_canonical


_haystack_symbol_to_canonical = _load_haystack_alias()


def _to_pint_unit(unit: str) -> str:
    """
    Convert haystack unit to pint unit
    Args:
        unit: haystack unit

    Returns:
        pint unit
    """
    if not unit:
        return unit
    if unit in _haystack_symbol_to_canonical:
        return _haystack_symbol_to_canonical[unit]

    # Try to use pint
    return unit


def _load_pint_units() -> UnitRegistry:
    """Missing units found in project-haystack Added to the registry"""
    unit_ureg = UnitRegistry(on_redefinition='ignore')
    unit_ureg.load_definitions(os.path.join(os.path.dirname(__file__),
                                            'haystack_units.pint'))
    unit_ureg.define(UnitDefinition('%', 'percent', (), ScaleConverter(1 / 100.0)))
    return unit_ureg


unit_reg = _load_pint_units()
