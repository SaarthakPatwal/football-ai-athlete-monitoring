from __future__ import annotations

import streamlit as st
from database.database import init_db, get_session
from views import dashboard, data, players, predictions, model_analysis, health
from utils.ui import apply_theme

PAGES = {"Dashboard": dashboard.render, "Data": data.render, "Players": players.render,
         "ML Predictions": predictions.render, "Model Analysis": model_analysis.render, "Health": health.render}


def main():
    st.set_page_config(page_title="Football Player ML Prediction & Analytics System", layout="wide")
    apply_theme()
    init_db()
    st.sidebar.title("Football Player ML")
    st.sidebar.caption("Prediction & Analytics System")
    page = st.sidebar.radio("Navigation", list(PAGES), label_visibility="collapsed")
    with get_session() as session:
        PAGES[page](session)


if __name__ == "__main__":
    main()
