import streamlit as st


def apply_theme():
    st.markdown("""
    <style>
    .block-container {max-width: 1280px; padding-top: 2rem;}
    h1 {font-size: 2rem !important; letter-spacing: 0 !important;}
    h2 {font-size: 1.3rem !important; letter-spacing: 0 !important;}
    [data-testid="stMetricValue"] {font-size: 1.7rem;}
    button {border-radius: 4px !important;}
    </style>
    """, unsafe_allow_html=True)


def show_table(frame, empty="No data available."):
    if frame.empty:
        st.info(empty)
    else:
        st.dataframe(frame, hide_index=True, width="stretch")
