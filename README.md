# The Home-energy check-up (Australia)

**Beta Version 1.0**  
A web-based home-energy check-up tool for Australian households.

The Home-energy check-up (Australia) is a Streamlit application that helps users inspect common household energy-wasting features, answer simple decision questions, and receive a practical energy action plan with indicative bill-saving opportunities.

This tool is designed as a public-facing research prototype with a market-ready interface. It is intended for education, engagement, and early-stage user testing, not as a certified home energy audit or formal compliance assessment.

---

## Developed by

**Tech Innovation Experts**  
Providing technology-driven services across Oceania  
Email: tinx@gmail.com

---

## Purpose

The tool helps Australian households understand where energy waste may occur and which actions should be prioritised first. It focuses on practical, low-cost decisions before larger upgrades.

Users complete a short profile, inspect key household areas, answer energy-related questions, and receive a prioritised action plan.

---

## Main features

- Short household profile to personalise the action plan
- Interactive inspection workflow
- Seven home-energy check-up questions
- Immediate correct/wrong feedback after each answer
- Hidden scoring and recommendation logic
- Indicative savings summary
- Final personalised energy action plan
- Recognition certificate at the end of the tool
- Downloadable certificate as PNG
- Social sharing buttons for LinkedIn, Facebook, and X
- Company branding and contact details
- Sidebar inspection status tracker

---

## Inspection topics

The current beta version covers:

1. Heating and cooling settings
2. LED lighting
3. Curtains and window use
4. Draught sealing
5. Shower and hot-water behaviour
6. Standby appliances
7. Ceiling or roof insulation awareness

---

## Important disclaimer

This tool provides **educational guidance and indicative savings only**.

It is **not**:

- a certified home energy assessment,
- an accredited NatHERS rating,
- an NCC compliance report,
- a substitute for professional building or energy advice.

The tool is aligned with general Australian home-energy guidance and NatHERS Whole of Home concepts, but it does not perform formal compliance modelling.

---

## Technology stack

- Python
- Streamlit
- pandas
- Plotly
- Pillow
- GitHub
- Streamlit Cloud

---

## Recommended repository structure

```text
home-energy-checkup-australia/
│
├── app.py
├── requirements.txt
├── README.md
│
├── assets/
│   └── company_logo.png
│
└── docs/
    ├── CONTENT_EVIDENCE.md
    ├── DEPLOYMENT.md
    └── MARKET_READY_NOTES.md
```

If the `assets` folder does not exist, create it and place the company logo inside it as:

```text
assets/company_logo.png
```

---

## Installation

Clone the repository:

```bash
git clone https://github.com/YOUR-USERNAME/YOUR-REPOSITORY.git
cd YOUR-REPOSITORY
```

Install the required packages:

```bash
pip install -r requirements.txt
```

Run the app locally:

```bash
streamlit run app.py
```

---

## requirements.txt

Use the following dependencies:

```text
streamlit>=1.36.0
pandas>=2.2.0
plotly>=5.22.0
Pillow>=10.3.0
```

---

## Deployment on Streamlit Cloud

1. Upload the project files to a GitHub repository.
2. Go to Streamlit Cloud.
3. Select **New app**.
4. Connect your GitHub repository.
5. Set the main file path to:

```text
app.py
```

6. Deploy the app.

After each GitHub commit, Streamlit Cloud should automatically redeploy the latest version.

---

## Version notes

### Beta Version 1.0

Current version includes:

- renamed tool title: **The Home-energy check-up (Australia)**
- smaller company logo
- company contact information
- improved feedback display
- final recognition certificate
- square certificate design
- improved ribbon visibility
- downloadable certificate image
- social sharing links

---

## Suggested future improvements

Before making strong public claims about dollar savings, the tool should be validated using:

- Australian tariff assumptions,
- household size and occupancy patterns,
- climate zone,
- appliance efficiency assumptions,
- hot-water system type,
- heating and cooling equipment type,
- measured or self-reported baseline bills.

For a stronger public release, future versions should include optional user inputs for tariff, state/territory, dwelling type, and hot-water system type.

---

## Licence

This repository is prepared as a private or controlled-release research prototype unless a formal licence is added by the owner.

