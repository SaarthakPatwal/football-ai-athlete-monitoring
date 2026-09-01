from __future__ import annotations

import streamlit as st
from sqlalchemy.orm import Session

from services.analytics_service import latest_team_summary, team_kpis
from utils.ui import metric_row


def _go(page: str) -> None:
    st.session_state["requested_page"] = page
    st.rerun()


def render(session: Session) -> None:
    st.title("Football AI")
    st.caption("Athlete Monitoring & Football Intelligence Platform")
    st.write(
        "A minimal internal workspace for squad monitoring, daily data entry and football performance intelligence."
    )

    summary = latest_team_summary(session)
    kpis = team_kpis(summary)
    metric_row({
        "Squad": kpis["Squad Size"],
        "Fitness": kpis["Average Fitness"],
        "Recovery": kpis["Average Recovery"],
        "Attention": kpis["Players Needing Attention"],
    })

    st.divider()
    col_a, col_b, col_c = st.columns(3)
    with col_a:
        st.subheader("Start Monitoring")
        st.caption("Open the main team dashboard.")
        if st.button("Open Dashboard", use_container_width=True):
            _go("Dashboard")
    with col_b:
        st.subheader("Enter Data")
        st.caption("Add today’s training, recovery, match or wellness observations.")
        if st.button("Open Data Entry", use_container_width=True, type="primary"):
            _go("Data Entry")
    with col_c:
        st.subheader("Review Squad")
        st.caption("View players, roles and current readiness.")
        if st.button("Open Squad", use_container_width=True):
            _go("Squad")

    st.caption("Synthetic demo data is loaded by default. Manual entries write to the same database and update analytics.")
