from __future__ import annotations

import streamlit as st
from sqlalchemy.orm import Session

from services.analytics_service import daily_team_trends, latest_team_summary
from utils.charts import bar_chart, line_chart
from utils.ui import page_header


def render(session: Session) -> None:
    page_header("Team Analytics", "Historical trends, baselines and squad health distribution.")
    days = st.selectbox("Window", [7, 14, 30, 90, 365], index=2)
    trends = daily_team_trends(session, days=days)
    summary = latest_team_summary(session)
    if trends.empty or summary.empty:
        st.info("Team analytics are not available yet.")
        return
    st.plotly_chart(
        line_chart(trends, "date", ["training_load", "recovery_score", "fatigue_score", "injury_risk_pct"], f"{days}-Day Team Trend"),
        use_container_width=True,
    )
    health = summary["Risk"].value_counts().reindex(["LOW", "MEDIUM", "HIGH"], fill_value=0).reset_index()
    health.columns = ["Risk", "Players"]
    st.plotly_chart(bar_chart(health, "Risk", "Players", "Team Health Overview", color="Risk"), use_container_width=True)

    st.subheader("Player Comparison")
    selected = st.multiselect("Players", summary["Player"].tolist(), default=summary["Player"].head(3).tolist())
    comparison = summary[summary["Player"].isin(selected)]
    if not comparison.empty:
        st.dataframe(
            comparison[["Player", "Fitness", "Performance", "Recovery", "Fatigue", "Workload", "Risk %", "Risk"]],
            use_container_width=True,
            hide_index=True,
        )

