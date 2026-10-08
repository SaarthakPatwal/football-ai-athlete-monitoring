from datetime import date, timedelta
import streamlit as st
from ml.predict import predict
from ml.train import load_artifact
from utils.ui import show_table


def prediction_tables(session, player_id=None, point=None):
    for task in ("injury", "performance"):
        st.markdown(f"**{'Injury probability' if task == 'injury' else 'Predicted next match rating'}**")
        artifact = load_artifact(session, task)
        if artifact is None:
            st.info(f"No trained {task} model for the current dataset. Train it on Model Analysis.")
            continue
        if point is not None and point < date.fromisoformat(artifact["metadata"]["fitted_through"]):
            st.warning("Select a later prediction date.")
            continue
        frame = predict(session, task, point)
        if player_id and not frame.empty:
            frame = frame[frame.player_id == player_id]
        if task == "injury" and not frame.empty:
            st.dataframe(frame, hide_index=True, width="stretch",
                         column_config={"probability": st.column_config.NumberColumn("Probability", format="percent")})
        else:
            show_table(frame, "No eligible player history at this prediction date. Recent training and recovery are required; performance also needs prior matches.")
        with st.expander(f"{task.title()} model features"):
            st.dataframe(artifact["metadata"]["top_model_contributors"][:12], hide_index=True, width="stretch")


def render(session):
    st.title("ML Predictions")
    point = st.date_input("Prediction date", value=date.today() + timedelta(days=1),
                          max_value=date.today() + timedelta(days=1))
    prediction_tables(session, point=point)
