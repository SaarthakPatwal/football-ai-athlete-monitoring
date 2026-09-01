from __future__ import annotations

import streamlit as st


def apply_theme() -> None:
    st.markdown(
        """
        <style>
        :root, .stApp, [data-testid="stAppViewContainer"] {
            --primary: #b91c1c;
            --text: #111827;
            --muted: #4b5563;
            --surface: #ffffff;
            --surface-muted: #f3f4f6;
            --border: #e5e7eb;
            --text-color: #111827;
            --secondary-text-color: #4b5563;
            --background-color: #fbfbfa;
            --secondary-background-color: #f3f4f6;
        }
        html, body, .stApp, [data-testid="stAppViewContainer"], [data-testid="stMain"] {
            background-color: #fbfbfa !important;
            color: #111827 !important;
        }
        p, span, label, li, h1, h2, h3, h4, h5, h6, small {
            color: inherit;
        }
        h1, h2, h3 {
            letter-spacing: 0;
            color: #111827 !important;
        }
        [data-testid="stCaption"], [data-testid="stCaptionContainer"], .stCaption, .stMarkdown p {
            color: #374151 !important;
        }

        section[data-testid="stSidebar"] {
            background: #f3f4f6 !important;
            border-right: 1px solid #e5e7eb;
            color: #111827 !important;
        }
        section[data-testid="stSidebar"] [data-testid="stMarkdownContainer"],
        section[data-testid="stSidebar"] [data-testid="stMarkdownContainer"] p,
        section[data-testid="stSidebar"] [data-testid="stWidgetLabel"],
        section[data-testid="stSidebar"] [data-testid="stCaptionContainer"],
        section[data-testid="stSidebar"] [data-testid="stCaptionContainer"] p,
        section[data-testid="stSidebar"] h1,
        section[data-testid="stSidebar"] h2,
        section[data-testid="stSidebar"] h3,
        section[data-testid="stSidebar"] [data-testid="stRadio"] label,
        section[data-testid="stSidebar"] [data-testid="stRadio"] p,
        section[data-testid="stSidebar"] [role="radiogroup"] label,
        section[data-testid="stSidebar"] [role="radiogroup"] p,
        section[data-testid="stSidebar"] [role="radiogroup"] span,
        section[data-testid="stSidebar"] [role="radiogroup"] div {
            color: #111827 !important;
            -webkit-text-fill-color: #111827 !important;
        }

        div[data-testid="stMetric"] {
            background: #ffffff !important;
            border: 1px solid #e5e7eb;
            border-radius: 8px;
            padding: 14px 16px;
            color: #111827 !important;
        }
        div[data-testid="stMetric"] *,
        div[data-testid="stMetricLabel"],
        div[data-testid="stMetricValue"],
        div[data-testid="stMetricDelta"] {
            color: #111827 !important;
            -webkit-text-fill-color: #111827 !important;
        }
        div[data-testid="stMetricLabel"],
        div[data-testid="stMetricLabel"] * {
            color: #374151 !important;
            -webkit-text-fill-color: #374151 !important;
        }
        div[data-testid="stMetricValue"],
        div[data-testid="stMetricValue"] * {
            color: #111827 !important;
            -webkit-text-fill-color: #111827 !important;
            font-weight: 700;
        }

        .stButton > button,
        button[kind="secondary"],
        [data-testid="stBaseButton-secondary"] {
            background-color: #ffffff !important;
            color: #111827 !important;
            border: 1px solid #d1d5db !important;
        }
        .stButton > button[kind="primary"],
        button[kind="primary"],
        [data-testid="stBaseButton-primary"] {
            background-color: #b91c1c !important;
            color: #ffffff !important;
            border: 1px solid #b91c1c !important;
        }

        .status-low {
            color: #2f6f5e;
            font-weight: 700;
        }
        .status-medium {
            color: #d97706;
            font-weight: 700;
        }
        .status-high {
            color: #b91c1c;
            font-weight: 700;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )


def page_header(title: str, description: str) -> None:
    st.title(title)
    st.caption(description)


def metric_row(metrics: dict[str, str | float | int], suffix: str = "") -> None:
    columns = st.columns(len(metrics))
    for column, (label, value) in zip(columns, metrics.items()):
        display = f"{value}{suffix}" if isinstance(value, (int, float)) and suffix else value
        column.metric(label, display)


def risk_badge(risk: str) -> str:
    risk_lower = risk.lower()
    return f'<span class="status-{risk_lower}">{risk}</span>'
