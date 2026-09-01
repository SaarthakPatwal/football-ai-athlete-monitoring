from __future__ import annotations

import streamlit as st
from sqlalchemy.orm import Session

from services.analytics_service import latest_team_summary
from services.player_service import get_players, player_attribute_dataframe, player_time_series
from services.recommendation_service import recommendations_for_player, risk_explanation_for_player
from utils.charts import bar_chart, line_chart
from utils.ui import metric_row, page_header


RANGE_OPTIONS = {"7 Days": 7, "14 Days": 14, "30 Days": 30, "90 Days": 90, "Season": 365}


def render(session: Session) -> None:
    page_header("Player Analysis", "Individual athlete profile, trends, workload, recovery and explainable risk.")
    players = get_players(session)
    if not players:
        st.info("No players found.")
        return

    selected_name = st.selectbox("Player", [f"#{p.jersey_number} {p.name} - {p.position}" for p in players])
    player = players[[f"#{p.jersey_number} {p.name} - {p.position}" for p in players].index(selected_name)]
    date_range = st.radio("Date range", list(RANGE_OPTIONS.keys()), horizontal=True)

    st.subheader(player.name)
    st.caption(f"{player.position} | #{player.jersey_number} | Age {player.age} | {player.height_cm:.0f} cm | {player.weight_kg:.0f} kg")

    summary = latest_team_summary(session)
    matching = summary[summary["Player ID"] == player.id] if not summary.empty else summary
    if matching.empty:
        st.info("No monitoring summary yet. Add training and recovery data in Data Entry.")
    else:
        row = matching.iloc[0]
        metric_row({
            "Fitness": row["Fitness"],
            "Performance": row["Performance"],
            "Recovery": row["Recovery"],
            "Fatigue": row["Fatigue"],
            "Risk": row["Risk"],
        })

    series = player_time_series(session, player.id, RANGE_OPTIONS[date_range])
    training_df = series["training"]
    recovery_df = series["recovery"]
    match_df = series["matches"]

    tab_trends, tab_profile, tab_ai = st.tabs(["Trends", "Profile", "AI Insights"])
    with tab_trends:
        if not training_df.empty:
            st.plotly_chart(
                line_chart(training_df, "date", ["training_load", "baseline_workload"], "Training Load vs Baseline"),
                use_container_width=True,
            )
            st.plotly_chart(
                line_chart(training_df, "date", ["fitness_score", "fatigue_score", "injury_risk_pct"], "Fitness, Fatigue and Risk"),
                use_container_width=True,
            )
        if not recovery_df.empty:
            st.plotly_chart(
                line_chart(recovery_df, "date", ["recovery_score", "sleep_hours", "muscle_soreness"], "Recovery, Sleep and Soreness"),
                use_container_width=True,
            )
        if not match_df.empty:
            st.plotly_chart(line_chart(match_df, "date", "performance_score", "Match Performance"), use_container_width=True)

    with tab_profile:
        col_a, col_b = st.columns(2)
        with col_a:
            st.markdown("**Physical Profile**")
            st.write(f"Sprint speed: {player.sprint_speed:.1f} km/h")
            st.write(f"VO2 max: {player.vo2_max:.1f}")
            st.write(f"Resting HR: {player.resting_hr:.0f}")
            st.write(f"Body fat: {player.body_fat_pct:.1f}%")
        with col_b:
            st.plotly_chart(bar_chart(player_attribute_dataframe(player), "Attribute", "Score", "Football Attributes"), use_container_width=True)

    with tab_ai:
        st.markdown("**AI-assisted injury-risk estimation**")
        st.caption("Synthetic demo model. This is not a medical diagnosis and is not clinically validated.")
        explanations = risk_explanation_for_player(session, player)
        if explanations:
            st.dataframe(explanations, use_container_width=True, hide_index=True)
        st.markdown("**Recommendations**")
        for item in recommendations_for_player(session, player):
            st.write(f"- {item['recommendation']} Reason: {item['reason']}")

