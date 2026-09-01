from __future__ import annotations

import pandas as pd
import streamlit as st
from sqlalchemy.orm import Session

from utils.ui import page_header


REQUIRED_COLUMNS = {
    "players.csv": {"name", "age", "position", "jersey_number"},
    "training.csv": {"player_id", "date", "duration_min", "rpe"},
    "matches.csv": {"player_id", "date", "opponent", "minutes_played"},
    "recovery.csv": {"player_id", "date", "sleep_hours", "sleep_quality", "hrv"},
    "nutrition.csv": {"player_id", "date", "calories", "protein_g", "water_l"},
}


def render(session: Session) -> None:
    page_header("Data Import", "CSV validation preview for future database imports.")
    st.caption("Phase 1 validates files and reports issues without crashing. Persisted imports can be added after the schema stabilizes.")
    file_type = st.selectbox("Expected file", list(REQUIRED_COLUMNS.keys()))
    uploaded = st.file_uploader("Upload CSV", type=["csv"])
    if not uploaded:
        st.info("Upload a CSV to validate its structure.")
        return

    try:
        df = pd.read_csv(uploaded)
    except Exception as exc:
        st.error(f"Could not read CSV: {exc}")
        return

    required = REQUIRED_COLUMNS[file_type]
    missing = sorted(required - set(df.columns))
    invalid_rows = int(df.isna().any(axis=1).sum())
    accepted_rows = len(df) - invalid_rows if not missing else 0

    st.metric("Rows imported", accepted_rows)
    st.metric("Rows rejected", invalid_rows if not missing else len(df))
    if missing:
        st.warning("Missing columns: " + ", ".join(missing))
    else:
        st.success("Required columns are present.")
    st.dataframe(df.head(50), use_container_width=True, hide_index=True)

