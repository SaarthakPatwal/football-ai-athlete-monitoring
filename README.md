# AI Athlete Monitoring & Football Intelligence Platform

Portfolio-ready Streamlit application that simulates an internal football club performance department platform. The app uses realistic synthetic data so it can be demonstrated without private club data.

## Features

- Squad database with player profiles, physical attributes and football attributes
- Team dashboard with fitness, recovery, fatigue, workload, performance and risk indicators
- Player analysis with training load, recovery, fatigue, sleep and match-performance trends
- Training workload monitoring with baseline comparison
- Recovery and nutrition pages with transparent scoring
- Match analytics, form indicators and a simplified tactical pitch
- Deterministic AI assistant that answers from application data
- Manual data-entry suite for players, training, recovery, matches, nutrition and wellness
- AI-assisted injury-risk estimation with explainable factors
- Alerts generated from actual workload, recovery and fatigue rules
- CSV validation page for future persisted imports

## Architecture

```text
Streamlit UI
    -> services
        -> SQLAlchemy models
        -> SQLite by default, PostgreSQL-compatible URL later
    -> utils
        -> calculations, charts, synthetic data
    -> ml
        -> reproducible model interfaces
```

## Technology Stack

Python, Streamlit, Pandas, NumPy, Plotly, SQLAlchemy, SQLite and pytest. The code is organized so scikit-learn models and a FastAPI layer can be added later without changing the UI contract. Screen modules live in `views/` so Streamlit does not treat them as extra multipage scripts.

## Database Schema

Core tables are `players`, `training_sessions`, `recovery_records`, `match_records`, `nutrition_records`, `injury_history` and `alerts`.

## ML Models

Phase 1 includes transparent model interfaces and rule-based baseline predictions for fatigue, injury risk and expected performance. These expose `train_model()`, `save_model()`, `load_model()` and `predict()` style functions where applicable.

## AI Recommendation Engine

Recommendations combine the latest player workload, recovery, fatigue, performance and risk indicators. Every recommendation includes a reason and avoids medical diagnosis.

## Screenshots

Add screenshots after running the local app.

## Installation

```bash
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
```

## Running Locally

```bash
streamlit run app.py
```

On first launch, the app opens on a minimal Start page. From there, open the dashboard or the Data Entry suite. The app creates the SQLite database and seeds 25 players with 365 days of synthetic training, recovery, nutrition and match data.

## Synthetic Data

The generator creates realistic relationships: higher workload can increase fatigue, poor sleep can reduce recovery, and elevated fatigue can affect risk and performance indicators. The data is synthetic and intentionally imperfect.

## Manual Entry

The Data Entry page supports add/edit/delete player workflows and manual training, recovery, match, nutrition and wellness submissions. New training and recovery observations recalculate workload, fatigue, injury-risk estimates, alerts and player recommendations through the same database-backed analytics pipeline.

## Model Limitations

Injury-risk outputs are AI-assisted estimates for demonstration only. They are not medical diagnoses, are not clinically validated and should not be used for real athlete health decisions.

## Deployment

The app can run in Docker:

```bash
docker build -t football-ai-monitoring .
docker run -p 8501:8501 football-ai-monitoring
```

Use `DATABASE_URL` to point at SQLite locally or PostgreSQL-compatible infrastructure later.

## Future Improvements

- Persist validated CSV imports into database tables
- Add trained scikit-learn models and model evaluation pages
- Add SHAP or a richer contribution engine
- Add FastAPI endpoints for programmatic access
- Add authentication and role-based views

## Disclaimer

This is a portfolio and research project using synthetic data. It is not medical software and does not provide clinical advice.
