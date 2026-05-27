"""Conservative household energy-saving estimators for EnergyWise Homes Australia.

The functions intentionally use simple assumptions because the first public prototype is
not a certified energy-audit tool. The user interface should label results as indicative.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, Tuple


ELECTRICITY_PRICE_AUD_PER_KWH = 0.35  # editable default; users can override in Streamlit
GAS_PRICE_AUD_PER_KWH = 0.12          # approximate default for gas-equivalent calculations
LITRES_PER_MIN_STANDARD_SHOWER = 9.0
LITRES_PER_MIN_EFFICIENT_SHOWER = 6.0
KWH_PER_LITRE_HOT_WATER = 0.058       # approx. raising water by ~50C including system losses


@dataclass(frozen=True)
class HouseholdInputs:
    household_size: str
    tenure_type: str
    bill_problem: str
    hvac_type: str
    solar_status: str
    monthly_bill_aud: float
    electricity_price: float
    shower_minutes_current: int
    shower_minutes_target: int
    showers_per_person_per_day: float
    old_bulbs: int
    hours_per_bulb_per_day: float
    standby_devices: int
    thermostat_degrees_improved: int


def household_multiplier(size: str) -> float:
    return {
        "1": 1.0,
        "2": 1.7,
        "3-4": 3.2,
        "5+": 5.0,
    }.get(size, 2.0)


def monthly_to_annual_bill(monthly_bill_aud: float) -> float:
    return max(monthly_bill_aud, 0) * 12


def estimate_thermostat_saving(annual_bill: float, degrees_improved: int) -> Tuple[float, float]:
    """Return conservative low/high annual AUD savings from thermostat improvement.

    Assumption: heating/cooling portion is 30% of annual bill and each degree saves 5-10%
    of that portion. The app exposes this as indicative only.
    """
    heating_cooling_share = 0.30
    low = annual_bill * heating_cooling_share * 0.05 * max(degrees_improved, 0)
    high = annual_bill * heating_cooling_share * 0.10 * max(degrees_improved, 0)
    return round(low, 0), round(high, 0)


def estimate_shower_time_saving(inputs: HouseholdInputs) -> Tuple[float, float]:
    people = household_multiplier(inputs.household_size)
    minutes_saved = max(inputs.shower_minutes_current - inputs.shower_minutes_target, 0)
    litres_saved_per_year = minutes_saved * LITRES_PER_MIN_STANDARD_SHOWER * inputs.showers_per_person_per_day * people * 365
    kwh_saved = litres_saved_per_year * KWH_PER_LITRE_HOT_WATER
    aud = kwh_saved * inputs.electricity_price
    return round(aud * 0.75, 0), round(aud * 1.10, 0)


def estimate_showerhead_saving(inputs: HouseholdInputs) -> Tuple[float, float]:
    people = household_multiplier(inputs.household_size)
    flow_saved = max(LITRES_PER_MIN_STANDARD_SHOWER - LITRES_PER_MIN_EFFICIENT_SHOWER, 0)
    litres_saved_per_year = flow_saved * inputs.shower_minutes_target * inputs.showers_per_person_per_day * people * 365
    kwh_saved = litres_saved_per_year * KWH_PER_LITRE_HOT_WATER
    aud = kwh_saved * inputs.electricity_price
    return round(aud * 0.65, 0), round(aud, 0)


def estimate_led_saving(inputs: HouseholdInputs) -> Tuple[float, float]:
    # halogen 50W to LED 8W = 42W saved per bulb-hour
    watts_saved = 42
    kwh_saved = inputs.old_bulbs * inputs.hours_per_bulb_per_day * watts_saved / 1000 * 365
    aud = kwh_saved * inputs.electricity_price
    return round(aud * 0.85, 0), round(aud * 1.05, 0)


def estimate_standby_saving(inputs: HouseholdInputs) -> Tuple[float, float]:
    # Conservative standby assumption: 2-5W avoidable per device for 20 hours/day
    low_kwh = inputs.standby_devices * 2 / 1000 * 20 * 365
    high_kwh = inputs.standby_devices * 5 / 1000 * 20 * 365
    return round(low_kwh * inputs.electricity_price, 0), round(high_kwh * inputs.electricity_price, 0)


def estimate_all_savings(inputs: HouseholdInputs) -> Dict[str, Tuple[float, float]]:
    annual_bill = monthly_to_annual_bill(inputs.monthly_bill_aud)
    return {
        "thermostat": estimate_thermostat_saving(annual_bill, inputs.thermostat_degrees_improved),
        "shorter_showers": estimate_shower_time_saving(inputs),
        "efficient_showerhead": estimate_showerhead_saving(inputs),
        "leds": estimate_led_saving(inputs),
        "standby": estimate_standby_saving(inputs),
    }


def format_saving_range(value: Tuple[float, float]) -> str:
    low, high = value
    if high <= 0:
        return "Not enough change to estimate a saving"
    if abs(high - low) < 1:
        return f"About A${high:,.0f}/year"
    return f"A${low:,.0f}–A${high:,.0f}/year"
