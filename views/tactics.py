from __future__ import annotations

import streamlit as st
from sqlalchemy.orm import Session

from services.analytics_service import latest_team_summary
from utils.charts import tactical_pitch
from utils.ui import page_header


def render(session: Session) -> None:
    page_header("Tactical Analysis", "Formation view with simplified analytics-based tactical observations.")
    summary = latest_team_summary(session)
    if summary.empty:
        st.info("No squad data is available.")
        return
    formation = st.selectbox("Formation", ["4-3-3", "4-2-3-1", "4-4-2", "3-5-2"])
    starters = summary.sort_values(["Performance", "Fitness"], ascending=False).head(11)
    st.plotly_chart(tactical_pitch(starters, formation), use_container_width=True)

    midfield = summary[summary["Position"].isin(["DM", "CM", "AM"])]
    wide_defenders = summary[summary["Position"].isin(["RB", "LB"])]
    st.subheader("Tactical Observations")
    if not midfield.empty:
        st.write(f"- Midfield average performance is {midfield['Performance'].mean():.1f}.")
    if not wide_defenders.empty:
        st.write(f"- Full-back workload is {wide_defenders['Workload Change %'].mean():.1f}% versus baseline.")
    st.caption("These are simplified indicators and do not replace professional tactical analysis.")

