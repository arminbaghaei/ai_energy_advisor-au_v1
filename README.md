# The Home-energy check-up (Australia)

**Beta Version 1.0**  
A web-based, money-first home-energy check-up tool for Australian households.

The Home-energy check-up (Australia) is a Streamlit application developed by **Tech Innovation Experts**. It helps users estimate possible avoidable energy-bill waste, complete a short household energy inspection, receive immediate feedback, and generate a practical action roadmap with indicative saving opportunities.

The latest version is more than a simple questionnaire. It includes a household account layer, Supabase-backed project storage, monthly check-ins, recommendation tracking, visual guidance, and a dashboard for returning users.

This tool is a public-facing research and market-readiness prototype. It is intended for education, engagement, early user testing, and household energy-awareness support. It is **not** a certified home energy audit, NatHERS rating, NCC compliance report, or professional building assessment.

---

## Developed by

**Tech Innovation Experts Ltd.**  
Providing technology-driven services across Oceania
Contact us: support@tinx.co.nz

---

## Current deployment status

Recommended beta deployment pattern:

```text
tinx.co.nz                 → WordPress website / public landing page
tools.tinx.co.nz           → redirect or future custom app domain
Streamlit Cloud app         → current running Python application
GitHub repository           → source code and documentation
Streamlit Secrets           → private secrets; do not commit to GitHub
```

For the current beta, the safest setup is to keep the Streamlit app running on Streamlit Cloud and link to it from WordPress. A standard cPanel redirect from `tools.tinx.co.nz` to the Streamlit app is acceptable for beta testing, but it will still show the Streamlit URL after redirecting.

For a fully branded production release where `tools.tinx.co.nz` stays in the browser address bar, deploy the app to a platform that supports custom domains, such as Render, Railway, Azure Container Apps, Google Cloud Run, DigitalOcean, or a VPS.

---

## Main purpose

The tool helps Australian households understand where energy waste may occur and which actions should be prioritised first.

The interface is deliberately money-first. It starts with a quick estimate of possible avoidable bill waste, then guides users through practical checks related to heating and cooling, lighting, curtains, draughts, hot water, standby power, and insulation.

The intended user journey is:

```text
Create or log in to account
        ↓
Create/select household project
        ↓
Complete money-leak scan
        ↓
Set household assumptions
        ↓
Inspect seven household energy hotspots
        ↓
Receive personalised energy-saving roadmap
        ↓
Save roadmap to dashboard
        ↓
Return for monthly bill and action check-ins
```

---

## Latest app features

### 1. Account and project layer

- Email-based account creation and login through Supabase.
- One active household project by default.
- Project-management logic for adding or switching household projects.
- Sidebar account status panel.
- Dashboard access for logged-in users.

### 2. Money-first engagement flow

- Quick monthly bill input.
- Household size, dwelling type, bill-pressure, and thermal-feel inputs.
- Estimated annual bill baseline.
- Indicative annual and monthly recoverable-money range.
- Energy-cost pathway chart showing current pathway, strategy pathway, and benchmark-style operating band.
- Stronger visual highlighting of dollar values, costs, savings, and recovery estimates.

### 3. Household profile and challenge assumptions

- Household size.
- Tenure type: rented or owned.
- Main bill pressure: winter, summer, hot water, or unsure.
- Dwelling type.
- Main heating/cooling system.
- Solar status.
- Monthly bill.
- Electricity price.
- Thermostat improvement assumption.
- Current and target shower time.
- Showers per person per day.
- Number of old halogen/incandescent bulbs.
- Average bulb-use hours.
- Number of standby devices.

### 4. Interactive inspection workflow

The beta version includes seven home-energy checks:

1. Heating and cooling settings.
2. LED lighting.
3. Curtains and window use.
4. Draught sealing.
5. Shower and hot-water behaviour.
6. Standby appliances.
7. Ceiling or roof insulation awareness.

Each check includes:

- a practical question;
- answer choices;
- immediate feedback;
- scoring logic;
- estimated saving lens where available;
- visual guide cards;
- contribution to the final roadmap.

### 5. Recommendation and saving pathway

The final roadmap includes:

- overall energy-readiness score;
- top three money moves;
- full recommendation list;
- indicative annual saving range;
- saving chart;
- save-to-upgrade pathway;
- renter and owner pathways;
- conditional hot-water cylinder-wrap logic;
- behaviour-saving pool for funding the next upgrade.

### 6. Dashboard and monthly check-ins

For logged-in users, the dashboard supports:

- latest annual bill estimate;
- latest saving opportunity range;
- completed-action count;
- monthly bill check-ins;
- comfort rating;
- completed or maintained actions;
- notes;
- bill progress chart;
- recommendation status updates.

### 7. Certificate recognition

The tool can display an optional completion certificate.

The certificate is a recognition certificate only. It does not represent an accredited qualification, formal energy assessment, NCC compliance certificate, NatHERS rating, or verified saving result.

---

## Important disclaimer

This tool provides **educational guidance and indicative decision-support estimates only**.

It is **not**:

- a certified home energy assessment;
- an accredited NatHERS rating;
- an NCC compliance report;
- a professional building-performance assessment;
- a substitute for qualified building, electrical, plumbing, insulation, solar, or energy advice.

Dollar estimates are indicative and depend on local tariffs, climate zone, household behaviour, dwelling condition, equipment efficiency, occupancy, and appliance use. No saving is guaranteed.

---

## Technology stack

- Python
- Streamlit
- pandas
- Plotly
- Pillow
- Supabase
- Streamlit GSheets connection
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
├── LICENSE.md
│
├── logic/
│   ├── calculations.py
│   └── recommendations.py
│
├── assets/
│   ├── company_logo.png
│   └── recommendations/
│       ├── thermostat.jpg
│       ├── leds.jpg
│       ├── curtains.jpg
│       ├── draught.jpg
│       ├── shower.jpg
│       ├── standby.jpg
│       ├── insulation.jpg
│       └── cylinder_wrap.jpg
│
└── docs/
    ├── MARKET_READY_NOTES.md
    ├── DEPLOYMENT.md
    └── CONTENT_EVIDENCE.md
```

If local recommendation images are not available, the app can fall back to online image URLs. For a stronger production release, use locally stored, licensed images in `assets/recommendations/`.

---

## Installation

Clone the repository:

```bash
git clone https://github.com/YOUR-USERNAME/YOUR-REPOSITORY.git
cd YOUR-REPOSITORY
```

Create and activate a virtual environment:

```bash
python -m venv .venv
source .venv/bin/activate       # macOS/Linux
.venv\Scripts\activate          # Windows
```

Install dependencies:

```bash
pip install -r requirements.txt
```

Run the app locally:

```bash
streamlit run app.py
```

---

## Suggested `requirements.txt`

```text
streamlit>=1.36.0
pandas>=2.2.0
plotly>=5.22.0
Pillow>=10.3.0
st-gsheets-connection>=0.1.0
supabase>=2.0.0
```

If your local environment already uses pinned versions, keep the versions that are known to work with your deployed Streamlit Cloud app.

---

## Secrets and private configuration

Do **not** commit real secrets to GitHub.

The app expects private configuration through Streamlit Cloud Secrets or equivalent environment variables on another hosting platform.

At minimum, the Supabase section is expected in Streamlit Secrets:

```toml
[supabase]
url = "https://YOUR_PROJECT_ID.supabase.co"
anon_key = "YOUR_SUPABASE_ANON_PUBLIC_KEY"
```

If Google Sheets storage is enabled, keep the required Google Sheets credentials in Streamlit Secrets as well. Do not paste those credentials into WordPress, HTML, JavaScript, public files, or the GitHub repository.

Recommended repository rule:

```text
.streamlit/secrets.toml          # never commit
.streamlit/secrets.toml.example  # safe placeholder only
```

Example placeholder:

```toml
[supabase]
url = "YOUR_SUPABASE_URL"
anon_key = "YOUR_SUPABASE_ANON_KEY"
```

---

## Deployment on Streamlit Cloud

1. Push the project files to GitHub.
2. Go to Streamlit Cloud.
3. Select **New app**.
4. Connect the GitHub repository.
5. Set the main file path to:

```text
app.py
```

6. Add the required secrets in **App settings → Secrets**.
7. Deploy the app.
8. After each GitHub commit, Streamlit Cloud should redeploy automatically.

---

## WordPress integration recommendation

For the current beta, the recommended approach is:

```text
WordPress page → button/link → Streamlit Cloud app
```

Avoid relying on iframe embedding for the main public release because it can create:

- width problems;
- height problems;
- Streamlit embed branding;
- mobile layout issues;
- WordPress theme conflicts.

A redirect such as `tools.tinx.co.nz` is acceptable for beta testing, but it will not hide the final Streamlit URL in the browser. To keep `tools.tinx.co.nz` visible in the browser, deploy the app to a custom-domain-capable host.

---

## Version notes

### Beta Version 1.0

Current version includes:

- money-first entry flow;
- energy money-leak scan;
- highlighted saving and cost values;
- visual guide cards;
- seven inspection hotspots;
- immediate feedback;
- hidden scoring logic;
- indicative saving calculations;
- ranked action plan;
- save-to-upgrade pathway;
- account creation and login;
- Supabase-backed dashboard;
- household project management logic;
- monthly bill check-ins;
- recommendation status tracking;
- optional completion certificate;
- company branding and contact details.

---

## Suggested future improvements

Before making stronger public or commercial claims, future versions should include:

- state/territory and climate-zone input;
- real tariff selection or tariff upload;
- hot-water system type;
- heating and cooling equipment details;
- appliance power assumptions;
- user-owned vs renter-specific pathways;
- stronger image licensing documentation;
- accessibility review;
- privacy policy and terms of use;
- user testing with Australian households;
- pre/post validation of bill, behaviour, and action outcomes;
- migration from Streamlit Cloud to a custom-domain production host.

---

## Licence

This project is released under a custom non-commercial licence. See [`LICENSE.md`](LICENSE.md).
