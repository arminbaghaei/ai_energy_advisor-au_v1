# The Energy Detective Australia

A Streamlit web application that turns the Level 1 home-energy inspection game into a practical, market-facing web prototype for Australian households.

## What the app does

The Energy Detective Australia guides a user through a short home-energy check-up. The user answers five household profile questions, completes seven inspection hotspots, and receives a prioritised Energy Action Plan with conservative indicative annual savings.

The app is designed for public education and engagement. It is not a certified home energy audit, NatHERS assessment, solar calculator, or compliance tool.

## Main features

- Simple household profile workflow
- Seven inspection hotspots:
  - Heating/cooling thermostat
  - Old light bulbs
  - Curtains and windows
  - Draught gaps
  - Shower and hot water
  - Standby appliances
  - Ceiling/roof insulation awareness
- Hidden scoring and recommendation logic
- Bill risk and comfort-readiness meters
- Final action plan with ranked recommendations
- Conservative indicative savings for selected actions
- CSV download of recommendations
- Company logo placeholder

## Repository structure

```text
energywise_streamlit_repo/
├── app.py
├── requirements.txt
├── README.md
├── DEPLOYMENT.md
├── CONTENT_EVIDENCE.md
├── MARKET_READY_NOTES.md
├── .gitignore
├── .streamlit/
│   └── config.toml
├── assets/
│   └── .gitkeep
├── data/
│   └── actions.json
└── logic/
    ├── calculations.py
    └── recommendations.py
```

## Add your logo

Place your company logo in:

```text
assets/company_logo.png
```

The app will automatically show it on the landing screen. PNG is recommended.

## Run locally

```bash
python -m venv .venv
source .venv/bin/activate  # Mac/Linux
# .venv\Scripts\activate  # Windows
pip install -r requirements.txt
streamlit run app.py
```

## Deploy on Streamlit Cloud

1. Create a GitHub repository.
2. Upload all files from this folder.
3. Go to Streamlit Community Cloud.
4. Connect your GitHub account.
5. Select the repository and set the main file path to `app.py`.
6. Deploy.

## Important product positioning

Use the phrase **research prototype with a market-ready interface** until the app has been validated with real users and tested against local tariffs, climate zones, appliance data, and pre/post energy outcomes.

Do not claim guaranteed bill savings. Use language such as:

> Indicative annual saving based on user inputs and simplified assumptions. Actual savings depend on tariff, climate, appliance efficiency, occupancy, and behaviour.

## Suggested next development steps

1. Add state-specific tariff defaults.
2. Add climate-zone selection.
3. Add hot-water system type.
4. Add optional bill-upload or manual kWh entry.
5. Add landlord/renter-specific recommendation letters.
6. Add analytics only with clear privacy notice and consent.
7. Validate recommendations with pilot households before public claims.
