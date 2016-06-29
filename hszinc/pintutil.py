#!/usr/bin/python
# -*- coding: utf-8 -*-
# Pint integration helpers
# (C) 2016 VRT Systems
#

from __future__ import unicode_literals
from pint import UnitRegistry

HAYSTACK_CONVERSION = [
                    ('_', ' '),
                    ('°','deg'),
                    ('per ', '/ '),
                    ('per_h','per_hour'),
                    ('Δ','delta_'),
                    ('meters','meter'),
                    ('liters','liter'),
                    ('gallons','gallon'),
                    ('millimeters','millimeter'),
                    ('centimeters','centimeter'),
                    ('H₂O', 'H2O'),
                    ('Volt', 'volt'),
                    ('grams', 'gram'),
                    ('tons refrigeration', 'refrigeration_ton'),
                    ('%', 'percent'),
                    ('degree kelvin','degK'),
                    ('degree celsius','degC'),
                    ('degree farenheit','degF'),
                    ('pound force', 'pound_force'),
                    ('metric ton', 'metric_ton'),
                    ('fluid ounce', 'fluid_ounce'),
                    ('imperial gallon','imperial_gallon'),
                    ('galUK','UK_gallon'),
                    ('kgdegK','(kg degK)'),
                    ('tonrefh','refrigeration_ton * hour'),
                    ('tonref','refrigeration_ton'),
                    ('Nm ', 'newton meter'),
                    ('Ns', 'newton second'),
                    ('Js', 'joule second'),
                    ('short ton', 'short_ton'),
                    ('degrees angular', 'deg'),
                    ('degrees phase', 'deg'),
                    ('degPh', 'deg'),
                    ('yr','year '),
                    ('atmosphere', 'atm'),
                    ('mo','month '),
                    ('wk','week '),
                    ('parts / unit','ppu'),
                    ('parts / million','ppm'),
                    ('parts / billion','ppb'),
                    ('kcfm','kilocfm'),
                    ('kilohm','kiloohm'),
                    ('megohm','megaohm'),
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
                    ('db','dB'),
                    ('Am', 'A * m'),
                    ('percent relative humidity', 'percentRH'),
                    ('pf', 'PF'),
                    ('power factor', 'PF'),
                    ('gH2O','g H2O'),
                    ('irradiance',''),
                    ('irr',''),
                    ('dry air', 'dry'),
                    ('dry', 'dry_air'),
                    ('kgAir','kg dry_air'),
                    ('percent obscuration', 'percentobsc'),
                    ('natural gas', ''),
                    ('Ωm', 'ohm meter'),
                    ('hecto cubic foot', 'hecto_cubic_foot'),
                    ('julian month','month'),
                    ('tenths second', 'tenths_second'),
                    ('hundredths second', 'hundredths_second'),
                    ('australian dollar','australian_dollar'),
                    ('british pound','british_pound'),
                    ('canadian dollar','canadian_dollar'),
                    ('chinese yuan','chinese_yuan'),
                    ('emerati dirham','emerati_dirham'),
                    ('indian rupee','indian_rupee'),
                    ('japanese yen','japanese_yen'),
                    ('russian ruble','russian_ruble'),
                    ('south korean won','south_korean_won'),
                    ('swedish krona','swedish_krona'),
                    ('swiss franc','swiss_franc'),
                    ('taiwan dollar','taiwan_dollar'),
                    ('us dollar','us_dollar'),
                    ('new israeli shekel','new_israeli_shekel'),
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
                    ('of','')
                    ]
                    
PINT_CONVERSION = [
                    ('foot ** 3', 'cubic_foot'),
                    ('/','per'),
                    ('hectofoot ** 3','hecto_cubic_foot'),
                    ('meter ** 3','cubic_meter'),
                    ('Volt_per','volts_per'),
                    ('°ree','degree')
]

def to_haystack(unit):
    """
    Some parsing tweaks to fit pint units / handling of edge cases.
    """
    unit = str(unit)
    global HAYSTACK_CONVERSION
    global PINT_CONVERSION
    if unit == 'per_minute' or \
        unit == '/min' or \
        unit == 'per_second' or \
        unit == '/s' or \
        unit == 'per_hour' or \
        unit == '/h' or \
        unit == None:
        return ''
        # Those units are not units... they are impossible to fit anywhere in Pint
    
    for pint_value, haystack_value in PINT_CONVERSION:
        unit = unit.replace(pint_value, haystack_value)
    for haystack_value, pint_value in HAYSTACK_CONVERSION:
        if pint_value == '':
            continue
        unit = unit.replace(pint_value, haystack_value)
    return unit

def to_pint(unit):
    """
    Some parsing tweaks to fit pint units / handling of edge cases.
    """
    global HAYSTACK_CONVERSION
    if unit == 'per_minute' or \
        unit == '/min' or \
        unit == 'per_second' or \
        unit == '/s' or \
        unit == 'per_hour' or \
        unit == '/h' or \
        unit == None:
        return ''
        # Those units are not units... they are impossible to fit anywhere in Pint
    for haystack_value, pint_value in HAYSTACK_CONVERSION:
        unit = unit.replace(haystack_value, pint_value)
    return unit

                
def define_haystack_units():
    """
    Missing units found in project-haystack
    Added to the registry
    """
    ureg = UnitRegistry()
    ureg.define('% = [] = percent')
    ureg.define('pixel = [] = px = dot = picture_element = pel')
    ureg.define('decibel = [] = dB')
    ureg.define('ppu = [] = parts_per_unit')
    ureg.define('ppm = [] = parts_per_million')
    ureg.define('ppb = [] = parts_per_billion')
    ureg.define('%RH = [] = percent_relative_humidity = percentRH')
    ureg.define('cubic_feet = ft ** 3 = cu_ft')
    ureg.define('cfm = cu_ft * minute = liter_per_second / 0.4719475')
    ureg.define('cfh = cu_ft * hour')
    ureg.define('cfs = cu_ft * second')
    ureg.define('VAR = volt * ampere')
    ureg.define('kVAR = 1000 * volt * ampere')
    ureg.define('MVAR = 1000000 * volt * ampere')
    ureg.define('inH2O = in_H2O')
    ureg.define('dry_air = []')
    ureg.define('gas = []')
    ureg.define('energy_efficiency_ratio = [] = EER')
    ureg.define('coefficient_of_performance = [] = COP')
    ureg.define('data_center_infrastructure_efficiency = [] = DCIE')
    ureg.define('power_usage_effectiveness = [] = PUE')
    ureg.define('formazin_nephelometric_unit = [] = fnu')
    ureg.define('nephelometric_turbidity_units = [] = ntu')
    ureg.define('power_factor = [] = PF')
    ureg.define('degree_day_celsius = [] = degdaysC')
    ureg.define('degree_day_farenheit = degree_day_celsius * 9 / 5 = degdaysF')
    ureg.define('footcandle = lumen / sq_ft = ftcd')
    ureg.define('Nm = newton * meter')
    ureg.define('%obsc = [] = percent_obscuration = percentobsc')
    ureg.define('cycle = []')
    ureg.define('cph = cycle / hour')
    ureg.define('cpm = cycle / minute')
    ureg.define('cps = cycle / second')
    ureg.define('hecto_cubic_foot = 100 * cubic_foot')
    ureg.define('tenths_second = second / 10')
    ureg.define('hundredths_second = second / 100')

    #ureg.define('irradiance = W / sq_meter = irr')
    # In the definition of project haystack, there's a redundancy as irr = W/m^2
    # no need to use : watts_per_square_meter_irradiance
    
    # CURRENCY
    # I know...we won'T be able to convert right now !
    ureg.define('australian_dollar = [] = AUD')
    ureg.define('british_pound = [] = GBP = £')
    ureg.define('canadian_dollar = [] = CAD')
    ureg.define('chinese_yuan = [] = CNY = 元')
    ureg.define('emerati_dirham = [] = AED')
    ureg.define('euro = [] = EUR = €')
    ureg.define('indian_rupee = [] = INR = ₹')
    ureg.define('japanese_yen = [] = JPY = ¥')
    ureg.define('russian_ruble = [] = RUB = руб')
    ureg.define('south_korean_won = [] = KRW = ₩')
    ureg.define('swedish_krona = [] = SEK = kr')
    ureg.define('swiss_franc = [] = CHF = Fr')
    ureg.define('taiwan_dollar = [] = TWD')
    ureg.define('us_dollar = [] = USD = $')
    ureg.define('new_israeli_shekel = [] = NIS')

    return ureg
