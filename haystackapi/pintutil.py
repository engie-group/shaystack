# -*- coding: utf-8 -*-
# Pint integration helpers
# See the accompanying LICENSE file.
# (C) 2016 VRT Systems
# (C) 2021 Engie Digital
#
"""
Tools to convert haystack unit to pint unit.
"""
from pint import UnitRegistry

HAYSTACK_CONVERSION = [
    ('_', ' '),
    ('°', 'deg'),
    ('per ', '/ '),
    ('per_h', 'per_hour'),
    ('Δ', 'delta_'),
    ('meters', 'meter'),
    ('liters', 'liter'),
    ('gallons', 'gallon'),
    ('millimeters', 'millimeter'),
    ('centimeters', 'centimeter'),
    ('H₂O', 'H2O'),
    ('Volt', 'volt'),
    ('grams', 'gram'),
    ('tons refrigeration', 'refrigeration_ton'),
    ('%', 'percent'),
    ('degree kelvin', 'degK'),
    ('degree celsius', 'degC'),
    ('degree fahrenheit', 'degF'),
    ('btu', 'BTU'),
    ('pound force', 'pound_force'),
    ('metric ton', 'metric_ton'),
    ('fluid ounce', 'fluid_ounce'),
    ('imperial gallon', 'imperial_gallon'),
    ('galUK', 'UK_gallon'),
    ('kgdegK', '(kg degK)'),
    ('tonrefh', 'refrigeration_ton * hour'),
    ('tonref', 'refrigeration_ton'),
    ('Nm ', 'newton meter'),
    ('Ns', 'newton second'),
    ('Js', 'joule second'),
    ('short ton', 'short_ton'),
    ('degrees angular', 'deg'),
    ('degrees phase', 'deg'),
    ('degPh', 'deg'),
    ('yr', 'year '),
    ('atmosphere', 'atm'),
    ('mo', 'month '),
    ('wk', 'week '),
    ('parts / unit', 'ppu'),
    ('parts / million', 'ppm'),
    ('parts / billion', 'ppb'),
    ('kcfm', 'kilocfm'),
    ('kilohm', 'kiloohm'),
    ('megohm', 'megaohm'),
    ('volt ampere reactive', 'VAR'),
    ('kilovolt ampere reactive', 'kVAR'),
    ('megavolt ampere reactive', 'MVAR'),
    ('VAh', 'volt * ampere * hour'),
    ('kVAh', 'kilovolt * ampere * hour'),
    ('MVAh', 'megavolt * ampere * hour'),
    ('VARh', 'VAR * hour'),
    ('kVARh', 'kVAR * hour'),
    ('MVARh', 'MVAR * hour'),
    ('hph', 'horsepower * hour'),
    ('energy efficiency ratio', 'EER'),
    ('coefficient of performance', 'COP'),
    ('data center infrastructure efficiency', 'DCIE'),
    ('power usage effectiveness', 'PUE'),
    ('formazin nephelometric unit', 'fnu'),
    ('nephelometric turbidity units', 'ntu'),
    ('dBµV', 'dB microvolt'),
    ('dBmV', 'dB millivolt'),
    ('db', 'dB'),
    ('Am', 'A * m'),
    ('percent relative humidity', 'percentRH'),
    ('pf', 'PF'),
    ('power factor', 'PF'),
    ('gH2O', 'g H2O'),
    ('irradiance', ''),
    ('irr', ''),
    ('dry air', 'dry'),
    ('dry', 'dry_air'),
    ('kgAir', 'kg dry_air'),
    ('percent obscuration', 'percentobsc'),
    ('natural gas', ''),
    ('Ωm', 'ohm meter'),
    ('hecto cubic foot', 'hecto_cubic_foot'),
    ('julian month', 'month'),
    ('tenths second', 'tenths_second'),
    ('hundredths second', 'hundredths_second'),
    ('australian dollar', 'australian_dollar'),
    ('british pound', 'british_pound'),
    ('canadian dollar', 'canadian_dollar'),
    ('chinese yuan', 'chinese_yuan'),
    ('emerati dirham', 'emerati_dirham'),
    ('indian rupee', 'indian_rupee'),
    ('japanese yen', 'japanese_yen'),
    ('russian ruble', 'russian_ruble'),
    ('south korean won', 'south_korean_won'),
    ('swedish krona', 'swedish_krona'),
    ('swiss franc', 'swiss_franc'),
    ('taiwan dollar', 'taiwan_dollar'),
    ('us dollar', 'us_dollar'),
    ('new israeli shekel', 'new_israeli_shekel'),
    ('delta_K', 'delta_degC'),
    ('delta degK', 'delta_degC'),
    ('delta degC', 'delta_degC'),
    ('delta degF', 'delta_degF'),
    ('$', 'USD'),
    ('£', 'GBP'),
    ('元', 'CNY'),
    ('€', 'EUR'),
    ('₹', 'INR'),
    ('¥', 'JPY'),
    ('₩', 'KRW'),
    ('of', '')
]

PINT_CONVERSION = [
    ('foot ** 3', 'cubic_foot'),
    ('/', 'per'),
    ('hectofoot ** 3', 'hecto_cubic_foot'),
    ('meter ** 3', 'cubic_meter'),
    ('Volt_per', 'volts_per'),
    ('°', 'degree'),
    ('BTU', 'btu')
]


def to_haystack(unit: str):
    """Some parsing tweaks to fit pint units / handling of edge cases.

    Args:
        unit (str):
    """
    global HAYSTACK_CONVERSION  # pylint: disable=global-statement
    global PINT_CONVERSION  # pylint: disable=global-statement
    if unit == 'per_minute' or \
            unit == '/min' or \
            unit == 'per_second' or \
            unit == '/s' or \
            unit == 'per_hour' or \
            unit == '/h' or \
            unit is None:  # pylint: disable=too-many-boolean-expressions
        return ''
        # Those units are not units... they are impossible to fit anywhere in Pint

    for pint_value, haystack_value in PINT_CONVERSION:
        unit = unit.replace(pint_value, haystack_value)
    for haystack_value, pint_value in HAYSTACK_CONVERSION:
        if pint_value == '':
            continue
        unit = unit.replace(pint_value, haystack_value)  # PPR: optimise this big loop
    return unit


def to_pint(unit: str) -> str:
    """Some parsing tweaks to fit pint units / handling of edge cases.

    Args:
        unit (str):
    """
    global HAYSTACK_CONVERSION  # pylint: disable=global-statement
    if unit == 'per_minute' or \
            unit == '/min' or \
            unit == 'per_second' or \
            unit == '/s' or \
            unit == 'per_hour' or \
            unit == '/h' or \
            unit is None:
        return ''
        # Those units are not units... they are impossible to fit anywhere in Pint
    for haystack_value, pint_value in HAYSTACK_CONVERSION:  # PPR: leasy ?
        unit = unit.replace(haystack_value, pint_value)
    return unit


def define_haystack_units() -> UnitRegistry:
    """Missing units found in project-haystack Added to the registry"""
    unit_ureg = UnitRegistry(on_redefinition='ignore')
    unit_ureg.define('% = [] = percent')
    unit_ureg.define('pixel = [] = px = dot = picture_element = pel')
    unit_ureg.define('decibel = [] = dB')
    unit_ureg.define('ppu = [] = parts_per_unit')
    unit_ureg.define('ppm = [] = parts_per_million')
    unit_ureg.define('ppb = [] = parts_per_billion')
    unit_ureg.define('%RH = [] = percent_relative_humidity = percentRH')
    unit_ureg.define('cubic_feet = ft ** 3 = cu_ft')
    unit_ureg.define('cfm = cu_ft * minute = liter_per_second / 0.4719475')
    unit_ureg.define('cfh = cu_ft * hour')
    unit_ureg.define('cfs = cu_ft * second')
    unit_ureg.define('VAR = volt * ampere')
    unit_ureg.define('kVAR = 1000 * volt * ampere')
    unit_ureg.define('MVAR = 1000000 * volt * ampere')
    unit_ureg.define('inH2O = in_H2O')
    unit_ureg.define('dry_air = []')
    unit_ureg.define('gas = []')
    unit_ureg.define('energy_efficiency_ratio = [] = EER')
    unit_ureg.define('coefficient_of_performance = [] = COP')
    unit_ureg.define('data_center_infrastructure_efficiency = [] = DCIE')
    unit_ureg.define('power_usage_effectiveness = [] = PUE')
    unit_ureg.define('formazin_nephelometric_unit = [] = fnu')
    unit_ureg.define('nephelometric_turbidity_units = [] = ntu')
    unit_ureg.define('power_factor = [] = PF')
    unit_ureg.define('degree_day_celsius = [] = degdaysC')
    unit_ureg.define('degree_day_farenheit = degree_day_celsius * 9 / 5 = degdaysF')
    unit_ureg.define('footcandle = lumen / sq_ft = ftcd')
    unit_ureg.define('Nm = newton * meter')
    unit_ureg.define('%obsc = [] = percent_obscuration = percentobsc')
    unit_ureg.define('cycle = []')
    unit_ureg.define('cph = cycle / hour')
    unit_ureg.define('cpm = cycle / minute')
    unit_ureg.define('cps = cycle / second')
    unit_ureg.define('hecto_cubic_foot = 100 * cubic_foot')
    unit_ureg.define('tenths_second = second / 10')
    unit_ureg.define('hundredths_second = second / 100')

    # ureg.define('irradiance = W / sq_meter = irr')
    # In the definition of project haystack, there's a redundancy as irr = W/m^2
    # no need to use : watts_per_square_meter_irradiance

    # CURRENCY
    # I know...we won'T be able to convert right now !
    unit_ureg.define('australian_dollar = [] = AUD')
    unit_ureg.define('british_pound = [] = GBP = £')
    unit_ureg.define('canadian_dollar = [] = CAD')
    unit_ureg.define('chinese_yuan = [] = CNY = 元')
    unit_ureg.define('emerati_dirham = [] = AED')
    unit_ureg.define('euro = [] = EUR = €')
    unit_ureg.define('indian_rupee = [] = INR = ₹')
    unit_ureg.define('japanese_yen = [] = JPY = ¥')
    unit_ureg.define('russian_ruble = [] = RUB = руб')
    unit_ureg.define('south_korean_won = [] = KRW = ₩')
    unit_ureg.define('swedish_krona = [] = SEK = kr')
    unit_ureg.define('swiss_franc = [] = CHF = Fr')
    unit_ureg.define('taiwan_dollar = [] = TWD')
    unit_ureg.define('us_dollar = [] = USD = $')
    unit_ureg.define('new_israeli_shekel = [] = NIS')

    # See https://pint.readthedocs.io/en/stable/defining.html

    return unit_ureg


unit_reg = define_haystack_units()
