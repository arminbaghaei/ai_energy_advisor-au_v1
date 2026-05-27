"""Recommendation rules for EnergyWise Homes Australia."""
from __future__ import annotations

import json
from pathlib import Path
from typing import Dict, List, Tuple


ROOT = Path(__file__).resolve().parents[1]
ACTIONS_PATH = ROOT / "data" / "actions.json"


def load_actions() -> Dict[str, dict]:
    with open(ACTIONS_PATH, "r", encoding="utf-8") as f:
        return json.load(f)


def score_label(score: int) -> str:
    if score <= 40:
        return "High energy waste"
    if score <= 65:
        return "Some good choices, but major savings missed"
    if score <= 85:
        return "Good energy-saving plan"
    return "Excellent EnergyWise home inspection"


def bill_problem_priority(bill_problem: str) -> List[str]:
    mapping = {
        "High winter bill": ["thermostat", "draught_sealing", "curtains", "insulation_owner", "insulation_renter"],
        "High summer bill": ["thermostat", "curtains", "draught_sealing", "insulation_owner", "insulation_renter"],
        "High hot-water bill": ["shorter_showers", "efficient_showerhead"],
        "Not sure": ["thermostat", "shorter_showers", "leds", "standby"],
    }
    return mapping.get(bill_problem, mapping["Not sure"])


def tenure_filter(action_key: str, tenure_type: str) -> bool:
    if tenure_type == "Rented" and action_key == "insulation_owner":
        return False
    if tenure_type == "Owned" and action_key == "insulation_renter":
        return False
    return True


def generate_ranked_actions(
    selected_action_keys: List[str],
    tenure_type: str,
    bill_problem: str,
    solar_status: str,
) -> List[Tuple[str, dict]]:
    actions = load_actions()
    keys = list(dict.fromkeys(selected_action_keys))

    # Add sensible missing actions based on user profile.
    for key in bill_problem_priority(bill_problem):
        if key not in keys:
            keys.append(key)
    if tenure_type == "Rented" and "insulation_renter" not in keys:
        keys.append("insulation_renter")
    if tenure_type == "Owned" and "insulation_owner" not in keys:
        keys.append("insulation_owner")
    if solar_status in ["No", "Not sure"] and tenure_type == "Owned":
        keys.append("solar_after_efficiency")

    filtered = [k for k in keys if k in actions and tenure_filter(k, tenure_type)]
    ranked = sorted([(k, actions[k]) for k in filtered], key=lambda item: item[1]["priority"])
    return ranked


def top_three_actions(ranked_actions: List[Tuple[str, dict]]) -> List[Tuple[str, dict]]:
    return ranked_actions[:3]
