from __future__ import annotations

import pandas as pd
import streamlit as st
from sqlalchemy.orm import Session

from services.alert_service import generate_alerts
from utils.ui import page_header


def render(session: Session) -> None:
    page_header("Alerts", "Generated from workload, recovery, fatigue and risk indicators.")
    if st.button("Refresh Alerts"):
        generate_alerts(session)
        session.commit()
        st.success("Alerts refreshed.")

    alerts = generate_alerts(session)
    session.commit()
    if not alerts:
        st.success("No alerts generated from current rules.")
        return
    df = pd.DataFrame([{
        "Date": alert.date,
        "Priority": alert.priority,
        "Category": alert.category,
        "Player ID": alert.player_id,
        "Message": alert.message,
        "Reason": alert.reason,
    } for alert in alerts])
    priority = st.selectbox("Priority", ["All", "HIGH", "MEDIUM", "LOW"])
    if priority != "All":
        df = df[df["Priority"] == priority]
    st.dataframe(df, use_container_width=True, hide_index=True)

