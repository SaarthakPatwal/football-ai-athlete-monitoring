from __future__ import annotations

import streamlit as st
from sqlalchemy.orm import Session

from services.analytics_service import latest_team_summary
from services.player_service import players_dataframe
from utils.charts import bar_chart
from utils.ui import page_header


def render(session: Session) -> None:
    page_header("Squad", "Complete player database with readiness and performance context.")
    players = players_dataframe(session)
    summary = latest_team_summary(session)
    if players.empty:
        st.info("No players found.")
        return

    positions = ["All"] + sorted(players["Position"].unique().tolist())
    selected_position = st.selectbox("Position", positions)
    filtered = players if selected_position == "All" else players[players["Position"] == selected_position]

    st.dataframe(filtered, use_container_width=True, hide_index=True)
    st.subheader("Current Readiness")
    if summary.empty:
        st.info("No readiness data yet. Add training and recovery observations in Data Entry.")
    else:
        st.dataframe(
            summary[["Player", "Position", "Fitness", "Recovery", "Fatigue", "Performance", "Risk"]],
            use_container_width=True,
            hide_index=True,
        )
    position_counts = players.groupby("Position", as_index=False).size().rename(columns={"size": "Players"})
    st.plotly_chart(bar_chart(position_counts, "Position", "Players", "Squad Balance by Position"), use_container_width=True)

