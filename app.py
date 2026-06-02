from __future__ import annotations

from pathlib import Path
import base64
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


def sidebar_status() -> None:
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


if st.session_state.stage == "welcome":
    welcome_screen()
elif st.session_state.stage == "money":
    money_screen()
elif st.session_state.stage == "profile":
    profile_screen()
elif st.session_state.stage == "inspection":
    inspection_screen()
elif st.session_state.stage == "plan":
    plan_screen()
