from __future__ import annotations

import streamlit as st

from database.database import get_session, init_db
from database.seed import seed_demo_data
from views import (
    ai_assistant,
    alerts,
    dashboard,
    data_entry,
    data_import,
    matches,
    nutrition,
    player_analysis,
    recovery,
    squad,
    start,
    tactics,
    team_analytics,
    training,
)
from utils.ui import apply_theme


PAGES = {
    "Start": start.render,
    "Dashboard": dashboard.render,
    "Squad": squad.render,
    "Player Analysis": player_analysis.render,
    "Training": training.render,
    "Recovery": recovery.render,
    "Matches": matches.render,
    "Tactics": tactics.render,
    "Nutrition": nutrition.render,
    "Team Analytics": team_analytics.render,
    "AI Assistant": ai_assistant.render,
    "Alerts": alerts.render,
    "Data Entry": data_entry.render,
    "Data Import": data_import.render,
}


def bootstrap() -> None:
    init_db()
    with get_session() as session:
        seed_demo_data(session)


def main() -> None:
    st.set_page_config(
        page_title="Football AI",
        page_icon="FA",
        layout="wide",
        initial_sidebar_state="expanded",
    )
    apply_theme()
    bootstrap()

    st.sidebar.title("Football AI")
    st.sidebar.caption("Athlete Monitoring")
    if "nav_page" not in st.session_state:
        st.session_state["nav_page"] = "Start"
    if "requested_page" in st.session_state:
        st.session_state["nav_page"] = st.session_state.pop("requested_page")
    selected_page = st.sidebar.radio("Navigation", list(PAGES.keys()), key="nav_page", label_visibility="collapsed")
    st.sidebar.divider()
    if st.sidebar.button("Regenerate Demo Data", use_container_width=True):
        with st.spinner("Regenerating realistic synthetic data..."):
            with get_session() as session:
                seed_demo_data(session, force=True)
        st.sidebar.success("Demo data regenerated.")
        st.rerun()
    st.sidebar.caption("Synthetic demo data. Injury-risk output is not a medical diagnosis.")

    with get_session() as session:
        PAGES[selected_page](session)


if __name__ == "__main__":
    main()
