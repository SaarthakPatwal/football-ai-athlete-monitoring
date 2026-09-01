from __future__ import annotations

import streamlit as st
from sqlalchemy.orm import Session

from services.recommendation_service import answer_question
from utils.ui import page_header


EXAMPLES = [
    "Who has the highest workload?",
    "Who has poor recovery?",
    "Which players are fatigued?",
    "What is the team's workload trend?",
    "Which players need attention?",
]


def render(session: Session) -> None:
    page_header("AI Assistant", "A deterministic analytics assistant that answers from the current database.")
    st.caption("The interface is ready for a future LLM API, but this version never invents statistics.")
    selected_example = st.selectbox("Example questions", [""] + EXAMPLES)
    question = st.text_input("Coach question", value=selected_example)
    if question:
        st.markdown("**Assistant**")
        st.write(answer_question(session, question))

