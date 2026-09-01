from __future__ import annotations

import streamlit as st
from sqlalchemy.orm import Session

from services.analytics_service import daily_team_trends, latest_team_summary, team_kpis
from services.recommendation_service import recommendations_for_player
from services.player_service import get_player
from utils.charts import line_chart, risk_distribution_chart
from utils.ui import metric_row, page_header


def render(session: Session) -> None:
    page_header(
        "Team Dashboard",
        "A concise view of squad readiness, workload, recovery and AI-assisted risk indicators.",
    )
    summary = latest_team_summary(session)
    kpis = team_kpis(summary)
    metric_row(kpis)

    if summary.empty:
        st.info("No squad data is available yet.")
        return

    st.subheader("Team Trends")
    trends = daily_team_trends(session, days=30)
    left, right = st.columns([2, 1])
    with left:
        if not trends.empty:
            fig = line_chart(
                trends,
                "date",
                ["training_load", "recovery_score", "fatigue_score", "fitness_score"],
                "30-Day Team Monitoring Trend",
                labels={"value": "Score / Load", "date": "Date"},
            )
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("Trend data is not available.")
    with right:
        st.plotly_chart(risk_distribution_chart(summary), use_container_width=True)

    st.subheader("Players Needing Attention")
    attention = summary[(summary["Risk"] == "HIGH") | (summary["Recovery"] < 60) | (summary["Fatigue"] > 70)]
    if attention.empty:
        st.success("No players currently meet the attention rule.")
    else:
        st.dataframe(
            attention[["Player", "Position", "Recovery", "Fatigue", "Workload Change %", "Risk"]],
            use_container_width=True,
            hide_index=True,
        )

    st.subheader("Key Recommendations")
    for row in attention.head(3).to_dict("records"):
        player = get_player(session, int(row["Player ID"]))
        if not player:
            continue
        with st.container(border=True):
            st.markdown(f"**{player.name}**")
            for item in recommendations_for_player(session, player)[:2]:
                st.write(f"- {item['recommendation']} Reason: {item['reason']}")

