#!/usr/bin/python
# -*- coding: utf-8 -*-
# Pint integration helpers
# (C) 2016 VRT Systems
#
"""
Tools to convert haystack unit to pint unit.
"""
from pint import UnitRegistry

HAYSTACK_CONVERSION = [
    (u'_', ' '),
    (u'°', 'deg'),
    (u'per ', '/ '),
    (u'per_h', 'per_hour'),
    (u'Δ', 'delta_'),
    (u'meters', 'meter'),
    (u'liters', 'liter'),
    (u'gallons', 'gallon'),
    (u'millimeters', 'millimeter'),
    (u'centimeters', 'centimeter'),
    (u'H₂O', 'H2O'),
    (u'Volt', 'volt'),
    (u'grams', 'gram'),
    (u'tons refrigeration', 'refrigeration_ton'),
    (u'%', 'percent'),
    (u'degree kelvin', 'degK'),
    (u'degree celsius', 'degC'),
    (u'degree fahrenheit', 'degF'),
    (u'btu', 'BTU'),
    (u'pound force', 'pound_force'),
    (u'metric ton', 'metric_ton'),
    (u'fluid ounce', 'fluid_ounce'),
    (u'imperial gallon', 'imperial_gallon'),
    (u'galUK', 'UK_gallon'),
    (u'kgdegK', '(kg degK)'),
    (u'tonrefh', 'refrigeration_ton * hour'),
    (u'tonref', 'refrigeration_ton'),
    (u'Nm ', 'newton meter'),
    (u'Ns', 'newton second'),
    (u'Js', 'joule second'),
    (u'short ton', 'short_ton'),
    (u'degrees angular', 'deg'),
    (u'degrees phase', 'deg'),
    (u'degPh', 'deg'),
    (u'yr', 'year '),
    (u'atmosphere', 'atm'),
    (u'mo', 'month '),
    (u'wk', 'week '),
    (u'parts / unit', 'ppu'),
    (u'parts / million', 'ppm'),
    (u'parts / billion', 'ppb'),
    (u'kcfm', 'kilocfm'),
    (u'kilohm', 'kiloohm'),
    (u'megohm', 'megaohm'),
    (u'volt ampere reactive', 'VAR'),
    (u'kilovolt ampere reactive', 'kVAR'),
    (u'megavolt ampere reactive', 'MVAR'),
    (u'VAh', 'volt * ampere * hour'),
    (u'kVAh', 'kilovolt * ampere * hour'),
    (u'MVAh', 'megavolt * ampere * hour'),
    (u'VARh', 'VAR * hour'),
    (u'kVARh', 'kVAR * hour'),
    (u'MVARh', 'MVAR * hour'),
    (u'hph', 'horsepower * hour'),
    (u'energy efficiency ratio', 'EER'),
    (u'coefficient of performance', 'COP'),
    (u'data center infrastructure efficiency', 'DCIE'),
    (u'power usage effectiveness', 'PUE'),
    (u'formazin nephelometric unit', 'fnu'),
    (u'nephelometric turbidity units', 'ntu'),
    (u'dBµV', 'dB microvolt'),
    (u'dBmV', 'dB millivolt'),
    (u'db', 'dB'),
    (u'Am', 'A * m'),
    (u'percent relative humidity', 'percentRH'),
    (u'pf', 'PF'),
    (u'power factor', 'PF'),
    (u'gH2O', 'g H2O'),
    (u'irradiance', ''),
    (u'irr', ''),
    (u'dry air', 'dry'),
    (u'dry', 'dry_air'),
    (u'kgAir', 'kg dry_air'),
    (u'percent obscuration', 'percentobsc'),
    (u'natural gas', ''),
    (u'Ωm', 'ohm meter'),
    (u'hecto cubic foot', 'hecto_cubic_foot'),
    (u'julian month', 'month'),
    (u'tenths second', 'tenths_second'),
    (u'hundredths second', 'hundredths_second'),
    (u'australian dollar', 'australian_dollar'),
    (u'british pound', 'british_pound'),
    (u'canadian dollar', 'canadian_dollar'),
    (u'chinese yuan', 'chinese_yuan'),
    (u'emerati dirham', 'emerati_dirham'),
    (u'indian rupee', 'indian_rupee'),
    (u'japanese yen', 'japanese_yen'),
    (u'russian ruble', 'russian_ruble'),
    (u'south korean won', 'south_korean_won'),
    (u'swedish krona', 'swedish_krona'),
    (u'swiss franc', 'swiss_franc'),
    (u'taiwan dollar', 'taiwan_dollar'),
    (u'us dollar', 'us_dollar'),
    (u'new israeli shekel', 'new_israeli_shekel'),
    (u'delta_K', 'delta_degC'),
    (u'delta degK', 'delta_degC'),
    (u'delta degC', 'delta_degC'),
    (u'delta degF', 'delta_degF'),
    (u'$', 'USD'),
    (u'£', 'GBP'),
    (u'元', 'CNY'),
    (u'€', 'EUR'),
    (u'₹', 'INR'),
    (u'¥', 'JPY'),
    (u'₩', 'KRW'),
    (u'of', '')
]

PINT_CONVERSION = [
    (u'foot ** 3', 'cubic_foot'),
    (u'/', 'per'),
    (u'hectofoot ** 3', 'hecto_cubic_foot'),
    (u'meter ** 3', 'cubic_meter'),
    (u'Volt_per', 'volts_per'),
    (u'°', 'degree'),
    (u'BTU', 'btu')
]


def to_haystack(unit):
    """
    Some parsing tweaks to fit pint units / handling of edge cases.
    """
    global HAYSTACK_CONVERSION  # pylint: disable=global-statement
    global PINT_CONVERSION  # pylint: disable=global-statement
    if unit == u'per_minute' or \
            unit == u'/min' or \
            unit == u'per_second' or \
            unit == u'/s' or \
            unit == u'per_hour' or \
            unit == u'/h' or \
            unit is None:  # pylint: disable=too-many-boolean-expressions
        return u''
        # Those units are not units... they are impossible to fit anywhere in Pint

    for pint_value, haystack_value in PINT_CONVERSION:
        unit = unit.replace(pint_value, haystack_value)
    for haystack_value, pint_value in HAYSTACK_CONVERSION:
        if pint_value == u'':
            continue
        unit = unit.replace(pint_value, haystack_value)  # FIXME: optimise this big loop
    return unit


def to_pint(unit):
    """
    Some parsing tweaks to fit pint units / handling of edge cases.
    """
    global HAYSTACK_CONVERSION  # pylint: disable=global-statement
    if unit == u'per_minute' or \
            unit == u'/min' or \
            unit == u'per_second' or \
            unit == u'/s' or \
            unit == u'per_hour' or \
            unit == u'/h' or \
            unit is None:
        return ''
        # Those units are not units... they are impossible to fit anywhere in Pint
    for haystack_value, pint_value in HAYSTACK_CONVERSION:  # FIXME: leasy
        unit = unit.replace(haystack_value, pint_value)
    return unit


def define_haystack_units() -> UnitRegistry:
    """
    Missing units found in project-haystack
    Added to the registry
    """
    unit_ureg = UnitRegistry(on_redefinition='ignore')
    unit_ureg.define(u'% = [] = percent')
    unit_ureg.define(u'pixel = [] = px = dot = picture_element = pel')
    unit_ureg.define(u'decibel = [] = dB')
    unit_ureg.define(u'ppu = [] = parts_per_unit')
    unit_ureg.define(u'ppm = [] = parts_per_million')
    unit_ureg.define(u'ppb = [] = parts_per_billion')
    unit_ureg.define(u'%RH = [] = percent_relative_humidity = percentRH')
    unit_ureg.define(u'cubic_feet = ft ** 3 = cu_ft')
    unit_ureg.define(u'cfm = cu_ft * minute = liter_per_second / 0.4719475')
    unit_ureg.define(u'cfh = cu_ft * hour')
    unit_ureg.define(u'cfs = cu_ft * second')
    unit_ureg.define(u'VAR = volt * ampere')
    unit_ureg.define(u'kVAR = 1000 * volt * ampere')
    unit_ureg.define(u'MVAR = 1000000 * volt * ampere')
    unit_ureg.define(u'inH2O = in_H2O')
    unit_ureg.define(u'dry_air = []')
    unit_ureg.define(u'gas = []')
    unit_ureg.define(u'energy_efficiency_ratio = [] = EER')
    unit_ureg.define(u'coefficient_of_performance = [] = COP')
    unit_ureg.define(u'data_center_infrastructure_efficiency = [] = DCIE')
    unit_ureg.define(u'power_usage_effectiveness = [] = PUE')
    unit_ureg.define(u'formazin_nephelometric_unit = [] = fnu')
    unit_ureg.define(u'nephelometric_turbidity_units = [] = ntu')
    unit_ureg.define(u'power_factor = [] = PF')
    unit_ureg.define(u'degree_day_celsius = [] = degdaysC')
    unit_ureg.define(u'degree_day_farenheit = degree_day_celsius * 9 / 5 = degdaysF')
    unit_ureg.define(u'footcandle = lumen / sq_ft = ftcd')
    unit_ureg.define(u'Nm = newton * meter')
    unit_ureg.define(u'%obsc = [] = percent_obscuration = percentobsc')
    unit_ureg.define(u'cycle = []')
    unit_ureg.define(u'cph = cycle / hour')
    unit_ureg.define(u'cpm = cycle / minute')
    unit_ureg.define(u'cps = cycle / second')
    unit_ureg.define(u'hecto_cubic_foot = 100 * cubic_foot')
    unit_ureg.define(u'tenths_second = second / 10')
    unit_ureg.define(u'hundredths_second = second / 100')

    # ureg.define('irradiance = W / sq_meter = irr')
    # In the definition of project haystack, there's a redundancy as irr = W/m^2
    # no need to use : watts_per_square_meter_irradiance

    # CURRENCY
    # I know...we won'T be able to convert right now !
    unit_ureg.define(u'australian_dollar = [] = AUD')
    unit_ureg.define(u'british_pound = [] = GBP = £')
    unit_ureg.define(u'canadian_dollar = [] = CAD')
    unit_ureg.define(u'chinese_yuan = [] = CNY = 元')
    unit_ureg.define(u'emerati_dirham = [] = AED')
    unit_ureg.define(u'euro = [] = EUR = €')
    unit_ureg.define(u'indian_rupee = [] = INR = ₹')
    unit_ureg.define(u'japanese_yen = [] = JPY = ¥')
    unit_ureg.define(u'russian_ruble = [] = RUB = руб')
    unit_ureg.define(u'south_korean_won = [] = KRW = ₩')
    unit_ureg.define(u'swedish_krona = [] = SEK = kr')
    unit_ureg.define(u'swiss_franc = [] = CHF = Fr')
    unit_ureg.define(u'taiwan_dollar = [] = TWD')
    unit_ureg.define(u'us_dollar = [] = USD = $')
    unit_ureg.define(u'new_israeli_shekel = [] = NIS')

    # See https://pint.readthedocs.io/en/stable/defining.html

    return unit_ureg


unit_reg = define_haystack_units()
