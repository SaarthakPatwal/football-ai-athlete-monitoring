import pandas as pd
import streamlit as st
from services.data_service import dataset_counts
from ml.train import readiness
from views.predictions import prediction_tables


def render(session):
    st.title("Football Player ML Prediction & Analytics System")
    counts = dataset_counts(session)
    st.subheader("Dataset status")
    columns = st.columns(4)
    for index, (key, value) in enumerate(counts.items()):
        columns[index % 4].metric(key.replace("_", " ").title(), value)
    if not any(counts.values()):
        st.info("No data available. Add players using Manual Entry or CSV Upload on the Data page.")
    st.subheader("ML readiness")
    statuses = readiness(session)
    st.dataframe(pd.DataFrame([{"Task": task.title(), "Usable samples": status["dataset_rows"],
                               "Positive injury samples": str(status["positive_labels"]) if task == "injury" else "-",
                               "Status": "Ready to train" if status["ready"] else "Insufficient history"}
                              for task, status in statuses.items()]), hide_index=True, width="stretch")
    for task, status in statuses.items():
        if not status["ready"]:
            with st.expander(f"{task.title()} data requirements"):
                for reason in status["reasons"]:
                    st.write(reason)
    st.subheader("Predictions")
    prediction_tables(session)

    from views.health import dashboard_summary
    dashboard_summary(session)
