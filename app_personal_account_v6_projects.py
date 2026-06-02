from __future__ import annotations

from pathlib import Path
import base64
import json
from datetime import date, datetime
from io import BytesIO
import textwrap
from urllib.parse import quote_plus

import pandas as pd
from PIL import Image, ImageDraw, ImageFont
import plotly.graph_objects as go
import streamlit as st
from streamlit_gsheets import GSheetsConnection
from logic.calculations import HouseholdInputs, estimate_all_savings, format_saving_range
from logic.recommendations import generate_ranked_actions, score_label, top_three_actions


APP_TITLE = "The Home-energy check-up (Australia)"
TAGLINE = "A practical home-energy check-up for Australian households"
ROOT = Path(__file__).parent
LOGO_PATH = ROOT / "assets" / "company_logo.png"
APP_PUBLIC_URL = "https://your-streamlit-app-url-here"  # Replace with your deployed Streamlit URL for social sharing.


st.set_page_config(
    page_title=APP_TITLE,
    page_icon="🏡",
    layout="wide",
    initial_sidebar_state="expanded",
)


CUSTOM_CSS = """
<style>
.block-container {
    padding-top: 1.4rem;
    padding-bottom: 3rem;
    max-width: 1080px;
    margin-left: auto;
    margin-right: auto;
}
.header-grid {
    display: grid;
    grid-template-columns: minmax(0, 1fr) 210px;
    gap: 1.35rem;
    align-items: stretch;
    margin: 0 auto 1rem auto;
}
.hero {
    padding: 2rem;
    border-radius: 24px;
    background: linear-gradient(135deg, #0F766E 0%, #0EA5E9 100%);
    color: white;
    min-height: 210px;
}
.hero h1 {font-size: 2.35rem; margin-bottom: 0.3rem; letter-spacing: -0.02em;}
.hero p {font-size: 1.05rem; opacity: 0.96;}
.logo-card {
    min-height: 210px;
    background: transparent;
    display: flex;
    flex-direction: column;
    align-items: center;
    justify-content: center;
    padding: 0.5rem 0.25rem;
    text-align: center;
}
.logo-card img {
    width: 105px;
    max-width: 90%;
    height: auto;
    object-fit: contain;
    display: block;
}

.company-name {
    margin-top: 0.65rem;
    font-weight: 700;
    color: #0F172A;
    font-size: 0.95rem;
    line-height: 1.25;
}
.company-tagline {
    margin-top: 0.18rem;
    color: #475569;
    font-size: 0.78rem;
    line-height: 1.25;
}
.company-email {
    margin-top: 0.4rem;
    color: #0F766E;
    font-size: 0.80rem;
    font-weight: 600;
}

.sidebar-brand {
    margin-top: 2rem;
    padding-top: 1rem;
    border-top: 1px solid #E2E8F0;
    text-align: center;
}
.sidebar-brand img {
    width: 58px;
    max-width: 70%;
    height: auto;
    object-fit: contain;
    margin: 0 auto 0.45rem auto;
    display: block;
}
.sidebar-brand-title {
    font-size: 0.78rem;
    font-weight: 700;
    color: #0F172A;
    line-height: 1.2;
}
.sidebar-brand-text {
    font-size: 0.68rem;
    color: #64748B;
    line-height: 1.2;
    margin-top: 0.15rem;
}
.feedback-correct {
    padding: 0.9rem;
    border-radius: 14px;
    background:#ECFDF5;
    border:1px solid #A7F3D0;
    color:#065F46;
    margin-top: 0.75rem;
}
.feedback-wrong {
    padding: 0.9rem;
    border-radius: 14px;
    background:#FFFBEB;
    border:1px solid #FDE68A;
    color:#92400E;
    margin-top: 0.75rem;
}
.feedback-answer {
    margin-top: 0.35rem;
    font-size: 0.90rem;
    color: #334155;
}

.logo-placeholder {
    text-align: center;
    color: #64748B;
    font-size: 0.92rem;
}
.card {
    padding: 1.1rem; border-radius: 18px; background: white;
    border: 1px solid #E2E8F0; box-shadow: 0 1px 4px rgba(15, 23, 42, 0.06);
    min-height: 145px;
}
.compliance-strip {
    display: flex;
    align-items: center;
    gap: 0.65rem;
    padding: 0.85rem 1rem;
    border-radius: 16px;
    background: #F8FAFC;
    border: 1px solid #CBD5E1;
    color: #334155;
    margin: 0.25rem 0 1rem 0;
    font-size: 0.94rem;
}
.compliance-icon {
    width: 34px;
    height: 34px;
    min-width: 34px;
    border-radius: 10px;
    background: #0F766E;
    color: white;
    display: flex;
    align-items: center;
    justify-content: center;
    font-weight: 700;
}
.small-muted {color: #64748B; font-size: 0.92rem;}
.badge {display: inline-block; padding: 0.2rem 0.55rem; border-radius: 999px; background:#ECFDF5; color:#047857; font-size:0.82rem; font-weight:600;}
.warning-box {padding: 1rem; border-radius: 16px; background:#FFFBEB; border:1px solid #FDE68A; color:#92400E;}
.success-box {padding: 1rem; border-radius: 16px; background:#ECFDF5; border:1px solid #A7F3D0; color:#065F46;}

.certificate-card {
    position: relative;
    overflow: hidden;
    width: min(100%, 760px);
    aspect-ratio: 1 / 1;
    margin: 1.25rem auto 0 auto;
    padding: clamp(1.6rem, 4vw, 2.35rem);
    border-radius: 28px;
    background:
        radial-gradient(circle at top left, rgba(14,165,233,0.16), transparent 34%),
        radial-gradient(circle at bottom right, rgba(15,118,110,0.15), transparent 35%),
        linear-gradient(135deg, #FFFFFF 0%, #F8FAFC 100%);
    border: 1px solid #99F6E4;
    box-shadow: 0 18px 45px rgba(15, 23, 42, 0.12);
    text-align: center;
    display:flex;
    flex-direction:column;
    justify-content:center;
}
.certificate-card::before {
    content: "";
    position: absolute;
    inset: 18px;
    border: 2px solid #0F766E;
    border-radius: 22px;
    pointer-events: none;
}
.certificate-card::after {
    content: "Recognition";
    position: absolute;
    top: 42px;
    right: -60px;
    transform: rotate(45deg);
    background: #0F766E;
    color: #FFFFFF;
    padding: 0.42rem 4.6rem;
    font-size: 0.74rem;
    font-weight: 900;
    letter-spacing: 0.08em;
    text-transform: uppercase;
    box-shadow: 0 8px 18px rgba(15, 23, 42, 0.18);
    z-index: 2;
}
.certificate-kicker {font-size: 0.78rem; color:#0F766E; font-weight:800; letter-spacing:0.12em; text-transform:uppercase;}
.certificate-title {font-size: clamp(1.8rem, 4vw, 2.35rem); font-weight: 900; color: #0F172A; margin: 0.4rem 0 0.2rem 0; letter-spacing: -0.02em;}
.certificate-subtitle {font-size: 1rem; color: #475569; margin-bottom: 0.45rem;}
.certificate-company {font-size: 0.92rem; color:#0F766E; font-weight:800; margin-bottom:1.1rem;}
.certificate-name {font-size: clamp(1.65rem, 4vw, 2.15rem); font-weight: 900; color: #0F766E; margin: 0.75rem auto; padding-bottom:0.42rem; border-bottom: 2px solid #99F6E4; max-width: 560px;}
.certificate-small {font-size: 0.94rem; color: #334155; line-height: 1.55; max-width:620px; margin-left:auto; margin-right:auto;}
.certificate-meta {display:flex; justify-content:center; gap:0.65rem; flex-wrap:wrap; margin-top:1rem;}
.certificate-pill {padding:0.45rem 0.75rem; border-radius:999px; background:#ECFDF5; border:1px solid #A7F3D0; color:#065F46; font-weight:700; font-size:0.82rem;}
.certificate-footer {margin-top:1.15rem; font-size:0.82rem; color:#475569;}
.certificate-disclaimer {font-size:0.75rem; color:#64748B; margin-top:0.75rem;}
.share-row {display: flex; gap: 0.55rem; flex-wrap: wrap; margin-top: 0.75rem;}
.share-button {
    display: inline-flex; align-items: center; justify-content: center; min-width: 95px;
    padding: 0.55rem 0.75rem; border-radius: 999px; background: #0F172A;
    color: white !important; text-decoration: none !important; font-weight: 700; font-size: 0.86rem;
}
.share-button:hover { opacity: 0.88; }

@media (max-width: 760px) {
    .header-grid {grid-template-columns: 1fr;}
    .logo-card {min-height: 120px;}
    .logo-card img {width: 115px;}
}

.money-hero {
    padding: 1.6rem;
    border-radius: 24px;
    background: linear-gradient(135deg, #111827 0%, #0F766E 100%);
    color: white;
    margin: 1rem 0;
    box-shadow: 0 10px 30px rgba(15, 23, 42, 0.16);
}
.money-hero h2 {font-size: 2rem; margin: 0 0 0.5rem 0; letter-spacing: -0.02em;}
.money-hero p {font-size: 1rem; opacity: 0.95; margin-bottom: 0.4rem;}
.money-number {font-size: 2.35rem; font-weight: 900; line-height: 1.05; margin: 0.5rem 0;}
.money-sub {font-size: 0.88rem; opacity: 0.85;}
.money-card {
    padding: 1.15rem;
    border-radius: 18px;
    border: 1px solid #A7F3D0;
    background: #ECFDF5;
    min-height: 135px;
}
.money-card h4 {margin:0 0 0.35rem 0; color:#064E3B;}
.money-card .value {font-size:1.65rem; font-weight:900; color:#065F46; margin:0.2rem 0;}
.money-card p {color:#334155; font-size:0.92rem; margin-bottom:0;}
.unlock-card {
    padding: 1.05rem;
    border-radius: 18px;
    border: 1px solid #E2E8F0;
    background: #FFFFFF;
    box-shadow: 0 1px 5px rgba(15,23,42,0.06);
}
.unlock-badge {display:inline-block; padding:0.22rem 0.55rem; border-radius:999px; background:#F1F5F9; color:#334155; font-size:0.78rem; font-weight:700;}
.pathway-step {
    padding: 1rem;
    border-left: 5px solid #0F766E;
    background: #F8FAFC;
    border-radius: 14px;
    margin-bottom: 0.75rem;
}
.pathway-step h4 {margin: 0 0 0.25rem 0; color:#0F172A;}
.pathway-step p {margin: 0.2rem 0; color:#334155;}

</style>
"""
st.markdown(CUSTOM_CSS, unsafe_allow_html=True)


# ---------- Session state ----------
def initialise_state() -> None:
    defaults = {
        "stage": "welcome",
        "score": 0,
        "completed_hotspots": set(),
        "selected_actions": [],
        "bill_risk": 60,
        "comfort": 45,
        "last_feedback": {},
        "participant_id": "Anonymous Participant",
        "response_saved": False,
    }
    for key, value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value


def reset_app() -> None:
    for key in list(st.session_state.keys()):
        del st.session_state[key]
    initialise_state()


initialise_state()


# ---------- Google Sheets response storage ----------
def get_next_participant_id(conn) -> str:
    """Generate a simple anonymous participant ID based on the next available sheet row."""
    try:
        existing_data = conn.read(ttl=0)
        if existing_data is None or existing_data.empty:
            return "Participant 1"
        return f"Participant {len(existing_data) + 1}"
    except Exception:
        return "Participant 1"


def save_response_to_gsheet(submission: dict) -> None:
    """Append one anonymous completed response to the connected Google Sheet."""
    conn = st.connection("gsheets", type=GSheetsConnection)
    existing_data = conn.read(ttl=0)
    new_row = pd.DataFrame([submission])

    if existing_data is None or existing_data.empty:
        updated_data = new_row
    else:
        updated_data = pd.concat([existing_data, new_row], ignore_index=True)

    conn.update(data=updated_data)


def build_anonymous_submission(participant_id: str, savings: dict, ranked_actions: list, result_text: str) -> dict:
    """Build the row saved to Google Sheets. No name, email, or contact details are collected."""
    total_low = int(sum(v[0] for v in savings.values() if isinstance(v, tuple)))
    total_high = int(sum(v[1] for v in savings.values() if isinstance(v, tuple)))
    action_titles = [action.get("title", key) for key, action in ranked_actions]

    return {
        "participant_id": participant_id,
        "submission_time": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "household_size": st.session_state.get("household_size", ""),
        "tenure_type": st.session_state.get("tenure_type", ""),
        "bill_problem": st.session_state.get("bill_problem", ""),
        "dwelling_type": st.session_state.get("dwelling_type", ""),
        "home_condition": st.session_state.get("home_condition", ""),
        "hvac_type": st.session_state.get("hvac_type", ""),
        "solar_status": st.session_state.get("solar_status", ""),
        "thermostat_answer": st.session_state.get("thermostat_answer", ""),
        "thermostat_correct": st.session_state.get("thermostat_correct", ""),
        "lighting_answer": st.session_state.get("leds_answer", ""),
        "lighting_correct": st.session_state.get("leds_correct", ""),
        "curtains_answer": st.session_state.get("curtains_answer", ""),
        "curtains_correct": st.session_state.get("curtains_correct", ""),
        "draught_answer": st.session_state.get("draught_answer", ""),
        "draught_correct": st.session_state.get("draught_correct", ""),
        "shower_answer": st.session_state.get("shower_answer", ""),
        "shower_correct": st.session_state.get("shower_correct", ""),
        "standby_answer": st.session_state.get("standby_answer", ""),
        "standby_correct": st.session_state.get("standby_correct", ""),
        "insulation_answer": st.session_state.get("insulation_answer", ""),
        "insulation_correct": st.session_state.get("insulation_correct", ""),
        "score": st.session_state.get("score", ""),
        "result_category": result_text,
        "estimated_annual_savings": f"A${total_low:,}–A${total_high:,}",
        "money_first_snapshot": str(st.session_state.get("money_snapshot", {})),
        "selected_actions": "; ".join(action_titles),
        "consent_given": True,
    }


# ---------- Data ----------
HOTSPOTS = {
    "thermostat": {
        "label": "Air-conditioner / heater remote",
        "room": "Living room",
        "question": "Which setting is usually more energy-smart?",
        "options": [
            "Cooling at 18°C in summer",
            "Cooling around 25–27°C in summer",
            "Heating at 26°C in winter",
        ],
        "correct": "Cooling around 25–27°C in summer",
        "points": 15,
        "action": "thermostat",
        "correct_feedback": "Correct. Moderate thermostat settings reduce the workload on heating and cooling systems.",
        "wrong_feedback": "Not ideal. Extreme thermostat settings increase energy use. Aim for around 18–20°C for heating and 25–27°C for cooling.",
    },
    "leds": {
        "label": "Old light bulb",
        "room": "Living room / hallway",
        "question": "What should this household do first?",
        "options": ["Keep using old bulbs", "Replace frequently used bulbs with LEDs", "Use more lamps instead"],
        "correct": "Replace frequently used bulbs with LEDs",
        "points": 10,
        "action": "leds",
        "correct_feedback": "Correct. LEDs are a simple low-cost upgrade for reducing electricity use.",
        "wrong_feedback": "Not the best choice. Start by replacing old bulbs in frequently used areas with LEDs.",
    },
    "curtains": {
        "label": "Curtains and window",
        "room": "Living room",
        "question": "Which action helps reduce heating or cooling demand?",
        "options": [
            "Leave windows uncovered during hot afternoons",
            "Use curtains/blinds to block summer heat and reduce winter heat loss",
            "Open windows while heating",
        ],
        "correct": "Use curtains/blinds to block summer heat and reduce winter heat loss",
        "points": 10,
        "action": "curtains",
        "correct_feedback": "Correct. Good curtain and blind use helps reduce unwanted heat gain and heat loss.",
        "wrong_feedback": "Not ideal. Poor window covering can make heating and cooling systems work harder.",
    },
    "draught": {
        "label": "Draught gap",
        "room": "Door / window area",
        "question": "What is the best low-cost action?",
        "options": ["Ignore small gaps", "Seal obvious draughts with door snakes or weather seals", "Increase heating or cooling"],
        "correct": "Seal obvious draughts with door snakes or weather seals",
        "points": 15,
        "action": "draught_sealing",
        "correct_feedback": "Correct. Draught sealing helps reduce wasted heating and cooling.",
        "wrong_feedback": "Not ideal. Gaps can let conditioned air escape and make systems work harder.",
    },
    "shower": {
        "label": "Shower / hot water",
        "room": "Bathroom",
        "question": "What is one fast way to reduce hot-water energy use?",
        "options": ["Take shorter showers", "Use hotter water", "Leave hot water running before showering"],
        "correct": "Take shorter showers",
        "points": 15,
        "action": "shorter_showers",
        "correct_feedback": "Correct. Hot water is a major household energy use. Shorter showers reduce both water and energy costs.",
        "wrong_feedback": "Not ideal. Longer showers increase hot-water energy use and can increase bills.",
    },
    "standby": {
        "label": "Standby appliances",
        "room": "Living room / study",
        "question": "What should the household do?",
        "options": ["Leave everything on standby", "Turn off unused devices at the wall or use a smart power board", "Buy a second fridge"],
        "correct": "Turn off unused devices at the wall or use a smart power board",
        "points": 10,
        "action": "standby",
        "correct_feedback": "Correct. Some appliances keep using energy when not actively used.",
        "wrong_feedback": "Not ideal. Unused standby devices can still use energy.",
    },
    "insulation": {
        "label": "Ceiling / roof insulation",
        "room": "Building shell check",
        "question": "Which upgrade usually gives strong long-term comfort and bill benefits?",
        "options": ["Check/improve ceiling or roof insulation", "Paint the wall a darker colour", "Open windows during winter nights"],
        "correct": "Check/improve ceiling or roof insulation",
        "points": 15,
        "action": "insulation_owner",
        "correct_feedback": "Correct. Insulation helps reduce heat transfer and lowers heating and cooling demand.",
        "wrong_feedback": "Not ideal. Poor insulation can increase heating and cooling demand.",
    },
}


# ---------- Money-first engagement logic ----------
def _currency(value: float) -> str:
    return f"A${int(round(value)):,}"


def estimate_money_snapshot(
    monthly_bill: float,
    household_size: str,
    main_problem: str,
    dwelling_type: str = "Detached house",
    home_condition: str = "Average / not sure",
) -> dict:
    """Return a conservative money-first snapshot for the opening hook.

    These are engagement estimates only, not certified savings. The ranges are intentionally
    bounded so the app sounds market-ready without making irresponsible claims.
    Dwelling type and perceived building condition are used only as light calibration signals.
    """
    annual_bill = max(0.0, monthly_bill * 12)
    if annual_bill <= 0:
        waste_low, waste_high = 0.0, 0.0
    else:
        # Conservative avoidable-waste assumption for a first-pass household check-up.
        base_low, base_high = 0.08, 0.22
        if main_problem in {"High winter bill", "High summer bill"}:
            base_low, base_high = 0.10, 0.25
        elif main_problem == "High hot-water bill":
            base_low, base_high = 0.07, 0.20

        # Household size and dwelling/building condition slightly adjust the opening estimate.
        # This is not a compliance calculation; it simply stops the hook being too generic.
        if household_size in {"3-4", "5+"}:
            base_high += 0.03
        if dwelling_type in {"Large detached house", "Detached house"}:
            base_high += 0.02
        elif dwelling_type == "Small apartment / unit":
            base_high -= 0.02
        if home_condition == "Older or draughty":
            base_low += 0.02
            base_high += 0.05
        elif home_condition == "Newer / efficient":
            base_low -= 0.02
            base_high -= 0.04

        base_low = max(0.04, base_low)
        base_high = max(base_low + 0.04, min(base_high, 0.32))
        waste_low = annual_bill * base_low
        waste_high = annual_bill * base_high
    return {
        "annual_bill": annual_bill,
        "waste_low": waste_low,
        "waste_high": waste_high,
        "three_month_low": waste_low / 4,
        "three_month_high": waste_high / 4,
        "monthly_low": waste_low / 12,
        "monthly_high": waste_high / 12,
        "dwelling_type": dwelling_type,
        "home_condition": home_condition,
    }


def estimate_behaviour_saving_pool(savings: dict) -> tuple[float, float]:
    """Estimate the no/low-cost saving pool available to fund first upgrades."""
    behaviour_keys = ["shorter_showers", "thermostat", "standby", "curtains"]
    low = sum(float(savings.get(k, (0, 0))[0]) for k in behaviour_keys if isinstance(savings.get(k, None), tuple))
    high = sum(float(savings.get(k, (0, 0))[1]) for k in behaviour_keys if isinstance(savings.get(k, None), tuple))
    return low, high


def months_to_fund(cost: float, monthly_low: float, monthly_high: float) -> str:
    """Translate a saving pool into a clear funding timeframe."""
    if cost <= 0:
        return "Immediate"
    if monthly_high <= 0:
        return "Not fundable from the current behaviour-saving estimate"
    fastest = max(1, int(-(-cost // max(monthly_high, 1))))
    slowest = max(fastest, int(-(-cost // max(monthly_low, 1)))) if monthly_low > 0 else None
    if slowest is None or slowest > 36:
        return f"From about {fastest}+ months, depending on consistency"
    if fastest == slowest:
        return f"About {fastest} month{'s' if fastest != 1 else ''}"
    return f"About {fastest}–{slowest} months"


def monthly_energy_seasonality(main_problem: str) -> list[float]:
    """Simple Australian monthly seasonality pattern for visual decision support.

    Values are normalised to average 1.0 so the user's reported monthly bill remains
    the annual anchor. Winter months are Jun-Aug; summer months are Dec-Feb.
    """
    if main_problem == "High winter bill":
        raw = [0.90, 0.88, 0.82, 0.78, 0.92, 1.28, 1.42, 1.32, 1.02, 0.86, 0.82, 0.88]
    elif main_problem == "High summer bill":
        raw = [1.38, 1.30, 1.05, 0.86, 0.78, 0.82, 0.86, 0.88, 0.92, 1.00, 1.12, 1.43]
    elif main_problem == "High hot-water bill":
        raw = [1.05, 1.02, 1.00, 0.98, 1.00, 1.08, 1.10, 1.08, 1.02, 0.98, 0.98, 1.01]
    else:
        raw = [1.15, 1.10, 0.98, 0.88, 0.90, 1.12, 1.22, 1.15, 0.95, 0.88, 0.92, 1.15]
    avg = sum(raw) / len(raw)
    return [v / avg for v in raw]


def build_energy_pathway_dataframe() -> pd.DataFrame:
    """Create the visual baseline/current/after-strategy annual cost pathway.

    The 'standard operating band' is a benchmark-style target: moderate thermostat use,
    efficient lighting, sensible hot-water behaviour, draught control, and reasonable
    envelope performance. It is aligned with the *intent* of efficient operation and
    NCC/NatHERS-style whole-of-home thinking, but it is not a code-compliance output.
    """
    months = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]
    monthly_bill = float(st.session_state.get("monthly_bill", 250.0))
    bill_problem = st.session_state.get("bill_problem", "Not sure")
    snap = st.session_state.get("money_snapshot") or estimate_money_snapshot(
        monthly_bill,
        st.session_state.get("household_size", "3-4"),
        bill_problem,
        st.session_state.get("dwelling_type", "Detached house"),
        st.session_state.get("home_condition", "Average / not sure"),
    )
    season = monthly_energy_seasonality(bill_problem)
    annual_bill = max(0.0, float(snap.get("annual_bill", monthly_bill * 12)))
    waste_low = max(0.0, float(snap.get("waste_low", annual_bill * 0.08)))
    waste_high = max(waste_low, float(snap.get("waste_high", annual_bill * 0.22)))

    current = [monthly_bill * m for m in season]
    # The optimal band is lower than the current line because this chart uses cost, not performance score.
    standard_upper = [(monthly_bill - waste_low / 12) * m for m in season]
    standard_lower = [(monthly_bill - waste_high / 12) * m for m in season]

    # Behaviour and low-cost upgrades improve progressively; the line moves toward the standard band.
    progress = [0.10, 0.16, 0.23, 0.31, 0.40, 0.50, 0.60, 0.69, 0.77, 0.84, 0.90, 0.94]
    after_strategy = [(monthly_bill - (waste_high / 12) * p) * m for p, m in zip(progress, season)]

    return pd.DataFrame({
        "Month": months,
        "Current estimated pathway": [round(v, 0) for v in current],
        "After applying strategies": [round(max(0, v), 0) for v in after_strategy],
        "Standard operating band - lower": [round(max(0, v), 0) for v in standard_lower],
        "Standard operating band - upper": [round(max(0, v), 0) for v in standard_upper],
    })


def energy_pathway_figure() -> go.Figure:
    df = build_energy_pathway_dataframe()
    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=df["Month"],
        y=df["Standard operating band - upper"],
        mode="lines",
        name="Standard operating band — upper",
        line=dict(width=0),
        hovertemplate="%{x}: A$%{y:.0f}<extra></extra>",
    ))
    fig.add_trace(go.Scatter(
        x=df["Month"],
        y=df["Standard operating band - lower"],
        mode="lines",
        name="Standard operating band",
        fill="tonexty",
        line=dict(width=0),
        hovertemplate="%{x}: A$%{y:.0f}<extra></extra>",
    ))
    fig.add_trace(go.Scatter(
        x=df["Month"],
        y=df["Current estimated pathway"],
        mode="lines+markers",
        name="Your current input",
        hovertemplate="%{x}: A$%{y:.0f}<extra></extra>",
    ))
    fig.add_trace(go.Scatter(
        x=df["Month"],
        y=df["After applying strategies"],
        mode="lines+markers",
        name="After applying strategies",
        hovertemplate="%{x}: A$%{y:.0f}<extra></extra>",
    ))
    fig.update_layout(
        height=385,
        margin=dict(l=20, r=20, t=45, b=20),
        yaxis_title="Estimated monthly energy cost (A$)",
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="left", x=0),
    )
    return fig




def current_household_inputs() -> HouseholdInputs:
    """Build the calculation input object from current session-state values."""
    return HouseholdInputs(
        household_size=st.session_state.get("household_size", "3-4"),
        tenure_type=st.session_state.get("tenure_type", "Rented"),
        bill_problem=st.session_state.get("bill_problem", "Not sure"),
        hvac_type=st.session_state.get("hvac_type", "Not sure"),
        solar_status=st.session_state.get("solar_status", "Not sure"),
        monthly_bill_aud=float(st.session_state.get("monthly_bill", 250.0)),
        electricity_price=float(st.session_state.get("electricity_price", 0.35)),
        shower_minutes_current=float(st.session_state.get("shower_current", 10)),
        shower_minutes_target=float(st.session_state.get("shower_target", 4)),
        showers_per_person_per_day=float(st.session_state.get("showers_per_person", 1.0)),
        old_bulbs=int(st.session_state.get("old_bulbs", 8)),
        hours_per_bulb_per_day=float(st.session_state.get("bulb_hours", 3.0)),
        standby_devices=int(st.session_state.get("standby_devices", 8)),
        thermostat_degrees_improved=int(st.session_state.get("thermostat_degrees", 2)),
    )


def current_ranked_actions() -> list:
    """Return ranked actions using the current completed inspection state."""
    return generate_ranked_actions(
        st.session_state.get("selected_actions", []),
        st.session_state.get("tenure_type", "Rented"),
        st.session_state.get("bill_problem", "Not sure"),
        st.session_state.get("solar_status", "Not sure"),
    )


def save_anonymous_progress_if_needed(savings: dict | None = None, ranked: list | None = None, result_text: str | None = None) -> bool:
    """Save the completed anonymous response once, at recommendation unlock.

    The app does not collect names, emails, phone numbers, or contact details. A short
    notice is shown near the recommendation button so data collection stays transparent.
    """
    if st.session_state.get("response_saved"):
        return True
    try:
        conn = st.connection("gsheets", type=GSheetsConnection)
        participant_id = get_next_participant_id(conn)
        if savings is None:
            savings = estimate_all_savings(current_household_inputs())
        if ranked is None:
            ranked = current_ranked_actions()
        if result_text is None:
            result_text = score_label(st.session_state.get("score", 0))
        submission = build_anonymous_submission(participant_id, savings, ranked, result_text)
        save_response_to_gsheet(submission)
        st.session_state["participant_id"] = participant_id
        st.session_state["response_saved"] = True
        return True
    except Exception as exc:
        st.session_state["save_error"] = str(exc)
        return False


def build_funding_pathway(inputs: HouseholdInputs, savings: dict) -> list[dict]:
    """Build a personalised save-to-upgrade pathway.

    The logic excludes irrelevant recommendations: for example, it does not ask users
    already at 4-minute showers to reduce shower time further.
    """
    behaviour_low, behaviour_high = estimate_behaviour_saving_pool(savings)
    monthly_low, monthly_high = behaviour_low / 12, behaviour_high / 12

    steps: list[dict] = []
    shower_gap = max(0, float(inputs.shower_minutes_current) - float(inputs.shower_minutes_target))
    if shower_gap > 0:
        steps.append({
            "stage": "Episode 1 — Recover money without spending",
            "title": "Run a 30-day hot-water challenge",
            "logic": f"Reduce average shower time from {inputs.shower_minutes_current:g} to {inputs.shower_minutes_target:g} minutes.",
            "saving": format_saving_range(savings.get("shorter_showers", (0, 0))),
            "cost": "A$0",
            "unlock": "Creates the first saving pool for small upgrades.",
        })
    else:
        steps.append({
            "stage": "Episode 1 — Recover money without spending",
            "title": "Skip shower reduction and target another behaviour",
            "logic": "Your shower target is already tight, so the pathway shifts to thermostat, standby, curtains, and appliance habits.",
            "saving": format_saving_range((max(0, behaviour_low - savings.get("shorter_showers", (0, 0))[0]), max(0, behaviour_high - savings.get("shorter_showers", (0, 0))[1]))),
            "cost": "A$0",
            "unlock": "Avoids giving you a generic recommendation that does not fit your behaviour.",
        })

    if inputs.old_bulbs > 0:
        led_cost = max(30, min(240, inputs.old_bulbs * 8))
        steps.append({
            "stage": "Episode 2 — Use saved money for a quick upgrade",
            "title": "Replace frequently used old bulbs with LEDs",
            "logic": f"You reported {inputs.old_bulbs} older bulbs. Start with the rooms used every day.",
            "saving": format_saving_range(savings.get("leds", (0, 0))),
            "cost": f"Approx. {_currency(led_cost)}",
            "unlock": months_to_fund(led_cost, monthly_low, monthly_high),
        })

    # Hot-water cylinder wrapping is only presented as a conditional pathway because many Australian homes do not have an exposed cylinder.
    cylinder_wrap_cost = 200
    if inputs.bill_problem == "High hot-water bill" or shower_gap > 0:
        steps.append({
            "stage": "Episode 3 — Fund a hot-water efficiency action",
            "title": "Check whether a hot-water cylinder wrap is relevant",
            "logic": "Only use this step if the home has an accessible electric storage hot-water cylinder and local safety guidance allows wrapping.",
            "saving": "Indicative; depends on system type and existing insulation",
            "cost": f"Example budget: {_currency(cylinder_wrap_cost)}",
            "unlock": months_to_fund(cylinder_wrap_cost, monthly_low, monthly_high),
        })

    draught_budget = 250 if inputs.tenure_type == "Rented" else 750
    steps.append({
        "stage": "Episode 4 — Compound savings into building-shell action",
        "title": "Move from behaviour savings to draught control",
        "logic": "Start with door snakes and weather seals; owners can later consider more complete draught sealing.",
        "saving": format_saving_range(savings.get("draught_sealing", (0, 0))) if "draught_sealing" in savings else "Not fully monetised in this beta",
        "cost": f"Planning budget: {_currency(draught_budget)}",
        "unlock": months_to_fund(draught_budget, monthly_low, monthly_high),
    })

    if inputs.tenure_type == "Owned":
        insulation_budget = 1800
        steps.append({
            "stage": "Episode 5 — Long-term upgrade pathway",
            "title": "Prepare for insulation or larger envelope upgrades",
            "logic": "Use the accumulated saving history to decide whether a professional insulation check is worth it.",
            "saving": "Potentially high, but requires home-specific assessment",
            "cost": f"Planning budget: {_currency(insulation_budget)}+",
            "unlock": months_to_fund(insulation_budget, monthly_low, monthly_high),
        })
    else:
        steps.append({
            "stage": "Episode 5 — Renter pathway",
            "title": "Turn evidence into a landlord/property-manager conversation",
            "logic": "Document draughts, poor curtains, and comfort problems. Ask for realistic upgrades rather than paying for owner-controlled capital works yourself.",
            "saving": "Depends on landlord-approved changes",
            "cost": "A$0–low cost for documentation and temporary measures",
            "unlock": "Immediate renter-friendly pathway",
        })
    return steps


# ---------- UI helpers ----------
def _logo_html() -> str:
    """Return the company logo as constrained HTML so Streamlit does not enlarge it."""
    if LOGO_PATH.exists():
        suffix = LOGO_PATH.suffix.lower().replace(".", "") or "png"
        mime = "jpeg" if suffix in {"jpg", "jpeg"} else suffix
        encoded = base64.b64encode(LOGO_PATH.read_bytes()).decode("utf-8")
        return f'<img src="data:image/{mime};base64,{encoded}" alt="Company logo">'
    return '<div class="logo-placeholder"><strong>Your logo here</strong><br>Add your file as<br><code>assets/company_logo.png</code></div>'


def _sidebar_logo_html() -> str:
    """Return a compact logo block for the sidebar."""
    if LOGO_PATH.exists():
        suffix = LOGO_PATH.suffix.lower().replace(".", "") or "png"
        mime = "jpeg" if suffix in {"jpg", "jpeg"} else suffix
        encoded = base64.b64encode(LOGO_PATH.read_bytes()).decode("utf-8")
        logo = f'<img src="data:image/{mime};base64,{encoded}" alt="Company logo">'
    else:
        logo = '<div class="logo-placeholder">Logo</div>'
    return f"""
    <div class="sidebar-brand">
        {logo}
        <div class="sidebar-brand-title">Tech Innovation Experts</div>
        <div class="sidebar-brand-text">Providing technology-driven services across Oceania</div>
        <div class="sidebar-brand-text">tinx@gmail.com</div>
    </div>
    """


def logo_header() -> None:
    st.markdown(
        f"""
        <div class="header-grid">
            <div class="hero">
                <span class="badge">Beta Version 1.0</span>
                <h1>{APP_TITLE}</h1>
                <p>{TAGLINE}</p>
                <p>Estimate avoidable energy waste, inspect the home, and build a staged saving pathway.</p>
            </div>
            <div class="logo-card">
                {_logo_html()}
                <div class="company-name">Tech Innovation Experts</div>
                <div class="company-tagline">Providing technology-driven services across Oceania</div>
                <div class="company-email">Email: tinx@gmail.com</div>
            </div>
        </div>
        <div class="compliance-strip">
            <div class="compliance-icon">NCC</div>
            <div><strong>NCC 2022 / NatHERS Whole of Home aligned.</strong> Educational guidance only; this tool is not a certified compliance assessment or accredited NatHERS rating.</div>
        </div>
        """,
        unsafe_allow_html=True,
    )



def sidebar_account_card() -> None:
    """Show logged-in account and active project information in the left sidebar."""
    st.sidebar.markdown(
        """
        <style>
        .sidebar-account-card {
            padding: .9rem;
            border-radius: 16px;
            background: #ECFDF5;
            border: 1px solid #A7F3D0;
            margin: .6rem 0 1rem 0;
            color: #064E3B;
        }
        .sidebar-account-top {
            display: flex;
            gap: .55rem;
            align-items: center;
            margin-bottom: .45rem;
        }
        .sidebar-avatar {
            width: 34px;
            height: 34px;
            min-width: 34px;
            border-radius: 999px;
            background: #0F766E;
            color: #FFFFFF;
            display: flex;
            align-items: center;
            justify-content: center;
            font-weight: 900;
            font-size: .9rem;
        }
        .sidebar-account-title {
            font-weight: 900;
            color: #064E3B;
            font-size: .86rem;
            line-height: 1.2;
        }
        .sidebar-account-email {
            font-size: .72rem;
            color: #047857;
            line-height: 1.25;
            overflow-wrap: anywhere;
        }
        .sidebar-account-row {
            font-size: .76rem;
            color: #334155;
            margin-top: .25rem;
            line-height: 1.35;
        }
        .sidebar-account-pill {
            display: inline-block;
            margin-top: .45rem;
            padding: .25rem .5rem;
            border-radius: 999px;
            background: #FFFFFF;
            border: 1px solid #A7F3D0;
            color: #065F46;
            font-size: .70rem;
            font-weight: 800;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )

    if is_logged_in():
        email = st.session_state.get("auth_email", "Logged-in user")
        project = st.session_state.get("active_project_name") or st.session_state.get("household_nickname", "Home 1")
        initials = (email[:1] or "U").upper()
        st.sidebar.markdown(
            f"""
            <div class='sidebar-account-card'>
                <div class='sidebar-account-top'>
                    <div class='sidebar-avatar'>{initials}</div>
                    <div>
                        <div class='sidebar-account-title'>Logged in</div>
                        <div class='sidebar-account-email'>{email}</div>
                    </div>
                </div>
                <div class='sidebar-account-row'><strong>Active project:</strong> {project}</div>
                <div class='sidebar-account-row'><strong>Mode:</strong> Personal dashboard</div>
                <span class='sidebar-account-pill'>Account saved</span>
            </div>
            """,
            unsafe_allow_html=True,
        )
        if st.sidebar.button("Open dashboard", use_container_width=True, key="sidebar_open_dashboard"):
            next_stage("dashboard")
        if st.sidebar.button("Log out", use_container_width=True, key="sidebar_logout"):
            for key in ["auth_user_id", "auth_email", "auth_access_token", "auth_refresh_token"]:
                st.session_state.pop(key, None)
            st.rerun()
    else:
        st.sidebar.markdown(
            """
            <div class='sidebar-account-card'>
                <div class='sidebar-account-top'>
                    <div class='sidebar-avatar'>?</div>
                    <div>
                        <div class='sidebar-account-title'>Not logged in</div>
                        <div class='sidebar-account-email'>Create an account to continue</div>
                    </div>
                </div>
                <span class='sidebar-account-pill'>Account required</span>
            </div>
            """,
            unsafe_allow_html=True,
        )
        if st.sidebar.button("Log in / create account", use_container_width=True, key="sidebar_login"):
            next_stage("account")


def sidebar_status() -> None:
    sidebar_account_card()
    st.sidebar.title("Inspection status")
    st.sidebar.metric("Score", f"{st.session_state.score}/100")
    st.sidebar.progress(min(st.session_state.score, 100) / 100)
    st.sidebar.write(f"**Result:** {score_label(st.session_state.score)}")
    st.sidebar.write(f"Completed checks: {len(st.session_state.completed_hotspots)}/7")
    if st.sidebar.button("Restart check-up"):
        reset_app()
        st.rerun()
    st.sidebar.markdown(_sidebar_logo_html(), unsafe_allow_html=True)


def next_stage(stage: str) -> None:
    st.session_state.stage = stage
    st.rerun()


def update_for_answer(hotspot_key: str, selected: str) -> None:
    hotspot = HOTSPOTS[hotspot_key]
    already_done = hotspot_key in st.session_state.completed_hotspots
    is_correct = selected == hotspot["correct"]
    feedback_text = hotspot["correct_feedback"] if is_correct else hotspot["wrong_feedback"]

    if is_correct:
        if not already_done:
            st.session_state.score += hotspot["points"]
            st.session_state.bill_risk = max(0, st.session_state.bill_risk - 7)
            st.session_state.comfort = min(100, st.session_state.comfort + 5)
            st.session_state.selected_actions.append(hotspot["action"])
            if hotspot_key == "insulation":
                if st.session_state.get("tenure_type") == "Rented":
                    st.session_state.selected_actions[-1] = "insulation_renter"
    else:
        if not already_done:
            st.session_state.bill_risk = min(100, st.session_state.bill_risk + 3)

    st.session_state.completed_hotspots.add(hotspot_key)
    st.session_state[f"{hotspot_key}_answer"] = selected
    st.session_state[f"{hotspot_key}_correct"] = is_correct
    st.session_state.last_feedback[hotspot_key] = {
        "is_correct": is_correct,
        "selected": selected,
        "correct": hotspot["correct"],
        "message": feedback_text,
    }


def gauge(value: int, title: str) -> go.Figure:
    fig = go.Figure(go.Indicator(
        mode="gauge+number",
        value=value,
        gauge={"axis": {"range": [0, 100]}, "bar": {"thickness": 0.25}},
        title={"text": title},
    ))
    fig.update_layout(height=240, margin=dict(l=20, r=20, t=50, b=10))
    return fig


def _load_font(size: int, bold: bool = False):
    candidates = [
        "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf" if bold else "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
        "/usr/share/fonts/truetype/liberation2/LiberationSans-Bold.ttf" if bold else "/usr/share/fonts/truetype/liberation2/LiberationSans-Regular.ttf",
    ]
    for candidate in candidates:
        if Path(candidate).exists():
            return ImageFont.truetype(candidate, size)
    return ImageFont.load_default()


def _draw_centered(draw: ImageDraw.ImageDraw, text: str, y: int, font, fill: str, width: int = 1200) -> int:
    bbox = draw.textbbox((0, 0), text, font=font)
    x = (width - (bbox[2] - bbox[0])) / 2
    draw.text((x, y), text, font=font, fill=fill)
    return y + (bbox[3] - bbox[1]) + 12


def _draw_wrapped_centered(draw: ImageDraw.ImageDraw, text: str, y: int, font, fill: str, width: int, wrap: int, line_gap: int = 7) -> int:
    for line in textwrap.wrap(text, width=wrap):
        bbox = draw.textbbox((0, 0), line, font=font)
        x = (width - (bbox[2] - bbox[0])) / 2
        draw.text((x, y), line, font=font, fill=fill)
        y += (bbox[3] - bbox[1]) + line_gap
    return y


def generate_certificate_png(name: str, score: int, result_label: str) -> bytes:
    name = name.strip() or "Home-energy Participant"
    today = date.today().strftime("%d %B %Y")
    width, height = 1400, 1400
    img = Image.new("RGB", (width, height), "#EEF2F7")
    draw = ImageDraw.Draw(img)

    # Main square certificate surface
    margin = 70
    draw.rounded_rectangle((margin, margin, width - margin, height - margin), radius=54, fill="#FFFFFF", outline="#0F766E", width=8)
    draw.rounded_rectangle((102, 102, width - 102, height - 102), radius=38, outline="#99F6E4", width=3)
    draw.rounded_rectangle((132, 132, width - 132, height - 132), radius=30, outline="#E2E8F0", width=2)

    # Decorative top band and corner shapes
    draw.rectangle((margin, margin, width - margin, 235), fill="#0F766E")
    draw.polygon([(margin, 235), (270, 235), (160, 345)], fill="#0EA5E9")
    draw.polygon([(width - margin, 235), (width - 270, 235), (width - 160, 345)], fill="#0EA5E9")

    # Visible right-side ribbon
    ribbon = [(width - 315, margin), (width - 70, margin), (width - 70, 315)]
    draw.polygon(ribbon, fill="#0F766E")
    draw.line((width - 315, margin, width - 70, 315), fill="#CCFBF1", width=3)
    # rotated ribbon text
    ribbon_layer = Image.new("RGBA", (430, 80), (0, 0, 0, 0))
    rd = ImageDraw.Draw(ribbon_layer)
    rd.text((20, 22), "RECOGNITION", font=_load_font(28, True), fill="#FFFFFF")
    ribbon_layer = ribbon_layer.rotate(-45, expand=True)
    img.paste(ribbon_layer, (width - 365, 78), ribbon_layer)

    # Logo on top band
    if LOGO_PATH.exists():
        try:
            logo = Image.open(LOGO_PATH).convert("RGBA")
            logo.thumbnail((240, 92))
            logo_x = int((width - logo.width) / 2)
            logo_y = 105 + int((92 - logo.height) / 2)
            img.paste(logo, (logo_x, logo_y), logo)
        except Exception:
            _draw_centered(draw, "Tech Innovation Experts", 130, _load_font(28, True), "#FFFFFF", width)
    else:
        _draw_centered(draw, "Tech Innovation Experts", 130, _load_font(28, True), "#FFFFFF", width)

    y = 315
    y = _draw_centered(draw, "BETA VERSION 1.0", y, _load_font(22, True), "#0F766E", width)
    y = _draw_centered(draw, "Certificate of Completion", y + 12, _load_font(60, True), "#0F172A", width)
    y = _draw_centered(draw, "The Home-energy check-up (Australia)", y + 8, _load_font(31, True), "#475569", width)
    y = _draw_centered(draw, "Tech Innovation Experts", y + 8, _load_font(26, True), "#0F766E", width)
    y = _draw_centered(draw, "This certificate recognises", y + 34, _load_font(28), "#475569", width)

    name_font = _load_font(62, True)
    name_lines = textwrap.wrap(name, width=28) or [name]
    for line in name_lines[:2]:
        y = _draw_centered(draw, line, y + 10, name_font, "#0F766E", width)
    draw.line((340, y + 6, width - 340, y + 6), fill="#99F6E4", width=5)
    y += 42

    body = "for completing the home-energy check-up and building a practical, prioritised energy action plan."
    y = _draw_wrapped_centered(draw, body, y, _load_font(30), "#334155", width, wrap=68, line_gap=11)
    y += 34

    badges = [f"Result: {result_label}", f"Score: {score}/100", f"Date: {today}"]
    badge_font = _load_font(25, True)
    badge_h = 62
    badge_widths = [draw.textbbox((0, 0), b, font=badge_font)[2] + 62 for b in badges]
    total_w = sum(badge_widths) + 24 * (len(badges) - 1)
    x = int((width - total_w) / 2)
    for b, bw in zip(badges, badge_widths):
        draw.rounded_rectangle((x, y, x + bw, y + badge_h), radius=31, fill="#ECFDF5", outline="#A7F3D0", width=2)
        bbox = draw.textbbox((0, 0), b, font=badge_font)
        draw.text((x + (bw - (bbox[2] - bbox[0])) / 2, y + 18), b, font=badge_font, fill="#065F46")
        x += bw + 24
    y += badge_h + 55

    # Recognition seal
    seal_cx, seal_cy, seal_r = width // 2, y + 68, 74
    draw.ellipse((seal_cx - seal_r, seal_cy - seal_r, seal_cx + seal_r, seal_cy + seal_r), fill="#0F766E", outline="#0EA5E9", width=6)
    _draw_centered(draw, "TIE", seal_cy - 42, _load_font(38, True), "#FFFFFF", width)
    _draw_centered(draw, "RECOGNISED", seal_cy + 2, _load_font(15, True), "#CCFBF1", width)

    footer_y = height - 205
    _draw_centered(draw, "Tech Innovation Experts", footer_y, _load_font(26, True), "#0F172A", width)
    _draw_centered(draw, "Providing technology-driven services across Oceania | tinx@gmail.com", footer_y + 40, _load_font(22), "#475569", width)
    _draw_centered(draw, "Recognition certificate only. Not a certified energy assessment or accredited NCC/NatHERS rating.", height - 105, _load_font(18), "#64748B", width)

    buffer = BytesIO()
    img.save(buffer, format="PNG", quality=95)
    return buffer.getvalue()

def welcome_screen() -> None:
    logo_header()
    col1, col2, col3 = st.columns(3)
    with col1:
        st.markdown("<div class='card'><h3>1. Profile</h3><p>Answer five simple household questions.</p></div>", unsafe_allow_html=True)
    with col2:
        st.markdown("<div class='card'><h3>2. Inspect</h3><p>Complete seven home-energy checks.</p></div>", unsafe_allow_html=True)
    with col3:
        st.markdown("<div class='card'><h3>3. Action plan</h3><p>Receive a prioritised plan with indicative savings.</p></div>", unsafe_allow_html=True)
    st.markdown("<br>", unsafe_allow_html=True)
    st.info("This public prototype gives educational guidance, not a certified home energy assessment. Dollar estimates are indicative and depend on tariff, climate, equipment, and behaviour.")
    if st.button("Show me my money leak", type="primary", use_container_width=True):
        next_stage("money")



def money_screen() -> None:
    logo_header()
    sidebar_account_card()
    st.title("Start with the money")
    st.caption("The first step is not another generic energy tip. It is a quick estimate of how much avoidable energy waste may be leaving your pocket.")

    with st.form("money_snapshot_form"):
        c1, c2, c3 = st.columns(3)
        with c1:
            monthly_bill = st.number_input("Approximate monthly energy bill (A$)", min_value=0.0, max_value=3000.0, value=float(st.session_state.get("monthly_bill", 250.0)), step=10.0)
            dwelling_options = ["Small apartment / unit", "Townhouse / small house", "Detached house", "Large detached house"]
            dwelling_type = st.selectbox("What best describes the home?", dwelling_options, index=dwelling_options.index(st.session_state.get("dwelling_type", "Detached house")) if st.session_state.get("dwelling_type", "Detached house") in dwelling_options else 2)
        with c2:
            household_size = st.radio("People in the home", ["1", "2", "3-4", "5+"], horizontal=True, index=["1", "2", "3-4", "5+"].index(st.session_state.get("household_size", "3-4")) if st.session_state.get("household_size", "3-4") in ["1", "2", "3-4", "5+"] else 2)
            condition_options = ["Newer / efficient", "Average / not sure", "Older or draughty"]
            home_condition = st.radio("How does the home feel thermally?", condition_options, index=condition_options.index(st.session_state.get("home_condition", "Average / not sure")) if st.session_state.get("home_condition", "Average / not sure") in condition_options else 1)
        with c3:
            bill_problem = st.selectbox("Where does the bill hurt most?", ["High winter bill", "High summer bill", "High hot-water bill", "Not sure"], index=["High winter bill", "High summer bill", "High hot-water bill", "Not sure"].index(st.session_state.get("bill_problem", "Not sure")) if st.session_state.get("bill_problem", "Not sure") in ["High winter bill", "High summer bill", "High hot-water bill", "Not sure"] else 3)
            st.markdown("<div class='small-muted'>These five inputs are enough to create a stronger first estimate without turning the start into a long audit.</div>", unsafe_allow_html=True)
        submitted = st.form_submit_button("Estimate my saving opportunity", type="primary", use_container_width=True)

    if submitted or "money_snapshot" in st.session_state:
        if submitted:
            st.session_state["monthly_bill"] = monthly_bill
            st.session_state["household_size"] = household_size
            st.session_state["bill_problem"] = bill_problem
            st.session_state["dwelling_type"] = dwelling_type
            st.session_state["home_condition"] = home_condition
            st.session_state["money_snapshot"] = estimate_money_snapshot(monthly_bill, household_size, bill_problem, dwelling_type, home_condition)

        snap = st.session_state["money_snapshot"]
        st.markdown(
            f"""
            <div class='money-hero'>
                <h2>Your energy bill may contain avoidable waste</h2>
                <p>Based on this quick starting scenario, your estimated annual energy spend is:</p>
                <div class='money-number'>{_currency(snap['annual_bill'])}</div>
                <p>A realistic first-stage saving opportunity may be around <strong>{_currency(snap['waste_low'])}–{_currency(snap['waste_high'])} per year</strong>, depending on your habits, tariff, appliances, and building condition.</p>
                <div class='money-sub'>Indicative decision-support estimate only. This is not a certified energy assessment or a guaranteed saving.</div>
            </div>
            """,
            unsafe_allow_html=True,
        )
        c1, c2, c3 = st.columns(3)
        with c1:
            st.markdown(f"<div class='money-card'><h4>Possible monthly recovery</h4><div class='value'>{_currency(snap['monthly_low'])}–{_currency(snap['monthly_high'])}</div><p>Money that may be recovered through behaviour and low-cost actions.</p></div>", unsafe_allow_html=True)
        with c2:
            st.markdown(f"<div class='money-card'><h4>Possible 3-month target</h4><div class='value'>{_currency(snap['three_month_low'])}–{_currency(snap['three_month_high'])}</div><p>A short challenge target before larger upgrades.</p></div>", unsafe_allow_html=True)
        with c3:
            st.markdown(f"<div class='money-card'><h4>12-month saving pathway</h4><div class='value'>{_currency(snap['waste_low'])}–{_currency(snap['waste_high'])}</div><p>The pathway will rank actions and show what each saving can fund next.</p></div>", unsafe_allow_html=True)

        st.markdown("### Your annual energy-cost pathway")
        st.caption("This graph shows where you are now, where an efficient operating range may sit, and where your household could move after applying the recommended strategies. It is a benchmark-style cost pathway, not an NCC/NatHERS compliance result or a guaranteed bill forecast.")
        st.plotly_chart(energy_pathway_figure(), use_container_width=True)
        st.markdown(
            f"""
            <div class='success-box'>
                <strong>What this means:</strong> your current pathway is estimated from the bill you entered. If you follow the personalised strategy pathway, the model estimates a possible annual saving of <strong>{_currency(snap['waste_low'])}–{_currency(snap['waste_high'])}</strong>.
            </div>
            """,
            unsafe_allow_html=True,
        )

        st.markdown("### Want to reduce this?")
        st.write("The next step checks whether your saving opportunity is coming from hot water, heating/cooling, lighting, standby devices, draughts, curtains, or insulation. Irrelevant recommendations will be skipped.")
        if st.button("Yes — build my personalised saving pathway", type="primary", use_container_width=True):
            next_stage("profile")


def profile_screen() -> None:
    sidebar_account_card()
    st.title("Household profile")
    st.caption("A short profile helps personalise the energy action plan without making the tool feel like a survey.")
    with st.form("profile_form"):
        c1, c2 = st.columns(2)
        with c1:
            household_size_options = ["1", "2", "3-4", "5+"]
            household_size = st.radio("How many people live in the home?", household_size_options, horizontal=True, index=household_size_options.index(st.session_state.get("household_size", "3-4")) if st.session_state.get("household_size", "3-4") in household_size_options else 2)
            tenure_type = st.radio("Is the home rented or owned?", ["Rented", "Owned"], horizontal=True)
            bill_problem_options = ["High winter bill", "High summer bill", "High hot-water bill", "Not sure"]
            bill_problem = st.selectbox("What is the main bill problem?", bill_problem_options, index=bill_problem_options.index(st.session_state.get("bill_problem", "Not sure")) if st.session_state.get("bill_problem", "Not sure") in bill_problem_options else 3)
            dwelling_type = st.selectbox("Home type", ["Small apartment / unit", "Townhouse / small house", "Detached house", "Large detached house"], index=["Small apartment / unit", "Townhouse / small house", "Detached house", "Large detached house"].index(st.session_state.get("dwelling_type", "Detached house")) if st.session_state.get("dwelling_type", "Detached house") in ["Small apartment / unit", "Townhouse / small house", "Detached house", "Large detached house"] else 2)
        with c2:
            hvac_type = st.selectbox("What is the main heating/cooling system?", ["Split-system AC", "Gas heater", "Portable electric heater", "Ducted system", "Not sure"])
            solar_status = st.radio("Does the home have solar panels?", ["Yes", "No", "Not sure"], horizontal=True)
            monthly_bill = st.number_input("Approximate monthly energy bill (A$)", min_value=0.0, max_value=2000.0, value=float(st.session_state.get("monthly_bill", 250.0)), step=10.0)
            condition_options = ["Newer / efficient", "Average / not sure", "Older or draughty"]
            home_condition = st.radio("Thermal feel of the home", condition_options, index=condition_options.index(st.session_state.get("home_condition", "Average / not sure")) if st.session_state.get("home_condition", "Average / not sure") in condition_options else 1)
        st.markdown("#### Optional assumptions for indicative savings")
        c3, c4, c5 = st.columns(3)
        with c3:
            electricity_price = st.number_input("Electricity price (A$/kWh)", 0.05, 1.50, 0.35, 0.01)
            thermostat_degrees = st.slider("Thermostat improvement from current setting (°C)", 0, 6, 2)
        with c4:
            shower_current = st.slider("Current average shower time (minutes)", 2, 20, 10)
            shower_target = st.slider("Target shower time (minutes)", 2, 12, 4)
            showers_per_person = st.slider("Showers per person per day", 0.5, 2.0, 1.0, 0.1)
        with c5:
            old_bulbs = st.slider("Old halogen/incandescent bulbs used often", 0, 30, 8)
            bulb_hours = st.slider("Average hours per bulb per day", 0.5, 10.0, 3.0, 0.5)
            standby_devices = st.slider("Standby devices to manage", 0, 30, 8)
        submitted = st.form_submit_button("Save profile and inspect home", type="primary", use_container_width=True)
    if submitted:
        st.session_state.update({
            "household_size": household_size,
            "tenure_type": tenure_type,
            "bill_problem": bill_problem,
            "dwelling_type": dwelling_type,
            "home_condition": home_condition,
            "hvac_type": hvac_type,
            "solar_status": solar_status,
            "monthly_bill": monthly_bill,
            "electricity_price": electricity_price,
            "shower_current": shower_current,
            "shower_target": shower_target,
            "showers_per_person": showers_per_person,
            "old_bulbs": old_bulbs,
            "bulb_hours": bulb_hours,
            "standby_devices": standby_devices,
            "thermostat_degrees": thermostat_degrees,
            "money_snapshot": estimate_money_snapshot(monthly_bill, household_size, bill_problem, dwelling_type, home_condition),
        })
        next_stage("inspection")


def inspection_screen() -> None:
    st.title("Home inspection")
    st.write("Select each hotspot, answer one question, and receive immediate feedback.")
    sidebar_status()

    st.caption("Complete the seven checks below. Your responses will personalise the final recommendations and saving pathway.")

    c1, c2 = st.columns([0.60, 0.40])
    with c1:
        tab1, tab2, tab3 = st.tabs(["Living room", "Bathroom", "Building shell"])
        with tab1:
            st.subheader("Living room checks")
            for key in ["thermostat", "leds", "curtains", "standby"]:
                render_hotspot(key)
        with tab2:
            st.subheader("Bathroom and hot water")
            render_hotspot("shower")
        with tab3:
            st.subheader("Door, window, and roof checks")
            render_hotspot("draught")
            render_hotspot("insulation")
    with c2:
        st.plotly_chart(gauge(st.session_state.bill_risk, "Bill risk"), use_container_width=True)
        st.plotly_chart(gauge(st.session_state.comfort, "Comfort readiness"), use_container_width=True)
        st.markdown("<div class='warning-box'><strong>Design note:</strong> The hidden model updates bill risk and comfort, but users only see simple feedback and final recommendations.</div>", unsafe_allow_html=True)

    if len(st.session_state.completed_hotspots) >= 7:
        st.info("When you unlock the recommendations, the completed responses are saved anonymously for tool improvement. No name, email address, phone number, or contact detail is collected or stored.")
        if st.button("Unlock my recommendations and saving pathway", type="primary", use_container_width=True):
            inputs = current_household_inputs()
            savings = estimate_all_savings(inputs)
            ranked = current_ranked_actions()
            result_text = score_label(st.session_state.get("score", 0))
            save_anonymous_progress_if_needed(savings, ranked, result_text)
            next_stage("plan")
    else:
        st.info("Complete all seven checks to unlock the final action plan.")


def render_hotspot(key: str) -> None:
    hotspot = HOTSPOTS[key]
    done = key in st.session_state.completed_hotspots
    feedback = st.session_state.last_feedback.get(key)
    with st.expander(("✅ " if done else "🔎 ") + hotspot["label"] + f" — {hotspot['room']}", expanded=True if feedback else not done):
        st.write(f"**Question:** {hotspot['question']}")
        answer = st.radio("Choose one answer", hotspot["options"], key=f"answer_{key}", index=None, disabled=done)
        if st.button("Check answer", key=f"check_{key}", disabled=answer is None or done):
            update_for_answer(key, answer)
            st.rerun()
        if feedback:
            if feedback["is_correct"]:
                st.success(
                    "**Correct answer**\n\n"
                    f"**Your selection:** {feedback['selected']}\n\n"
                    f"{feedback['message']}"
                )
            else:
                st.error(
                    "**Not the best answer**\n\n"
                    f"**Your selection:** {feedback['selected']}\n\n"
                    f"**Better choice:** {feedback['correct']}\n\n"
                    f"{feedback['message']}"
                )
        elif done:
            st.caption("This hotspot has already been scored.")


def plan_screen() -> None:
    st.title("Your Energy Action Plan")
    sidebar_status()

    inputs = current_household_inputs()
    savings = estimate_all_savings(inputs)
    ranked = current_ranked_actions()
    top_actions = top_three_actions(ranked)

    result_text = score_label(st.session_state.score)
    completion_date = date.today().strftime("%d %B %Y")
    total_low = int(sum(v[0] for v in savings.values()))
    total_high = int(sum(v[1] for v in savings.values()))
    st.session_state["result_category"] = result_text
    st.session_state["estimated_annual_savings"] = f"A${total_low:,}–A${total_high:,}"
    certificate_name = st.session_state.get("certificate_display_name", "") or st.session_state.get("participant_id", "Anonymous Participant")

    st.markdown(f"<div class='success-box'><h3>{result_text}</h3><p>Score: {st.session_state.score}/100. Fix energy waste first, then consider bigger upgrades.</p></div>", unsafe_allow_html=True)

    st.markdown("### Top three actions")
    cols = st.columns(3)
    for idx, (key, action) in enumerate(top_actions):
        with cols[idx]:
            saving_text = format_saving_range(savings[key]) if key in savings else "Impact depends on the home"
            st.markdown(
                f"""
                <div class='card'>
                    <span class='badge'>{action['category']}</span>
                    <h4>{action['title']}</h4>
                    <p>{action['recommendation']}</p>
                    <p><strong>Indicative saving:</strong> {saving_text}</p>
                </div>
                """,
                unsafe_allow_html=True,
            )

    st.markdown("### Full recommendation list")
    rows = []
    for key, action in ranked:
        rows.append({
            "Priority": action["priority"],
            "Action": action["title"],
            "Category": action["category"],
            "Cost": action["cost_level"],
            "Impact": action["impact_level"],
            "Indicative annual saving": format_saving_range(savings[key]) if key in savings else "Not monetised in prototype",
        })
    st.dataframe(pd.DataFrame(rows), use_container_width=True, hide_index=True)

    st.markdown("### Savings chart")
    monetised_rows = [
        {"Action": key.replace("_", " ").title(), "Low": val[0], "High": val[1]}
        for key, val in savings.items() if val[1] > 0
    ]
    if monetised_rows:
        chart_df = pd.DataFrame(monetised_rows)
        fig = go.Figure()
        fig.add_trace(go.Bar(x=chart_df["Action"], y=chart_df["Low"], name="Low estimate"))
        fig.add_trace(go.Bar(x=chart_df["Action"], y=chart_df["High"], name="High estimate"))
        fig.update_layout(yaxis_title="Indicative annual saving (A$)", barmode="group", height=420)
        st.plotly_chart(fig, use_container_width=True)

    st.markdown("### Your save-to-upgrade pathway")
    behaviour_low, behaviour_high = estimate_behaviour_saving_pool(savings)
    st.markdown(
        f"""
        <div class='unlock-card'>
            <span class='unlock-badge'>Personalised funding loop</span>
            <h4>Use behaviour savings to fund the next energy upgrade</h4>
            <p>Your estimated no/low-cost behaviour-saving pool is approximately <strong>{_currency(behaviour_low)}–{_currency(behaviour_high)} per year</strong>. The pathway below shows how those savings could fund the next action instead of asking you to spend everything upfront.</p>
        </div>
        """,
        unsafe_allow_html=True,
    )
    for step in build_funding_pathway(inputs, savings):
        st.markdown(
            f"""
            <div class='pathway-step'>
                <h4>{step['stage']}: {step['title']}</h4>
                <p><strong>Logic:</strong> {step['logic']}</p>
                <p><strong>Estimated saving:</strong> {step['saving']}</p>
                <p><strong>Indicative cost:</strong> {step['cost']}</p>
                <p><strong>When it may be unlocked:</strong> {step['unlock']}</p>
            </div>
            """,
            unsafe_allow_html=True,
        )
    st.caption("This pathway is deliberately conservative. It should motivate action without pretending to be a certified bill forecast.")

    st.markdown("### Important limitation")
    st.warning("These results are indicative educational estimates only. A validated version should use local tariffs, climate zone, actual equipment power, hot-water system type, occupancy patterns, and pre/post evaluation data.")

    csv = pd.DataFrame(rows).to_csv(index=False).encode("utf-8")
    st.download_button("Download action plan as CSV", csv, "energy_action_plan.csv", "text/csv", use_container_width=True)

    st.markdown("### Anonymous response record")
    if st.session_state.get("response_saved"):
        st.success(f"Your completed responses have been saved anonymously as {st.session_state.get('participant_id', 'Participant')}.")
    else:
        st.warning("The recommendation page is being shown, but the anonymous response could not be saved. The tool still works, but check Streamlit Secrets, Google Sheet sharing permissions, and requirements.txt.")
        if st.session_state.get("save_error"):
            st.caption(f"Technical detail: {st.session_state.get('save_error')}")
        if st.button("Retry anonymous save", use_container_width=True):
            if save_anonymous_progress_if_needed(savings, ranked, result_text):
                st.rerun()

    st.markdown("### Completion recognition")
    st.info("Optional: if you would like a certificate, type your name below. This name is used only on the on-screen certificate and is not saved to Google Sheets. You can then take a screenshot or print the page.")
    certificate_input = st.text_input(
        "Name to display on certificate only",
        value=st.session_state.get("certificate_display_name", ""),
        placeholder="Type your name here for the certificate",
        key="certificate_display_name_input",
    )
    st.session_state["certificate_display_name"] = certificate_input.strip()
    certificate_name = st.session_state.get("certificate_display_name", "") or st.session_state.get("participant_id", "Anonymous Participant")

    st.markdown(
        f"""
        <div class='certificate-card'>
            <div class='certificate-kicker'>Beta Version 1.0</div>
            <div class='certificate-title'>Certificate of Completion</div>
            <div class='certificate-subtitle'>The Home-energy check-up (Australia)</div>
            <div class='certificate-company'>Tech Innovation Experts</div>
            <div class='certificate-small'>This certificate recognises</div>
            <div class='certificate-name'>{certificate_name}</div>
            <div class='certificate-small'>for completing the home-energy check-up and building a practical, prioritised energy action plan.</div>
            <div class='certificate-meta'>
                <div class='certificate-pill'>Result: {result_text}</div>
                <div class='certificate-pill'>Score: {st.session_state.score}/100</div>
                <div class='certificate-pill'>Date: {completion_date}</div>
            </div>
            <div class='certificate-footer'>Tech Innovation Experts | Providing technology-driven services across Oceania | tinx@gmail.com</div>
            <div class='certificate-disclaimer'>Recognition certificate only. Not a certified energy assessment or accredited NCC/NatHERS rating.</div>
        </div>
        """,
        unsafe_allow_html=True,
    )
    st.caption("This recognition certificate is shown on-screen only. Screenshot or print the page if you want to keep a copy.")



# ---------- Commercial engagement layer: challenge, visuals, and saving logic ----------
RECOMMENDATION_VISUALS = {
    "thermostat": {
        "icon": "🌡️",
        "image": "https://images.unsplash.com/photo-1556912173-3bb406ef7e77?auto=format&fit=crop&w=900&q=80",
        "caption": "Thermostat discipline: keep heating/cooling in a moderate range."
    },
    "leds": {
        "icon": "💡",
        "image": "https://images.unsplash.com/photo-1507473885765-e6ed057f782c?auto=format&fit=crop&w=900&q=80",
        "caption": "LED lighting: low-cost upgrade with quick payback potential."
    },
    "curtains": {
        "icon": "🪟",
        "image": "https://images.unsplash.com/photo-1618221195710-dd6b41faaea6?auto=format&fit=crop&w=900&q=80",
        "caption": "Curtains and blinds: reduce summer heat gain and winter heat loss."
    },
    "draught": {
        "icon": "🚪",
        "image": "https://images.unsplash.com/photo-1505693416388-ac5ce068fe85?auto=format&fit=crop&w=900&q=80",
        "caption": "Draught control: stop paid heating/cooling escaping through gaps."
    },
    "shower": {
        "icon": "🚿",
        "image": "https://images.unsplash.com/photo-1584622650111-993a426fbf0a?auto=format&fit=crop&w=900&q=80",
        "caption": "Hot water behaviour: shorter showers can recover money quickly."
    },
    "standby": {
        "icon": "🔌",
        "image": "https://images.unsplash.com/photo-1621905252507-b35492cc74b4?auto=format&fit=crop&w=900&q=80",
        "caption": "Standby control: stop small loads quietly draining your bill."
    },
    "insulation": {
        "icon": "🏠",
        "image": "https://images.unsplash.com/photo-1560518883-ce09059eeffa?auto=format&fit=crop&w=900&q=80",
        "caption": "Building shell: insulation and envelope upgrades improve long-term performance."
    },
    "cylinder_wrap": {
        "icon": "♨️",
        "image": "https://images.unsplash.com/photo-1621905251918-48416bd8575a?auto=format&fit=crop&w=900&q=80",
        "caption": "Hot-water cylinder wrapping: relevant only for suitable accessible storage systems."
    },
}

ACTION_KEY_TO_VISUAL = {
    "thermostat": "thermostat",
    "leds": "leds",
    "curtains": "curtains",
    "draught_sealing": "draught",
    "shorter_showers": "shower",
    "standby": "standby",
    "insulation_owner": "insulation",
    "insulation_renter": "insulation",
}


def saving_fee_monthly() -> float:
    return float(st.session_state.get("saving_fee", 19.0))


def annual_saving_cost() -> float:
    return saving_fee_monthly() * 12


def roi_summary(low_saving: float, high_saving: float, monthly_fee: float | None = None) -> dict:
    """Compare indicative savings with a possible saving fee.

    This is not a payment system. It is a commercial value framing tool: if the user pays
    X per month, the app shows whether the estimated annual saving opportunity is larger.
    """
    if monthly_fee is None:
        monthly_fee = saving_fee_monthly()
    annual_fee = monthly_fee * 12
    net_low = low_saving - annual_fee
    net_high = high_saving - annual_fee
    multiple_low = (low_saving / annual_fee) if annual_fee > 0 else 0
    multiple_high = (high_saving / annual_fee) if annual_fee > 0 else 0
    return {
        "monthly_fee": monthly_fee,
        "annual_fee": annual_fee,
        "net_low": net_low,
        "net_high": net_high,
        "multiple_low": multiple_low,
        "multiple_high": multiple_high,
    }


def value_bar(label: str, value: str, note: str, icon: str = "💰") -> None:
    st.markdown(
        f"""
        <div class='value-card'>
            <div class='value-icon'>{icon}</div>
            <div>
                <div class='value-label'>{label}</div>
                <div class='value-number'>{value}</div>
                <div class='value-note'>{note}</div>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def episode_header(episode: str, title: str, subtitle: str, icon: str = "💸") -> None:
    st.markdown(
        f"""
        <div class='episode-hero'>
            <div class='episode-token'>{icon}</div>
            <div>
                <div class='episode-label'>{episode}</div>
                <h2>{title}</h2>
                <p>{subtitle}</p>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_payoff_strip(low_saving: float, high_saving: float, context: str = "estimated saving opportunity") -> None:
    """Show the money value without saving framing."""
    st.markdown(
        f"""
        <div class='payoff-strip'>
            <div><strong>Saving target</strong><br><span>{context}</span></div>
            <div><strong>{_currency(low_saving)}–{_currency(high_saving)}</strong><br><span>possible annual recovery</span></div>
            <div><strong>{_currency(low_saving / 12)}–{_currency(high_saving / 12)}</strong><br><span>possible monthly recovery</span></div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def _local_visual_path(visual_key: str) -> Path:
    return ROOT / "assets" / "recommendations" / f"{visual_key}.jpg"


def render_recommendation_visual(visual_key: str, height: int = 190) -> None:
    """Render recommendation image with fixed aspect ratio.

    Local files in assets/recommendations/ are preferred. If they are missing, the app
    falls back to the provided online image URL. All visuals are forced into the same
    16:9 frame so the recommendation cards stay aligned.
    """
    data = RECOMMENDATION_VISUALS.get(visual_key, RECOMMENDATION_VISUALS["thermostat"])
    local_path = _local_visual_path(visual_key)
    try:
        if local_path.exists():
            suffix = local_path.suffix.lower().replace(".", "") or "jpg"
            mime = "jpeg" if suffix in {"jpg", "jpeg"} else suffix
            img_src = f"data:image/{mime};base64,{base64.b64encode(local_path.read_bytes()).decode('utf-8')}"
        else:
            img_src = data["image"]
        st.markdown(
            f"""
            <div class='photo-frame'>
                <img class='reco-img' src="{img_src}" alt="{data['caption']}">
            </div>
            <div class='reco-caption'>{data['icon']} {data['caption']}</div>
            """,
            unsafe_allow_html=True,
        )
    except Exception:
        st.markdown(
            f"""
            <div class='visual-fallback'>
                <div class='visual-icon'>{data['icon']}</div>
                <div>{data['caption']}</div>
            </div>
            """,
            unsafe_allow_html=True,
        )


def saving_range_for_hotspot(key: str) -> tuple[float, float]:
    try:
        savings = estimate_all_savings(current_household_inputs())
    except Exception:
        return (0.0, 0.0)
    action_key = HOTSPOTS[key].get("action", "")
    if key == "insulation" and st.session_state.get("tenure_type") == "Rented":
        action_key = "insulation_renter"
    return savings.get(action_key, (0.0, 0.0)) if isinstance(savings.get(action_key, None), tuple) else (0.0, 0.0)


def commercial_teaser_panel(title: str = "Next advisor step") -> None:
    snap = st.session_state.get("money_snapshot", {})
    low = float(snap.get("waste_low", 0))
    high = float(snap.get("waste_high", 0))
    st.markdown(
        f"""
        <div class='premium-card'>
            <span class='premium-badge'>Next unlock</span>
            <h4>{title}</h4>
            <p>The next stage keeps the user moving: track one action, update the saving estimate, then unlock the next upgrade.</p>
            <p><strong>Current target:</strong> {_currency(low)}–{_currency(high)} possible annual recovery.</p>
        </div>
        """,
        unsafe_allow_html=True,
    )


# Extend CSS after the original CSS block.
st.markdown("""
<style>
.episode-hero {
    display:flex; gap:1rem; align-items:center;
    padding:1.25rem 1.35rem; border-radius:24px;
    background:linear-gradient(135deg,#0F172A 0%,#0F766E 100%);
    color:white; margin:1rem 0 1.15rem 0;
    box-shadow:0 12px 30px rgba(15,23,42,.18);
}
.episode-token {
    width:58px; height:58px; min-width:58px; border-radius:18px;
    display:flex; align-items:center; justify-content:center;
    background:rgba(255,255,255,.15); font-size:1.85rem;
}
.episode-label {font-size:.82rem; letter-spacing:.12em; text-transform:uppercase; font-weight:900; opacity:.82;}
.episode-hero h2 {margin:.15rem 0 .25rem 0; font-size:1.75rem; letter-spacing:-.02em;}
.episode-hero p {margin:0; opacity:.93;}
.value-card {
    display:flex; gap:.75rem; align-items:flex-start;
    padding:1rem; border-radius:18px; background:#FFFFFF;
    border:1px solid #A7F3D0; box-shadow:0 1px 5px rgba(15,23,42,.06);
    min-height:128px;
}
.value-icon {
    width:42px; height:42px; min-width:42px; border-radius:14px;
    background:#ECFDF5; display:flex; align-items:center; justify-content:center; font-size:1.35rem;
}
.value-label {font-size:.82rem; font-weight:800; color:#064E3B; text-transform:uppercase; letter-spacing:.05em;}
.value-number {font-size:1.55rem; font-weight:950; color:#0F172A; margin:.12rem 0;}
.value-note {font-size:.86rem; color:#475569; line-height:1.35;}
.payoff-strip {
    display:grid; grid-template-columns:1fr 1fr 1fr; gap:.85rem;
    padding:1rem; border-radius:18px; background:#FFFBEB; border:1px solid #FDE68A;
    margin:.85rem 0 1rem 0;
}
.payoff-strip strong {color:#78350F; font-size:1rem;}
.payoff-strip span {color:#92400E; font-size:.86rem;}
.premium-card {
    padding:1.1rem; border-radius:20px; background:linear-gradient(135deg,#111827 0%,#312E81 100%);
    color:white; box-shadow:0 12px 30px rgba(15,23,42,.16); margin:.75rem 0;
}
.premium-card h4 {margin:.4rem 0 .25rem 0; font-size:1.18rem;}
.premium-card p {margin:.35rem 0; opacity:.94;}
.premium-badge {display:inline-block; padding:.22rem .6rem; border-radius:999px; background:rgba(255,255,255,.16); font-weight:900; font-size:.76rem;}
.photo-frame img {border-radius:18px;}
.visual-fallback {
    min-height:165px; border-radius:18px; background:#F8FAFC; border:1px dashed #CBD5E1;
    display:flex; flex-direction:column; align-items:center; justify-content:center; text-align:center; color:#334155; padding:1rem;
}
.visual-icon {font-size:2.4rem; margin-bottom:.4rem;}
.series-card {
    padding:1rem; border-radius:18px; background:#F8FAFC; border:1px solid #E2E8F0; margin:.65rem 0;
}
.series-card h4 {margin:0 0 .35rem 0;}
.series-meta {display:flex; gap:.5rem; flex-wrap:wrap; margin-top:.6rem;}
.series-pill {padding:.32rem .55rem; border-radius:999px; background:#ECFDF5; color:#065F46; font-size:.78rem; font-weight:800;}
.hotspot-money {
    padding:.75rem; border-radius:14px; background:#F8FAFC; border:1px solid #CBD5E1; color:#334155; margin:.55rem 0;
}
.photo-frame {
    width:100%;
    aspect-ratio: 16 / 9;
    overflow:hidden;
    border-radius:18px;
    border:1px solid #E2E8F0;
    background:#F8FAFC;
    box-shadow:0 1px 6px rgba(15,23,42,.08);
}
.reco-img {
    width:100%;
    height:100%;
    object-fit:cover;
    display:block;
}
.reco-caption {
    color:#64748B;
    font-size:.82rem;
    line-height:1.45;
    margin:.45rem 0 .15rem 0;
}
@media (max-width: 760px) {
    .payoff-strip {grid-template-columns:1fr;}
    .episode-hero {align-items:flex-start;}
}
</style>
""", unsafe_allow_html=True)


# ---------- Overridden market-ready screens ----------
def welcome_screen() -> None:
    logo_header()
    sidebar_account_card()
    episode_header(
        "Series intro",
        "Find the money leaking from your home energy bill",
        "This advisor turns your energy bill into a staged saving challenge: recover money first, then use the savings to fund the next upgrade.",
        "💸",
    )
    c1, c2, c3 = st.columns(3)
    with c1:
        value_bar("Step 1", "Money leak scan", "Estimate annual cost and avoidable waste before asking for technical details.", "💰")
    with c2:
        value_bar("Step 2", "Energy challenge", "Complete seven short checks to reveal where the bill is leaking.", "⚡")
    with c3:
        value_bar("Step 3", "Upgrade roadmap", "Use recovered savings to fund the next action instead of spending blindly.", "🚀")

    st.markdown("<br>", unsafe_allow_html=True)
    st.warning("Dollar values are indicative decision-support estimates, not guaranteed bill reductions or certified NCC/NatHERS assessment results.")
    if st.button("Start Episode 1 — Find my money leak", type="primary", use_container_width=True):
        next_stage("money")


def money_screen() -> None:
    logo_header()
    episode_header(
        "Episode 1",
        "Energy Money Leak Scan",
        "Answer a few money-first questions. The app will compare your current bill pathway with a strategy pathway.",
        "💰",
    )

    with st.form("money_snapshot_form"):
        c1, c2, c3 = st.columns(3)
        with c1:
            monthly_bill = st.number_input("Approximate monthly energy bill (A$)", min_value=0.0, max_value=3000.0, value=float(st.session_state.get("monthly_bill", 250.0)), step=10.0)
            dwelling_options = ["Small apartment / unit", "Townhouse / small house", "Detached house", "Large detached house"]
            dwelling_type = st.selectbox("What best describes the home?", dwelling_options, index=dwelling_options.index(st.session_state.get("dwelling_type", "Detached house")) if st.session_state.get("dwelling_type", "Detached house") in dwelling_options else 2)
        with c2:
            household_size = st.radio("People in the home", ["1", "2", "3-4", "5+"], horizontal=True, index=["1", "2", "3-4", "5+"].index(st.session_state.get("household_size", "3-4")) if st.session_state.get("household_size", "3-4") in ["1", "2", "3-4", "5+"] else 2)
            condition_options = ["Newer / efficient", "Average / not sure", "Older or draughty"]
            home_condition = st.radio("How does the home feel thermally?", condition_options, index=condition_options.index(st.session_state.get("home_condition", "Average / not sure")) if st.session_state.get("home_condition", "Average / not sure") in condition_options else 1)
        with c3:
            bill_problem = st.selectbox("Where does the bill hurt most?", ["High winter bill", "High summer bill", "High hot-water bill", "Not sure"], index=["High winter bill", "High summer bill", "High hot-water bill", "Not sure"].index(st.session_state.get("bill_problem", "Not sure")) if st.session_state.get("bill_problem", "Not sure") in ["High winter bill", "High summer bill", "High hot-water bill", "Not sure"] else 3)
            st.markdown("<div class='small-muted'>This is deliberately short. The goal is to show money first, then unlock the deeper inspection.</div>", unsafe_allow_html=True)
        submitted = st.form_submit_button("Reveal my saving opportunity", type="primary", use_container_width=True)

    if submitted or "money_snapshot" in st.session_state:
        if submitted:
            st.session_state["monthly_bill"] = monthly_bill
            st.session_state["household_size"] = household_size
            st.session_state["bill_problem"] = bill_problem
            st.session_state["dwelling_type"] = dwelling_type
            st.session_state["home_condition"] = home_condition
            st.session_state["money_snapshot"] = estimate_money_snapshot(monthly_bill, household_size, bill_problem, dwelling_type, home_condition)

        snap = st.session_state["money_snapshot"]
        st.markdown(
            f"""
            <div class='money-hero'>
                <h2>Your bill may contain recoverable energy money</h2>
                <p>Based on your starting scenario, your estimated annual energy spend is:</p>
                <div class='money-number'>{_currency(snap['annual_bill'])}</div>
                <p>First-stage recoverable opportunity: <strong>{_currency(snap['waste_low'])}–{_currency(snap['waste_high'])} per year</strong>.</p>
                <p>The next steps show which actions can reduce the leak first and what those savings may fund next.</p>
                <div class='money-sub'>Indicative decision-support estimate only. No saving is guaranteed.</div>
            </div>
            """,
            unsafe_allow_html=True,
        )
        c1, c2, c3 = st.columns(3)
        with c1:
            value_bar("Current annual spend", _currency(snap["annual_bill"]), "This is your starting money baseline.", "💳")
        with c2:
            value_bar("Possible annual recovery", f"{_currency(snap['waste_low'])}–{_currency(snap['waste_high'])}", "This is the saving prize the challenge is trying to unlock.", "💰")
        with c3:
            value_bar("Possible monthly recovery", f"{_currency(snap['monthly_low'])}–{_currency(snap['monthly_high'])}", "The short-term money target for the first challenge.", "📈")

        render_payoff_strip(snap["waste_low"], snap["waste_high"], "first-stage recoverable opportunity")

        st.markdown("### Your annual energy-cost pathway")
        st.caption("The current line is based on the bill you entered. The strategy line shows how the bill could move if the recommended behaviour and low-cost actions are followed. The band is a benchmark-style efficient operating range, not a compliance result.")
        st.plotly_chart(energy_pathway_figure(), use_container_width=True)

        st.markdown("### What the next episodes unlock")
        c4, c5, c6 = st.columns(3)
        with c4:
            st.markdown("<div class='series-card'><h4>Episode 2 — The inspection</h4><p>Find which household habits or features are costing money.</p><div class='series-meta'><span class='series-pill'>7 checks</span><span class='series-pill'>score points</span></div></div>", unsafe_allow_html=True)
        with c5:
            st.markdown("<div class='series-card'><h4>Episode 3 — The action plan</h4><p>Rank actions by saving potential, cost level, and fit to your household.</p><div class='series-meta'><span class='series-pill'>money first</span><span class='series-pill'>personalised</span></div></div>", unsafe_allow_html=True)
        with c6:
            st.markdown("<div class='series-card'><h4>Episode 4 — Upgrade roadmap</h4><p>Use recovered money to fund the next efficiency move.</p><div class='series-meta'><span class='series-pill'>payback</span><span class='series-pill'>next unlock</span></div></div>", unsafe_allow_html=True)

        if st.button("Start Episode 2 — Inspect where the money is leaking", type="primary", use_container_width=True):
            next_stage("profile")


def profile_screen() -> None:
    episode_header(
        "Episode 2 setup",
        "Set the rules of your saving challenge",
        "These assumptions personalise the money calculation and stop the advisor from giving generic recommendations.",
        "🎯",
    )
    snap = st.session_state.get("money_snapshot", {})
    if snap:
        render_payoff_strip(float(snap.get("waste_low", 0)), float(snap.get("waste_high", 0)), "available target before detailed inspection")

    with st.form("profile_form"):
        c1, c2 = st.columns(2)
        with c1:
            household_size_options = ["1", "2", "3-4", "5+"]
            household_size = st.radio("How many people live in the home?", household_size_options, horizontal=True, index=household_size_options.index(st.session_state.get("household_size", "3-4")) if st.session_state.get("household_size", "3-4") in household_size_options else 2)
            tenure_type = st.radio("Is the home rented or owned?", ["Rented", "Owned"], horizontal=True)
            bill_problem_options = ["High winter bill", "High summer bill", "High hot-water bill", "Not sure"]
            bill_problem = st.selectbox("Main bill pressure", bill_problem_options, index=bill_problem_options.index(st.session_state.get("bill_problem", "Not sure")) if st.session_state.get("bill_problem", "Not sure") in bill_problem_options else 3)
            dwelling_type = st.selectbox("Home type", ["Small apartment / unit", "Townhouse / small house", "Detached house", "Large detached house"], index=["Small apartment / unit", "Townhouse / small house", "Detached house", "Large detached house"].index(st.session_state.get("dwelling_type", "Detached house")) if st.session_state.get("dwelling_type", "Detached house") in ["Small apartment / unit", "Townhouse / small house", "Detached house", "Large detached house"] else 2)
        with c2:
            hvac_type = st.selectbox("Main heating/cooling system", ["Split-system AC", "Gas heater", "Portable electric heater", "Ducted system", "Not sure"])
            solar_status = st.radio("Does the home have solar panels?", ["Yes", "No", "Not sure"], horizontal=True)
            monthly_bill = st.number_input("Approximate monthly energy bill (A$)", min_value=0.0, max_value=3000.0, value=float(st.session_state.get("monthly_bill", 250.0)), step=10.0)
            condition_options = ["Newer / efficient", "Average / not sure", "Older or draughty"]
            home_condition = st.radio("Thermal feel of the home", condition_options, index=condition_options.index(st.session_state.get("home_condition", "Average / not sure")) if st.session_state.get("home_condition", "Average / not sure") in condition_options else 1)
        st.markdown("#### Challenge assumptions")
        c3, c4, c5 = st.columns(3)
        with c3:
            electricity_price = st.number_input("Electricity price (A$/kWh)", 0.05, 1.50, float(st.session_state.get("electricity_price", 0.35)), 0.01)
            thermostat_degrees = st.slider("Thermostat improvement from current setting (°C)", 0, 6, int(st.session_state.get("thermostat_degrees", 2)))
        with c4:
            shower_current = st.slider("Current average shower time (minutes)", 2, 20, int(st.session_state.get("shower_current", 10)))
            shower_target = st.slider("Target shower time (minutes)", 2, 12, int(st.session_state.get("shower_target", 4)))
            showers_per_person = st.slider("Showers per person per day", 0.5, 2.0, float(st.session_state.get("showers_per_person", 1.0)), 0.1)
        with c5:
            old_bulbs = st.slider("Old halogen/incandescent bulbs used often", 0, 30, int(st.session_state.get("old_bulbs", 8)))
            bulb_hours = st.slider("Average hours per bulb per day", 0.5, 10.0, float(st.session_state.get("bulb_hours", 3.0)), 0.5)
            standby_devices = st.slider("Standby devices to manage", 0, 30, int(st.session_state.get("standby_devices", 8)))
        submitted = st.form_submit_button("Start the Energy Saving Challenge", type="primary", use_container_width=True)

    if submitted:
        st.session_state.update({
            "household_size": household_size,
            "tenure_type": tenure_type,
            "bill_problem": bill_problem,
            "dwelling_type": dwelling_type,
            "home_condition": home_condition,
            "hvac_type": hvac_type,
            "solar_status": solar_status,
            "monthly_bill": monthly_bill,
                        "electricity_price": electricity_price,
            "shower_current": shower_current,
            "shower_target": shower_target,
            "showers_per_person": showers_per_person,
            "old_bulbs": old_bulbs,
            "bulb_hours": bulb_hours,
            "standby_devices": standby_devices,
            "thermostat_degrees": thermostat_degrees,
            "money_snapshot": estimate_money_snapshot(monthly_bill, household_size, bill_problem, dwelling_type, home_condition),
        })
        next_stage("inspection")


def inspection_screen() -> None:
    episode_header(
        "Episode 2",
        "Inspect the seven money leaks",
        "Each check gives points and shows the likely saving logic. The final episode turns your answers into a money-value roadmap.",
        "⚡",
    )
    sidebar_status()

    snap = st.session_state.get("money_snapshot", {})
    if snap:
        render_payoff_strip(float(snap.get("waste_low", 0)), float(snap.get("waste_high", 0)), "target saving opportunity during this challenge")

    c1, c2 = st.columns([0.62, 0.38])
    with c1:
        tab1, tab2, tab3 = st.tabs(["💡 Living room", "🚿 Bathroom", "🏠 Building shell"])
        with tab1:
            for key in ["thermostat", "leds", "curtains", "standby"]:
                render_hotspot(key)
        with tab2:
            render_hotspot("shower")
        with tab3:
            render_hotspot("draught")
            render_hotspot("insulation")
    with c2:
        st.plotly_chart(gauge(st.session_state.bill_risk, "Bill risk"), use_container_width=True)
        st.plotly_chart(gauge(st.session_state.comfort, "Comfort readiness"), use_container_width=True)
        commercial_teaser_panel("Next episode unlock")

    if len(st.session_state.completed_hotspots) >= 7:
        st.info("When you unlock the recommendations, completed responses are saved anonymously for tool improvement. No name, email address, phone number, or contact detail is collected or stored.")
        if st.button("Unlock Episode 3 — My recommendations and saving pathway", type="primary", use_container_width=True):
            inputs = current_household_inputs()
            savings = estimate_all_savings(inputs)
            ranked = current_ranked_actions()
            result_text = score_label(st.session_state.get("score", 0))
            save_anonymous_progress_if_needed(savings, ranked, result_text)
            next_stage("plan")
    else:
        st.info("Complete all seven checks to unlock the money roadmap.")


def render_hotspot(key: str) -> None:
    hotspot = HOTSPOTS[key]
    done = key in st.session_state.completed_hotspots
    feedback = st.session_state.last_feedback.get(key)
    visual_key = ACTION_KEY_TO_VISUAL.get(hotspot.get("action", ""), key)
    visual_data = RECOMMENDATION_VISUALS.get(visual_key, {})
    low, high = saving_range_for_hotspot(key)
    icon = visual_data.get("icon", "⚡")
    with st.expander(("✅ " if done else f"{icon} ") + hotspot["label"] + f" — {hotspot['room']}", expanded=True if feedback else not done):
        left, right = st.columns([0.58, 0.42])
        with left:
            st.write(f"**Money-leak check:** {hotspot['question']}")
            st.markdown(
                f"""
                <div class='hotspot-money'>
                    <strong>Potential saving lens:</strong> {format_saving_range((low, high)) if high > 0 else "Impact depends on your home and behaviour."}<br>
                    <strong>Points available:</strong> {hotspot['points']} energy-saving points
                </div>
                """,
                unsafe_allow_html=True,
            )
            answer = st.radio("Choose the best move", hotspot["options"], key=f"answer_{key}", index=None, disabled=done)
            if st.button("Lock in this move", key=f"check_{key}", disabled=answer is None or done):
                update_for_answer(key, answer)
                st.rerun()
        with right:
            render_recommendation_visual(visual_key)

        if feedback:
            if feedback["is_correct"]:
                st.success(
                    "**Good move — this reduces the leak**\n\n"
                    f"**Your selection:** {feedback['selected']}\n\n"
                    f"{feedback['message']}"
                )
            else:
                st.error(
                    "**Money still leaking**\n\n"
                    f"**Your selection:** {feedback['selected']}\n\n"
                    f"**Better move:** {feedback['correct']}\n\n"
                    f"{feedback['message']}"
                )
        elif done:
            st.caption("This hotspot has already been scored.")


def plan_screen() -> None:
    episode_header(
        "Episode 3",
        "Your money-first energy roadmap",
        "The goal is simple: recover avoidable bill waste, compare it with the advisor cost, and use savings to fund the next upgrade.",
        "🚀",
    )
    sidebar_status()

    inputs = current_household_inputs()
    savings = estimate_all_savings(inputs)
    ranked = current_ranked_actions()
    top_actions = top_three_actions(ranked)

    result_text = score_label(st.session_state.score)
    completion_date = date.today().strftime("%d %B %Y")
    total_low = int(sum(v[0] for v in savings.values() if isinstance(v, tuple)))
    total_high = int(sum(v[1] for v in savings.values() if isinstance(v, tuple)))
    st.session_state["result_category"] = result_text
    st.session_state["estimated_annual_savings"] = f"A${total_low:,}–A${total_high:,}"

    c1, c2, c3 = st.columns(3)
    with c1:
        value_bar("Your score", f"{st.session_state.score}/100", f"{result_text}. The higher the score, the fewer obvious leaks remain.", "🏆")
    with c2:
        value_bar("Annual saving estimate", f"{_currency(total_low)}–{_currency(total_high)}", "Combined indicative opportunity from monetised actions.", "💰")
    with c3:
        value_bar("Possible monthly recovery", f"{_currency(total_low / 12)}–{_currency(total_high / 12)}", "A practical monthly target if actions are followed consistently.", "📈")

    render_payoff_strip(total_low, total_high, "combined monetised action estimate")

    st.markdown("### Top three money moves")
    cols = st.columns(3)
    for idx, (key, action) in enumerate(top_actions):
        with cols[idx]:
            visual_key = ACTION_KEY_TO_VISUAL.get(key, key)
            render_recommendation_visual(visual_key)
            saving_text = format_saving_range(savings[key]) if key in savings else "Impact depends on the home"
            st.markdown(
                f"""
                <div class='card'>
                    <span class='badge'>{action['category']}</span>
                    <h4>{action['title']}</h4>
                    <p>{action['recommendation']}</p>
                    <p><strong>Indicative saving:</strong> {saving_text}</p>
                </div>
                """,
                unsafe_allow_html=True,
            )

    st.markdown("### Episode 4 preview — the next saving loop")
    commercial_teaser_panel("Monthly saving loop")
    st.markdown(
        """
        <div class='series-card'>
            <h4>Ongoing roadmap concept</h4>
            <p>The first result gives a starting roadmap. The next loop would keep the user moving: monthly check-ins, proof-of-action photos, revised savings, next upgrade unlock, landlord letter for renters, and a running payback dashboard.</p>
            <div class='series-meta'><span class='series-pill'>monthly challenge</span><span class='series-pill'>upgrade unlocks</span><span class='series-pill'>payback tracking</span></div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    st.markdown("### Full recommendation list")
    rows = []
    for key, action in ranked:
        rows.append({
            "Priority": action["priority"],
            "Action": action["title"],
            "Category": action["category"],
            "Cost": action["cost_level"],
            "Impact": action["impact_level"],
            "Indicative annual saving": format_saving_range(savings[key]) if key in savings else "Not monetised in prototype",
        })
    st.dataframe(pd.DataFrame(rows), use_container_width=True, hide_index=True)

    st.markdown("### Savings chart")
    monetised_rows = [
        {"Action": key.replace("_", " ").title(), "Low": val[0], "High": val[1]}
        for key, val in savings.items() if isinstance(val, tuple) and val[1] > 0
    ]
    if monetised_rows:
        chart_df = pd.DataFrame(monetised_rows)
        fig = go.Figure()
        fig.add_trace(go.Bar(x=chart_df["Action"], y=chart_df["Low"], name="Low estimate"))
        fig.add_trace(go.Bar(x=chart_df["Action"], y=chart_df["High"], name="High estimate"))
        fig.update_layout(yaxis_title="Indicative annual saving (A$)", barmode="group", height=420)
        st.plotly_chart(fig, use_container_width=True)

    st.markdown("### Your save-to-upgrade pathway")
    behaviour_low, behaviour_high = estimate_behaviour_saving_pool(savings)
    st.markdown(
        f"""
        <div class='unlock-card'>
            <span class='unlock-badge'>Personalised funding loop</span>
            <h4>Use behaviour savings to fund the next energy upgrade</h4>
            <p>Your estimated no/low-cost behaviour-saving pool is approximately <strong>{_currency(behaviour_low)}–{_currency(behaviour_high)} per year</strong>. The pathway below shows how those savings could fund the next action instead of asking you to spend everything upfront.</p>
        </div>
        """,
        unsafe_allow_html=True,
    )
    for step in build_funding_pathway(inputs, savings):
        st.markdown(
            f"""
            <div class='pathway-step'>
                <h4>{step['stage']}: {step['title']}</h4>
                <p><strong>Logic:</strong> {step['logic']}</p>
                <p><strong>Estimated saving:</strong> {step['saving']}</p>
                <p><strong>Indicative cost:</strong> {step['cost']}</p>
                <p><strong>When it may be unlocked:</strong> {step['unlock']}</p>
            </div>
            """,
            unsafe_allow_html=True,
        )
        if "hot-water cylinder" in step["title"].lower() or "cylinder" in step["logic"].lower():
            render_recommendation_visual("cylinder_wrap")
        elif "draught" in step["title"].lower() or "door" in step["logic"].lower():
            render_recommendation_visual("draught")
        elif "insulation" in step["title"].lower():
            render_recommendation_visual("insulation")

    csv = pd.DataFrame(rows).to_csv(index=False).encode("utf-8")
    st.download_button("Download action plan as CSV", csv, "energy_action_plan.csv", "text/csv", use_container_width=True)

    st.markdown("### Completion recognition")
    st.info("Optional: if you would like a certificate, type your name below. This name is used only on the on-screen certificate and is not saved to Google Sheets.")
    certificate_input = st.text_input(
        "Name to display on certificate only",
        value=st.session_state.get("certificate_display_name", ""),
        placeholder="Type your name here for the certificate",
        key="certificate_display_name_input",
    )
    st.session_state["certificate_display_name"] = certificate_input.strip()
    certificate_name = st.session_state.get("certificate_display_name", "") or st.session_state.get("participant_id", "Anonymous Participant")

    st.markdown(
        f"""
        <div class='certificate-card'>
            <div class='certificate-kicker'>Beta Version 1.0</div>
            <div class='certificate-title'>Certificate of Completion</div>
            <div class='certificate-subtitle'>The Home-energy check-up (Australia)</div>
            <div class='certificate-company'>Tech Innovation Experts</div>
            <div class='certificate-small'>This certificate recognises</div>
            <div class='certificate-name'>{certificate_name}</div>
            <div class='certificate-small'>for completing the home-energy check-up and building a practical, prioritised energy saving roadmap.</div>
            <div class='certificate-meta'>
                <div class='certificate-pill'>Result: {result_text}</div>
                <div class='certificate-pill'>Score: {st.session_state.score}/100</div>
                <div class='certificate-pill'>Date: {completion_date}</div>
            </div>
            <div class='certificate-footer'>Tech Innovation Experts | Providing technology-driven services across Oceania | tinx@gmail.com</div>
            <div class='certificate-disclaimer'>Recognition certificate only. Not a certified energy assessment or accredited NCC/NatHERS rating.</div>
        </div>
        """,
        unsafe_allow_html=True,
    )


# ---------- Personalised account platform layer ----------
def get_supabase_client():
    """Create a Supabase client from Streamlit Secrets.

    Required Streamlit Secrets:
    [supabase]
    url = "https://YOUR_PROJECT_ID.supabase.co"
    anon_key = "YOUR_SUPABASE_ANON_PUBLIC_KEY"

    Important:
    Row Level Security policies use auth.uid(). For that to work, the Supabase
    client must carry the logged-in user's access token. Otherwise Supabase sees
    the request as anonymous and blocks inserts into tables such as energy_scans.
    """
    try:
        from supabase import create_client

        if "supabase" not in st.secrets:
            st.session_state["supabase_error"] = "Missing [supabase] section in Streamlit Secrets."
            return None

        url = str(st.secrets["supabase"].get("url", "")).strip()
        anon_key = str(st.secrets["supabase"].get("anon_key", "")).strip()

        if not url or "YOUR_PROJECT" in url or "YOUR_PROJECT_ID" in url:
            st.session_state["supabase_error"] = "Supabase URL is missing or still uses the placeholder value."
            return None
        if not url.startswith("https://") or ".supabase.co" not in url:
            st.session_state["supabase_error"] = "Supabase URL must look like: https://your-project-id.supabase.co"
            return None
        if not anon_key or "YOUR_SUPABASE" in anon_key:
            st.session_state["supabase_error"] = "Supabase anon_key is missing or still uses the placeholder value."
            return None

        client = create_client(url, anon_key)

        # Attach the logged-in user's JWT to database requests so RLS sees auth.uid().
        access_token = st.session_state.get("auth_access_token")
        refresh_token = st.session_state.get("auth_refresh_token")
        if access_token:
            try:
                if refresh_token:
                    client.auth.set_session(access_token, refresh_token)
            except Exception:
                # Different supabase-py versions expose token attachment differently.
                pass
            try:
                client.postgrest.auth(access_token)
            except Exception:
                pass
            try:
                client.rest.auth(access_token)
            except Exception:
                pass

        return client

    except Exception as exc:
        st.session_state["supabase_error"] = str(exc)
        return None


def is_logged_in() -> bool:
    return bool(st.session_state.get("auth_user_id"))


def auth_user_label() -> str:
    return st.session_state.get("auth_email") or "Your household account"


def auth_panel(compact: bool = False) -> None:
    """Render login/create-account controls.

    Account is now required before the user can start the energy pathway. This avoids
    anonymous guest journeys and ensures every roadmap can be saved to a household project.
    """
    st.markdown(
        """
        <style>
        .account-note {
            padding:1rem; border-radius:18px; background:#F8FAFC; border:1px solid #CBD5E1;
            color:#334155; margin:.75rem 0 1rem 0;
        }
        .account-note strong {color:#0F172A;}
        .login-mini-grid {
            display:grid; grid-template-columns: repeat(3, 1fr); gap:.75rem; margin:.75rem 0 1rem 0;
        }
        .login-mini-card {
            padding:.85rem; border-radius:16px; background:white; border:1px solid #E2E8F0;
            box-shadow:0 1px 4px rgba(15,23,42,.05); text-align:center;
        }
        .login-mini-icon {font-size:1.55rem; margin-bottom:.25rem;}
        .login-mini-title {font-weight:800; color:#0F172A; font-size:.88rem;}
        .login-mini-text {color:#64748B; font-size:.78rem; line-height:1.35; margin-top:.15rem;}
        .project-box {
            padding:1rem; border-radius:18px; background:#ECFDF5; border:1px solid #A7F3D0;
            color:#064E3B; margin:.85rem 0;
        }
        .locked-project {
            padding:1rem; border-radius:18px; background:#FFFBEB; border:1px solid #FDE68A;
            color:#92400E; margin:.85rem 0;
        }
        @media (max-width: 760px) {.login-mini-grid {grid-template-columns: 1fr;}}
        </style>
        """,
        unsafe_allow_html=True,
    )

    if is_logged_in():
        st.success(f"Logged in as {auth_user_label()}")
        c1, c2, c3 = st.columns(3)
        with c1:
            if st.button("Start Energy Money Leak Scan", type="primary", use_container_width=True, key="start_after_login_btn"):
                next_stage("money")
        with c2:
            if st.button("Open my dashboard", use_container_width=True, key="open_dashboard_btn"):
                next_stage("dashboard")
        with c3:
            if st.button("Log out", use_container_width=True, key="logout_btn"):
                for key in ["auth_user_id", "auth_email", "auth_access_token", "auth_refresh_token"]:
                    st.session_state.pop(key, None)
                st.rerun()
        return

    st.markdown(
        """
        <div class='account-note'>
            <strong>Account required before starting.</strong><br>
            Create or log in to a household account so your scan, recommendations, monthly bills, and action progress can be saved under your own energy project.
        </div>
        <div class='login-mini-grid'>
            <div class='login-mini-card'><div class='login-mini-icon'>👤</div><div class='login-mini-title'>Personal profile</div><div class='login-mini-text'>Save your household assumptions and preferences.</div></div>
            <div class='login-mini-card'><div class='login-mini-icon'>🏠</div><div class='login-mini-title'>Energy project</div><div class='login-mini-text'>Track Home 1 now; multi-home projects can be added later.</div></div>
            <div class='login-mini-card'><div class='login-mini-icon'>📊</div><div class='login-mini-title'>Progress dashboard</div><div class='login-mini-text'>Return monthly and update bills, actions, and comfort.</div></div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    login_tab, signup_tab, reset_tab = st.tabs(["🔐 Log in", "✨ Create account", "🔁 Reset password"])

    with login_tab:
        with st.form("login_form"):
            email = st.text_input("Email", key="login_email")
            password = st.text_input("Password", type="password", key="login_password")
            submitted = st.form_submit_button("Log in and continue", type="primary", use_container_width=True)
        if submitted:
            supabase = get_supabase_client()
            if supabase is None:
                st.error("Supabase is not configured yet. Add Supabase secrets in Streamlit Cloud.")
                if st.session_state.get("supabase_error"):
                    st.caption(st.session_state["supabase_error"])
            else:
                try:
                    result = supabase.auth.sign_in_with_password({"email": email, "password": password})
                    user = result.user
                    session = result.session
                    st.session_state["auth_user_id"] = user.id
                    st.session_state["auth_email"] = user.email
                    if session:
                        st.session_state["auth_access_token"] = session.access_token
                        st.session_state["auth_refresh_token"] = session.refresh_token
                    st.success("Logged in successfully.")
                    next_stage("dashboard")
                except Exception as exc:
                    st.error("Login failed. Check the email/password and Supabase configuration.")
                    st.caption("Most likely causes: incorrect Supabase URL, missing anon key, Supabase project paused, or Streamlit Cloud Secrets not saved/redeployed.")
                    st.caption(str(exc))

    with signup_tab:
        with st.form("signup_form"):
            email = st.text_input("Email", key="signup_email")
            password = st.text_input("Password", type="password", key="signup_password")
            household_nickname = st.text_input("Household / project nickname", value="Home 1", key="signup_home")
            st.markdown(
                "<div class='project-box'><strong>Project setup:</strong> this version creates one active household project. Later, you can enable additional homes as a paid or advanced feature.</div>",
                unsafe_allow_html=True,
            )
            submitted = st.form_submit_button("Create account and start", type="primary", use_container_width=True)
        if submitted:
            supabase = get_supabase_client()
            if supabase is None:
                st.error("Supabase is not configured yet. Add Supabase secrets in Streamlit Cloud.")
                if st.session_state.get("supabase_error"):
                    st.caption(st.session_state["supabase_error"])
            else:
                try:
                    result = supabase.auth.sign_up({"email": email, "password": password})
                    user = result.user
                    if user:
                        st.session_state["auth_user_id"] = user.id
                        st.session_state["auth_email"] = user.email
                        st.session_state["household_nickname"] = household_nickname or "Home 1"
                        save_profile_to_supabase(household_nickname=household_nickname or "Home 1")
                        st.success("Account created. If email confirmation is enabled in Supabase, check your inbox.")
                        next_stage("money")
                    else:
                        st.warning("Account request submitted. Check your email if confirmation is enabled.")
                except Exception as exc:
                    st.error("Account creation failed.")
                    st.caption("Most likely causes: incorrect Supabase URL, missing anon key, Supabase project paused, or Streamlit Cloud Secrets not saved/redeployed.")
                    st.caption(str(exc))

    with reset_tab:
        st.info("Enter your account email and we will ask Supabase to send a password reset link.")
        with st.form("reset_password_form"):
            reset_email = st.text_input("Account email", key="reset_email")
            submitted = st.form_submit_button("Send password reset link", use_container_width=True)
        if submitted:
            supabase = get_supabase_client()
            if supabase is None:
                st.error("Supabase is not configured yet. Add Supabase secrets in Streamlit Cloud.")
                if st.session_state.get("supabase_error"):
                    st.caption(st.session_state["supabase_error"])
            else:
                try:
                    try:
                        supabase.auth.reset_password_email(reset_email)
                    except AttributeError:
                        supabase.auth.reset_password_for_email(reset_email)
                    st.success("If this email exists in the system, a password reset link has been sent.")
                except Exception as exc:
                    st.error("Password reset request failed.")
                    st.caption(str(exc))




def save_profile_to_supabase(household_nickname: str | None = None) -> bool:
    if not is_logged_in():
        return False
    supabase = get_supabase_client()
    if supabase is None:
        return False

    profile = {
        "user_id": st.session_state["auth_user_id"],
        "email": st.session_state.get("auth_email"),
        "household_nickname": household_nickname or st.session_state.get("household_nickname", "My Home"),
        "household_size": st.session_state.get("household_size"),
        "tenure_type": st.session_state.get("tenure_type"),
        "dwelling_type": st.session_state.get("dwelling_type"),
        "home_condition": st.session_state.get("home_condition"),
        "bill_problem": st.session_state.get("bill_problem"),
        "updated_at": datetime.utcnow().isoformat(),
    }
    try:
        supabase.table("profiles").upsert(profile, on_conflict="user_id").execute()
        return True
    except Exception as exc:
        st.session_state["supabase_error"] = str(exc)
        return False


def save_scan_to_supabase(savings: dict, ranked: list, result_text: str) -> str | None:
    """Save the completed scan, answers, and recommendations to Supabase."""
    if not is_logged_in():
        return None
    supabase = get_supabase_client()
    if supabase is None:
        return None
    if not st.session_state.get("auth_access_token"):
        st.session_state["supabase_error"] = "Login session token is missing. Please log out and log in again."
        return None

    active_project_id = ensure_default_project()

    total_low = int(sum(v[0] for v in savings.values() if isinstance(v, tuple)))
    total_high = int(sum(v[1] for v in savings.values() if isinstance(v, tuple)))
    scan = {
        "user_id": st.session_state["auth_user_id"],
        "project_id": active_project_id,
        "created_at": datetime.utcnow().isoformat(),
        "monthly_bill": float(st.session_state.get("monthly_bill", 0) or 0),
        "annual_bill_estimate": float(st.session_state.get("monthly_bill", 0) or 0) * 12,
        "saving_low": total_low,
        "saving_high": total_high,
        "bill_problem": st.session_state.get("bill_problem"),
        "home_condition": st.session_state.get("home_condition"),
        "dwelling_type": st.session_state.get("dwelling_type"),
        "score": int(st.session_state.get("score", 0)),
        "result_category": result_text,
        "money_snapshot": json.dumps(st.session_state.get("money_snapshot", {})),
    }

    try:
        save_profile_to_supabase()
        inserted = supabase.table("energy_scans").insert(scan).execute()
        scan_id = inserted.data[0]["scan_id"] if inserted.data and "scan_id" in inserted.data[0] else inserted.data[0]["id"]

        answer_rows = []
        for key, hotspot in HOTSPOTS.items():
            answer_rows.append({
                "scan_id": scan_id,
                "user_id": st.session_state["auth_user_id"],
                "hotspot_key": key,
                "selected_answer": st.session_state.get(f"{key}_answer"),
                "is_correct": st.session_state.get(f"{key}_correct"),
                "points": hotspot.get("points", 0),
            })
        if answer_rows:
            supabase.table("answers").insert(answer_rows).execute()

        reco_rows = []
        for key, action in ranked:
            low, high = savings.get(key, (0, 0)) if isinstance(savings.get(key, None), tuple) else (0, 0)
            reco_rows.append({
                "scan_id": scan_id,
                "user_id": st.session_state["auth_user_id"],
                "action_key": key,
                "title": action.get("title"),
                "category": action.get("category"),
                "cost_level": action.get("cost_level"),
                "impact_level": action.get("impact_level"),
                "priority": action.get("priority"),
                "estimated_saving_low": int(low),
                "estimated_saving_high": int(high),
                "status": "Not started",
            })
        if reco_rows:
            supabase.table("recommendations").insert(reco_rows).execute()

        st.session_state["last_saved_scan_id"] = scan_id
        return str(scan_id)
    except Exception as exc:
        st.session_state["supabase_error"] = str(exc)
        return None


def load_user_dashboard_data() -> dict:
    """Load scans, recommendations, and check-ins for the logged-in user."""
    empty = {"scans": [], "recommendations": [], "checkins": []}
    if not is_logged_in():
        return empty
    supabase = get_supabase_client()
    if supabase is None:
        return empty
    uid = st.session_state["auth_user_id"]
    try:
        active_project_id = ensure_default_project()
        scans_q = supabase.table("energy_scans").select("*").eq("user_id", uid)
        rec_q = supabase.table("recommendations").select("*").eq("user_id", uid)
        check_q = supabase.table("monthly_checkins").select("*").eq("user_id", uid)
        if active_project_id:
            scans_q = scans_q.eq("project_id", active_project_id)
            check_q = check_q.eq("project_id", active_project_id)
        scans = scans_q.order("created_at", desc=True).limit(10).execute().data or []
        recommendations = rec_q.order("created_at", desc=True).limit(50).execute().data or []
        checkins = check_q.order("checkin_month", desc=False).limit(24).execute().data or []
        return {"scans": scans, "recommendations": recommendations, "checkins": checkins}
    except Exception as exc:
        st.session_state["supabase_error"] = str(exc)
        return empty




# ---------- Multi-project household management ----------
def clear_current_scan_state() -> None:
    """Clear only current scan/check-up state while keeping login and project info."""
    keep_keys = {
        "auth_user_id", "auth_email", "auth_access_token", "auth_refresh_token",
        "active_project_id", "active_project_name", "household_nickname",
        "supabase_error"
    }
    kept = {k: st.session_state[k] for k in keep_keys if k in st.session_state}
    for key in list(st.session_state.keys()):
        if key not in kept:
            del st.session_state[key]
    initialise_state()
    for k, v in kept.items():
        st.session_state[k] = v


def load_user_projects() -> list[dict]:
    if not is_logged_in():
        return []
    supabase = get_supabase_client()
    if supabase is None:
        return []
    try:
        return (
            supabase.table("household_projects")
            .select("*")
            .eq("user_id", st.session_state["auth_user_id"])
            .order("created_at", desc=False)
            .execute()
            .data
            or []
        )
    except Exception as exc:
        st.session_state["supabase_error"] = str(exc)
        return []


def ensure_default_project() -> str | None:
    if not is_logged_in():
        return None

    if st.session_state.get("active_project_id"):
        return st.session_state["active_project_id"]

    projects = load_user_projects()
    if projects:
        project = projects[0]
        st.session_state["active_project_id"] = project.get("project_id")
        st.session_state["active_project_name"] = project.get("project_name", "Home 1")
        st.session_state["household_nickname"] = project.get("project_name", "Home 1")
        return st.session_state["active_project_id"]

    supabase = get_supabase_client()
    if supabase is None:
        return None

    try:
        inserted = (
            supabase.table("household_projects")
            .insert({
                "user_id": st.session_state["auth_user_id"],
                "project_name": st.session_state.get("household_nickname", "Home 1"),
                "project_type": "Primary home",
                "is_active": True,
            })
            .execute()
        )
        if inserted.data:
            project = inserted.data[0]
            st.session_state["active_project_id"] = project.get("project_id")
            st.session_state["active_project_name"] = project.get("project_name", "Home 1")
            st.session_state["household_nickname"] = project.get("project_name", "Home 1")
            return st.session_state["active_project_id"]
    except Exception as exc:
        st.session_state["supabase_error"] = str(exc)
    return None


def create_household_project(project_name: str, project_type: str = "Home") -> str | None:
    if not is_logged_in():
        return None
    supabase = get_supabase_client()
    if supabase is None:
        return None
    try:
        inserted = (
            supabase.table("household_projects")
            .insert({
                "user_id": st.session_state["auth_user_id"],
                "project_name": project_name.strip() or "New Home",
                "project_type": project_type,
                "is_active": True,
            })
            .execute()
        )
        if inserted.data:
            project = inserted.data[0]
            st.session_state["active_project_id"] = project.get("project_id")
            st.session_state["active_project_name"] = project.get("project_name", project_name)
            st.session_state["household_nickname"] = project.get("project_name", project_name)
            clear_current_scan_state()
            return project.get("project_id")
    except Exception as exc:
        st.session_state["supabase_error"] = str(exc)
    return None


def set_active_project(project_id: str) -> None:
    projects = load_user_projects()
    for project in projects:
        if str(project.get("project_id")) == str(project_id):
            st.session_state["active_project_id"] = project.get("project_id")
            st.session_state["active_project_name"] = project.get("project_name", "Home")
            st.session_state["household_nickname"] = project.get("project_name", "Home")
            clear_current_scan_state()
            break


def project_manager_panel() -> None:
    """Switch/create projects directly from the dashboard without refreshing."""
    if not is_logged_in():
        return

    st.markdown("### My household projects")
    projects = load_user_projects()

    if st.session_state.get("supabase_error") and "household_projects" in st.session_state.get("supabase_error", ""):
        st.error("Project management table is not available yet. Run the project-upgrade SQL in Supabase.")
        st.caption(st.session_state["supabase_error"])
        return

    if not projects:
        ensure_default_project()
        projects = load_user_projects()

    if projects:
        project_options = {f"{p.get('project_name', 'Home')} — {p.get('project_type', 'Home')}": p.get("project_id") for p in projects}
        active_id = st.session_state.get("active_project_id") or next(iter(project_options.values()))
        labels = list(project_options.keys())
        active_label = next((label for label, pid in project_options.items() if str(pid) == str(active_id)), labels[0])
        selected_label = st.selectbox("Active project", labels, index=labels.index(active_label), key="active_project_select")
        selected_id = project_options[selected_label]
        if str(selected_id) != str(st.session_state.get("active_project_id")):
            set_active_project(selected_id)
            st.rerun()

    c1, c2 = st.columns(2)
    with c1:
        with st.form("new_project_form"):
            new_name = st.text_input("Create another project", placeholder="Example: Home 2, Rental unit, Parents' home")
            new_type = st.selectbox("Project type", ["Home", "Apartment / unit", "Rental property", "Holiday home", "Other"])
            submitted = st.form_submit_button("Create project and start scan", type="primary", use_container_width=True)
        if submitted:
            new_id = create_household_project(new_name, new_type)
            if new_id:
                next_stage("money")
            else:
                st.error("Could not create the project.")
                if st.session_state.get("supabase_error"):
                    st.caption(st.session_state["supabase_error"])
    with c2:
        st.markdown(
            f"""
            <div class='project-box'>
                <strong>Current project:</strong> {st.session_state.get('active_project_name', 'Home 1')}<br>
                Create a new project here without refreshing the page. Each project can have its own scan, dashboard, and check-ins.
            </div>
            """,
            unsafe_allow_html=True,
        )
        if st.button("Start a new scan for active project", use_container_width=True):
            clear_current_scan_state()
            next_stage("money")


def require_login_for_energy_pathway() -> bool:
    """Block guest use. Users must create/log in before using the project."""
    if is_logged_in():
        return True
    logo_header()
    episode_header(
        "Account required",
        "Create your household energy project first",
        "The scan, recommendations, monthly bills, and action progress are saved under your account, so this version does not support guest mode.",
        "🔐",
    )
    auth_panel(compact=False)
    return False


def account_screen() -> None:
    logo_header()
    sidebar_account_card()
    episode_header(
        "Personal account",
        "Save your energy roadmap and track performance",
        "Create a simple household account so you can return later, update bills, mark actions as completed, and see whether your pathway is improving.",
        "👤",
    )
    st.markdown(
        """
        <div class='account-note'>
            <strong>Profile and project management:</strong> users can manage their household profile and one active project in this version. A future tier can allow multiple homes, separate dashboards, and property-by-property roadmaps.
        </div>
        """,
        unsafe_allow_html=True,
    )
    st.warning("Account mode uses email login. That means email becomes account information. Do not collect full address, phone number, utility account number, or household income.")
    auth_panel(compact=False)


def dashboard_screen() -> None:
    logo_header()
    sidebar_account_card()
    if not is_logged_in():
        st.warning("Please log in or create an account first.")
        auth_panel(compact=False)
        return

    episode_header(
        "My dashboard",
        "Household energy performance tracker",
        "Track monthly bills, completed actions, and progress against your original saving pathway.",
        "📊",
    )

    data = load_user_dashboard_data()
    scans = data["scans"]
    recommendations = data["recommendations"]
    checkins = data["checkins"]

    if not scans:
        st.info("No saved scan yet for the active project. Create/switch a project below, then start a scan.")
        project_manager_panel()
        return

    latest = scans[0]
    c1, c2, c3 = st.columns(3)
    with c1:
        value_bar("Latest annual estimate", _currency(float(latest.get("annual_bill_estimate") or 0)), "Your latest saved baseline.", "💳")
    with c2:
        value_bar("Saving opportunity", f"{_currency(float(latest.get('saving_low') or 0))}–{_currency(float(latest.get('saving_high') or 0))}", "Latest saved annual saving range.", "💰")
    with c3:
        completed = len([r for r in recommendations if r.get("status") == "Completed"])
        value_bar("Completed actions", f"{completed}/{len(recommendations)}", "Actions marked complete in your dashboard.", "✅")

    project_manager_panel()

    st.markdown("### Monthly bill check-in")
    with st.form("monthly_checkin_form"):
        c4, c5, c6 = st.columns(3)
        with c4:
            checkin_month = st.date_input("Month", value=date.today())
            actual_bill = st.number_input("Actual energy bill for this month (A$)", min_value=0.0, max_value=3000.0, value=float(st.session_state.get("monthly_bill", 250.0)), step=10.0)
        with c5:
            comfort_rating = st.slider("Comfort rating this month", 1, 10, 6)
            completed_actions = st.multiselect(
                "Actions completed or maintained",
                sorted(list({r.get("title") for r in recommendations if r.get("title")})),
            )
        with c6:
            notes = st.text_area("Short note", placeholder="Example: started shorter showers; replaced kitchen bulbs.")
        submitted = st.form_submit_button("Save monthly check-in", type="primary", use_container_width=True)

    if submitted:
        supabase = get_supabase_client()
        if supabase:
            try:
                supabase.table("monthly_checkins").insert({
                    "user_id": st.session_state["auth_user_id"],
                    "project_id": st.session_state.get("active_project_id"),
                    "scan_id": latest.get("scan_id") or latest.get("id"),
                    "checkin_month": checkin_month.isoformat(),
                    "actual_bill": float(actual_bill),
                    "comfort_rating": int(comfort_rating),
                    "completed_actions": "; ".join(completed_actions),
                    "notes": notes,
                    "created_at": datetime.utcnow().isoformat(),
                }).execute()
                st.success("Monthly check-in saved.")
                st.rerun()
            except Exception as exc:
                st.error("Could not save the monthly check-in.")
                st.caption(str(exc))

    if checkins:
        st.markdown("### Bill progress")
        progress_df = pd.DataFrame(checkins)
        progress_df["checkin_month"] = pd.to_datetime(progress_df["checkin_month"])
        progress_df = progress_df.sort_values("checkin_month")
        fig = go.Figure()
        fig.add_trace(go.Scatter(
            x=progress_df["checkin_month"],
            y=progress_df["actual_bill"],
            mode="lines+markers",
            name="Actual monthly bill",
        ))
        fig.update_layout(height=360, yaxis_title="Monthly bill (A$)", margin=dict(l=20, r=20, t=30, b=20))
        st.plotly_chart(fig, use_container_width=True)

    st.markdown("### Action progress")
    if recommendations:
        for r in recommendations[:12]:
            with st.expander(f"{r.get('title', 'Action')} — {r.get('status', 'Not started')}"):
                st.write(f"**Category:** {r.get('category', '')}")
                st.write(f"**Estimated annual saving:** {_currency(float(r.get('estimated_saving_low') or 0))}–{_currency(float(r.get('estimated_saving_high') or 0))}")
                new_status = st.selectbox(
                    "Update status",
                    ["Not started", "In progress", "Completed", "Not relevant"],
                    index=["Not started", "In progress", "Completed", "Not relevant"].index(r.get("status", "Not started")) if r.get("status", "Not started") in ["Not started", "In progress", "Completed", "Not relevant"] else 0,
                    key=f"status_{r.get('recommendation_id') or r.get('id')}",
                )
                if st.button("Save status", key=f"save_status_{r.get('recommendation_id') or r.get('id')}"):
                    supabase = get_supabase_client()
                    if supabase:
                        try:
                            rec_id = r.get("recommendation_id") or r.get("id")
                            supabase.table("recommendations").update({"status": new_status}).eq("recommendation_id", rec_id).execute()
                            st.success("Action status updated.")
                            st.rerun()
                        except Exception as exc:
                            st.error("Could not update the action.")
                            st.caption(str(exc))


# Override plan_screen to add account saving and dashboard call-to-action.
_original_plan_screen_for_accounts = plan_screen

def plan_screen() -> None:
    _original_plan_screen_for_accounts()

    st.markdown("### Save and track this roadmap")
    if is_logged_in():
        inputs = current_household_inputs()
        savings = estimate_all_savings(inputs)
        ranked = current_ranked_actions()
        result_text = score_label(st.session_state.get("score", 0))
        if st.button("Save this roadmap to my dashboard", type="primary", use_container_width=True):
            scan_id = save_scan_to_supabase(savings, ranked, result_text)
            if scan_id:
                st.success("Roadmap saved to your dashboard.")
                next_stage("dashboard")
            else:
                st.error("Could not save to Supabase. Check your Supabase setup.")
                if st.session_state.get("supabase_error"):
                    st.caption(st.session_state["supabase_error"])
    else:
        st.info("Create an account to save this roadmap, update monthly bills, and track action progress.")
        auth_panel(compact=True)


# Override welcome_screen to require account before starting.
def welcome_screen() -> None:
    logo_header()
    sidebar_account_card()
    episode_header(
        "Welcome",
        "Your personalised household energy platform",
        "Create a household project, find where energy money is leaking, and return monthly to manage bills, actions, and performance.",
        "🏠",
    )
    st.markdown(
        """
        <div class='account-note'>
            <strong>Manage your profile and projects.</strong><br>
            Each user can manage a household profile, save an energy roadmap, and track monthly progress. This version allows one active home project, such as <strong>Home 1</strong>. Multi-home project management can be enabled later.
        </div>
        """,
        unsafe_allow_html=True,
    )

    if is_logged_in():
        st.success(f"Welcome back, {auth_user_label()}.")
        c1, c2 = st.columns(2)
        with c1:
            if st.button("Start / update my Home 1 energy scan", type="primary", use_container_width=True):
                next_stage("money")
        with c2:
            if st.button("Open my saved dashboard", use_container_width=True):
                next_stage("dashboard")
        st.markdown(
            """
            <div class='locked-project'>
                <strong>Future feature:</strong> add another home project, compare multiple properties, and manage separate upgrade roadmaps. This is intentionally shown as an expansion opportunity, not active in this version.
            </div>
            """,
            unsafe_allow_html=True,
        )
    else:
        auth_panel(compact=False)




if st.session_state.stage == "welcome":
    welcome_screen()
elif st.session_state.stage == "money":
    if require_login_for_energy_pathway():
        money_screen()
elif st.session_state.stage == "profile":
    if require_login_for_energy_pathway():
        profile_screen()
elif st.session_state.stage == "inspection":
    if require_login_for_energy_pathway():
        inspection_screen()
elif st.session_state.stage == "plan":
    if require_login_for_energy_pathway():
        plan_screen()
elif st.session_state.stage == "account":
    account_screen()
elif st.session_state.stage == "dashboard":
    dashboard_screen()
