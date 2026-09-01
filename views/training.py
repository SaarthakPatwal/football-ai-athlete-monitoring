from __future__ import annotations

import streamlit as st
from sqlalchemy.orm import Session

from services.analytics_service import latest_team_summary, training_dataframe
from utils.charts import bar_chart, line_chart
from utils.ui import page_header


def render(session: Session) -> None:
    page_header("Training", "Workload indicators, training load and sudden load increases.")
    days = st.slider("Days", min_value=7, max_value=90, value=30, step=7)
    training = training_dataframe(session, days=days)
    summary = latest_team_summary(session)
    if training.empty:
        st.info("No training sessions are available.")
        return

    daily = training.groupby("date", as_index=False).agg({"training_load": "mean", "acute_workload": "mean", "baseline_workload": "mean"})
    st.plotly_chart(
        line_chart(daily, "date", ["training_load", "acute_workload", "baseline_workload"], "Team Workload Indicators"),
        use_container_width=True,
    )

    st.subheader("High Load Watchlist")
    if summary.empty:
        st.info("No squad summary is available yet.")
    else:
        high_load = summary.sort_values("Workload Change %", ascending=False).head(8)
        st.dataframe(high_load[["Player", "Position", "Workload", "Baseline", "Workload Change %", "Fatigue", "Risk"]], use_container_width=True, hide_index=True)

    type_load = training.groupby("session_type", as_index=False)["training_load"].mean().sort_values("training_load", ascending=False)
    st.plotly_chart(bar_chart(type_load, "session_type", "training_load", "Average Load by Session Type"), use_container_width=True)

