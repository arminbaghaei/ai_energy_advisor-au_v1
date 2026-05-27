# Deployment Guide: GitHub + Streamlit Cloud

## 1. Prepare the repository

Create a new GitHub repository, for example:

```text
energywise-homes-australia
```

Upload these files and folders:

```text
app.py
requirements.txt
README.md
DEPLOYMENT.md
CONTENT_EVIDENCE.md
MARKET_READY_NOTES.md
.streamlit/config.toml
assets/
data/actions.json
logic/calculations.py
logic/recommendations.py
```

## 2. Add branding

Add your company logo as:

```text
assets/company_logo.png
```

Recommended dimensions: 800 × 800 px or a transparent PNG with similar proportions.

## 3. Deploy on Streamlit Cloud

1. Sign in to Streamlit Community Cloud.
2. Choose **New app**.
3. Select the GitHub repository.
4. Set branch to `main`.
5. Set main file path to `app.py`.
6. Click **Deploy**.

## 4. Test after deployment

Check the following before sharing publicly:

- The logo loads correctly.
- The household profile saves answers.
- All seven hotspot questions work.
- Score updates only once per hotspot.
- The final action plan appears.
- CSV download works.
- Dollar savings are labelled as indicative.
- The app works on mobile and desktop screens.

## 5. Public sharing checklist

Before LinkedIn, partner, or council dissemination:

- Add company name and contact details.
- Add a privacy statement if collecting analytics or storing user data.
- Add a limitation statement on all monetised savings.
- Test with at least 5–10 users from the target audience.
- Avoid claiming certified assessment, guaranteed savings, or compliance advice.
