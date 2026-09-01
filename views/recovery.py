from __future__ import annotations

import streamlit as st
from sqlalchemy.orm import Session

from services.analytics_service import latest_team_summary, recovery_dataframe
from utils.charts import line_chart
from utils.ui import page_header


def render(session: Session) -> None:
    page_header("Recovery", "Sleep, HRV, soreness, hydration and transparent recovery scoring.")
    recovery = recovery_dataframe(session, days=30)
    summary = latest_team_summary(session)
    if recovery.empty:
        st.info("No recovery records are available.")
        return

    daily = recovery.groupby("date", as_index=False).agg({
        "recovery_score": "mean",
        "sleep_hours": "mean",
        "hrv": "mean",
        "muscle_soreness": "mean",
    })
    st.plotly_chart(line_chart(daily, "date", ["recovery_score", "sleep_hours", "hrv", "muscle_soreness"], "30-Day Recovery Markers"), use_container_width=True)

    st.subheader("Lowest Recovery Today")
    if summary.empty:
        st.info("No squad summary is available yet.")
    else:
        low_recovery = summary.sort_values("Recovery").head(8)
        st.dataframe(low_recovery[["Player", "Position", "Recovery", "Sleep", "Soreness", "Fatigue", "Risk"]], use_container_width=True, hide_index=True)

    with st.expander("Recovery score calculation"):
        st.write(
            "Recovery combines sleep duration and quality, HRV, resting heart rate, hydration, soreness, stress, mood and rest-day context. "
            "The weights are transparent demo assumptions for a portfolio application."
        )

