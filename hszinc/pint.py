#!/usr/bin/python
# -*- coding: utf-8 -*-
# Zinc data types
# (C) 2016 VRT Systems
#

import pkg_resources, os
from pint import UnitRegistry

def define_registry():
    """
    This doesn't work.... not been able to import file into ureg...
    I'll try defining units manually...
    """
    resource_package = __name__
    main_unit_path = os.path.join('units', 'pyhaystack_pint.txt')
    add_on_path = os.path.join('', 'pyhaystack_addons.txt')
    addons = pkg_resources.resource_string(resource_package, add_on_path)
    units = pkg_resources.resource_string(resource_package, main_unit_path)
    #print(addons)    
    
def to_pint(unit):
    """
    Some parsing tweaks to fit pint units / handling of edge cases.
    """
    if unit == 'per_minute' or \
        unit == '/min' or \
        unit == 'per_second' or \
        unit == '/s' or \
        unit == 'per_hour' or \
        unit == '/h':
        return ''
        # Those units are not units... they are impossible to fit anywhere in Pint
        
    return unit.replace('_', ' ') \
                .replace('°','deg') \
                .replace('per ', '/ ') \
                .replace('Δ','delta_') \
                .replace('meters','meter') \
                .replace('liters','liter') \
                .replace('gallons','gallon') \
                .replace('millimeters','millimeter') \
                .replace('centimeters','centimeter') \
                .replace('H₂O', 'H2O') \
                .replace('Volt', 'volt') \
                .replace('grams', 'gram') \
                .replace('tons refrigeration', 'refrigeration_ton') \
                .replace('%', 'percent') \
                .replace('degree kelvin','degK') \
                .replace('degree celsius','degC') \
                .replace('degree farenheit','degF') \
                .replace('pound force', 'pound_force') \
                .replace('metric ton', 'metric_ton') \
                .replace('fluid ounce', 'fluid_ounce') \
                .replace('imperial gallon','imperial_gallon') \
                .replace('galUK','UK_gallon') \
                .replace('kgdegK','(kg degK)') \
                .replace('tonrefh','refrigeration_ton * hour') \
                .replace('tonref','refrigeration_ton') \
                .replace('Nm ', 'newton meter') \
                .replace('Ns', 'newton second') \
                .replace('Js', 'joule second') \
                .replace('short ton', 'short_ton') \
                .replace('degrees angular', 'deg') \
                .replace('degrees phase', 'deg') \
                .replace('degPh', 'deg') \
                .replace('yr','year ') \
                .replace('atmosphere', 'atm') \
                .replace('mo','month ') \
                .replace('wk','week ') \
                .replace('parts / unit','ppu') \
                .replace('parts / million','ppm') \
                .replace('parts / billion','ppb') \
                .replace('kcfm','kilocfm') \
                .replace('kilohm','kiloohm') \
                .replace('megohm','megaohm') \
                .replace('volt ampere reactive', 'VAR') \
                .replace('kilovolt ampere reactive', 'kVAR') \
                .replace('megavolt ampere reactive', 'MVAR') \
                .replace('VAh', 'volt * ampere * hour') \
                .replace('kVAh', 'kilovolt * ampere * hour') \
                .replace('MVAh', 'megavolt * ampere * hour') \
                .replace('VARh', 'VAR * hour') \
                .replace('kVARh', 'kVAR * hour') \
                .replace('MVARh', 'MVAR * hour') \
                .replace('hph', 'horsepower * hour') \
                .replace('energy efficiency ratio', 'EER') \
                .replace('coefficient of performance', 'COP') \
                .replace('data center infrastructure efficiency', 'DCIE') \
                .replace('power usage effectiveness', 'PUE') \
                .replace('formazin nephelometric unit', 'fnu') \
                .replace('nephelometric turbidity units', 'ntu') \
                .replace('dBµV', 'dB microvolt') \
                .replace('dBmV', 'dB millivolt') \
                .replace('Am', 'A * m') \
                .replace('percent relative humidity', 'percentRH') \
                .replace('pf', 'PF') \
                .replace('power factor', 'PF') \
                .replace('gH2O','g H2O') \
                .replace('irradiance','') \
                .replace('irr','') \
                .replace('dry air', 'dry') \
                .replace('dry', 'dry_air') \
                .replace('kgAir','kg dry_air') \
                .replace('percent obscuration', 'percentobsc') \
                .replace('natural gas', '') \
                .replace('Ωm', 'ohm meter') \
                .replace('hecto cubic foot', 'hecto_cubic_foot') \
                .replace('julian month','month') \
                .replace('tenths second', 'tenths_second') \
                .replace('hundredths second', 'hundredths_second') \
                .replace('australian dollar','australian_dollar') \
                .replace('british pound','british_pound') \
                .replace('canadian dollar','canadian_dollar') \
                .replace('chinese yuan','chinese_yuan') \
                .replace('emerati dirham','emerati_dirham') \
                .replace('indian rupee','indian_rupee') \
                .replace('japanese yen','japanese_yen') \
                .replace('russian ruble','russian_ruble') \
                .replace('south korean won','south_korean_won') \
                .replace('swedish krona','swedish_krona') \
                .replace('swiss franc','swiss_franc') \
                .replace('taiwan dollar','taiwan_dollar') \
                .replace('us dollar','us_dollar') \
                .replace('new israeli shekel','new_israeli_shekel') \
                .replace('delta_K', 'delta_degC') \
                .replace('delta degK', 'delta_degC') \
                .replace('delta degC', 'delta_degC') \
                .replace('delta degF', 'delta_degF') \
                .replace('of','')
                
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
    ureg.define('cfm = cu_ft * minute')
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