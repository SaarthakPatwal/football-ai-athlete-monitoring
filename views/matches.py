from __future__ import annotations

import streamlit as st
from sqlalchemy.orm import Session

from services.analytics_service import match_dataframe
from utils.charts import bar_chart, line_chart
from utils.ui import page_header


def render(session: Session) -> None:
    page_header("Match Analytics", "Recent match performance, player ratings and form indicators.")
    matches = match_dataframe(session)
    if matches.empty:
        st.info("No match records are available.")
        return

    recent = matches.sort_values("date", ascending=False)
    st.dataframe(
        recent[["date", "opponent", "result", "player_id", "minutes_played", "goals", "assists", "pass_accuracy", "player_rating", "performance_score"]].head(80),
        use_container_width=True,
        hide_index=True,
    )
    by_match = matches.groupby("date", as_index=False)["performance_score"].mean().sort_values("date")
    st.plotly_chart(line_chart(by_match, "date", "performance_score", "Team Match Performance Trend"), use_container_width=True)

    form = matches.groupby("player_id", as_index=False)["performance_score"].mean().sort_values("performance_score", ascending=False).head(10)
    st.plotly_chart(bar_chart(form, "player_id", "performance_score", "Top Average Match Form"), use_container_width=True)
