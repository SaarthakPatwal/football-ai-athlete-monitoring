from __future__ import annotations

import pandas as pd
import streamlit as st
from sqlalchemy import select
from sqlalchemy.orm import Session

from database.models import NutritionRecord
from services.player_service import get_players
from utils.charts import bar_chart
from utils.ui import page_header


def render(session: Session) -> None:
    page_header("Nutrition", "Daily intake compared with performance-oriented targets.")
    players = get_players(session)
    if not players:
        st.info("No players found. Add a player in Data Entry.")
        return
    player = st.selectbox("Player", players, format_func=lambda p: f"#{p.jersey_number} {p.name}")
    record = session.scalars(
        select(NutritionRecord).where(NutritionRecord.player_id == player.id).order_by(NutritionRecord.date.desc()).limit(1)
    ).first()
    if not record:
        st.info("No nutrition records are available.")
        return

    targets = {
        "Calories": 3600,
        "Protein": round(player.weight_kg * 2.0, 1),
        "Carbohydrates": 430,
        "Fats": 95,
        "Water": 4.0,
    }
    current = {
        "Calories": record.calories,
        "Protein": record.protein_g,
        "Carbohydrates": record.carbohydrates_g,
        "Fats": record.fats_g,
        "Water": record.water_l,
    }
    df = pd.DataFrame([
        {"Metric": metric, "Current": current[metric], "Target": target}
        for metric, target in targets.items()
    ])
    st.dataframe(df, use_container_width=True, hide_index=True)
    chart_df = df.melt(id_vars="Metric", value_vars=["Current", "Target"], var_name="Type", value_name="Value")
    st.plotly_chart(bar_chart(chart_df, "Metric", "Value", "Consumed vs Target", color="Type"), use_container_width=True)
    st.caption("Recommendations are general performance-support guidance for demo use, not medical or clinical dietary advice.")

