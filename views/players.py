import streamlit as st
from services.data_service import read_dataset
from services.feature_service import History, calculate_training_load
from views.predictions import prediction_tables
from utils.ui import show_table


def render(session):
    st.title("Players")
    roster = read_dataset(session, "players")
    if roster.empty:
        st.info("No players added yet.")
        return
    show_table(roster)
    names = dict(zip(roster.player_id, roster.name))
    player_id = st.selectbox("Player", list(names), format_func=lambda value: f"{value} - {names[value]}")
    player = next(row for row in roster.itertuples(index=False) if row.player_id == player_id)
    st.subheader(player.name)
    for key in ("training", "recovery", "matches", "injuries"):
        frame = read_dataset(session, key)
        date_field = "match_date" if key == "matches" else "injury_date" if key == "injuries" else "date"
        frame = frame[frame.player_id == player_id].sort_values(date_field)
        with st.expander(key.title(), expanded=key == "training"):
            show_table(frame.tail(30))
            if key == "training" and not frame.empty:
                st.line_chart(frame.assign(training_load=calculate_training_load(frame.duration_min, frame.rpe)).set_index("date")[["training_load"]])
            if key == "matches" and not frame.empty:
                st.line_chart(frame.set_index("match_date")[["rating"]])
    with st.expander("Feature Engineering"):
        from datetime import date, timedelta
        features = History(session).snapshot(player, date.today() + timedelta(days=1))
        st.dataframe([features], hide_index=True, width="stretch")
    st.subheader("ML predictions")
    prediction_tables(session, player_id=player_id)
