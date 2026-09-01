from __future__ import annotations

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go


CHART_TEMPLATE = "plotly_white"
PRIMARY = "#2f6f5e"
MUTED = "#6b7280"
WARNING = "#d97706"
RISK = "#b91c1c"


def line_chart(df: pd.DataFrame, x: str, y: str | list[str], title: str, labels: dict | None = None) -> go.Figure:
    fig = px.line(df, x=x, y=y, title=title, labels=labels or {}, template=CHART_TEMPLATE)
    fig.update_traces(line_width=2.4)
    fig.update_layout(
        title_font_size=16,
        margin=dict(l=8, r=8, t=48, b=8),
        legend_title_text="",
        hovermode="x unified",
    )
    return fig


def bar_chart(df: pd.DataFrame, x: str, y: str, title: str, color: str | None = None) -> go.Figure:
    fig = px.bar(df, x=x, y=y, title=title, color=color, template=CHART_TEMPLATE)
    fig.update_layout(title_font_size=16, margin=dict(l=8, r=8, t=48, b=8), legend_title_text="")
    return fig


def risk_distribution_chart(summary: pd.DataFrame) -> go.Figure:
    order = ["LOW", "MEDIUM", "HIGH"]
    colors = {"LOW": "#2f6f5e", "MEDIUM": "#d97706", "HIGH": "#b91c1c"}
    counts = summary["Risk"].value_counts().reindex(order, fill_value=0).reset_index()
    counts.columns = ["Risk", "Players"]
    fig = px.bar(counts, x="Risk", y="Players", color="Risk", color_discrete_map=colors, template=CHART_TEMPLATE)
    fig.update_layout(title="Injury-Risk Distribution", title_font_size=16, margin=dict(l=8, r=8, t=48, b=8), showlegend=False)
    return fig


def tactical_pitch(players: pd.DataFrame, formation: str) -> go.Figure:
    formation_slots = {
        "4-3-3": [(7, 50), (24, 18), (24, 38), (24, 62), (24, 82), (48, 30), (48, 50), (48, 70), (75, 22), (79, 50), (75, 78)],
        "4-2-3-1": [(7, 50), (24, 18), (24, 38), (24, 62), (24, 82), (43, 40), (43, 60), (62, 22), (64, 50), (62, 78), (81, 50)],
        "4-4-2": [(7, 50), (24, 18), (24, 38), (24, 62), (24, 82), (52, 18), (52, 38), (52, 62), (52, 82), (78, 40), (78, 60)],
        "3-5-2": [(7, 50), (25, 30), (25, 50), (25, 70), (50, 12), (50, 33), (50, 50), (50, 67), (50, 88), (78, 40), (78, 60)],
    }
    selected = players.head(11).copy()
    slots = formation_slots[formation]
    selected["x"] = [slot[0] for slot in slots[: len(selected)]]
    selected["y"] = [slot[1] for slot in slots[: len(selected)]]

    fig = go.Figure()
    fig.add_shape(type="rect", x0=0, y0=0, x1=100, y1=100, line=dict(color="#9ca3af", width=1))
    fig.add_shape(type="line", x0=50, y0=0, x1=50, y1=100, line=dict(color="#d1d5db", width=1))
    fig.add_shape(type="circle", x0=42, y0=42, x1=58, y1=58, line=dict(color="#d1d5db", width=1))
    fig.add_shape(type="rect", x0=0, y0=26, x1=15, y1=74, line=dict(color="#d1d5db", width=1))
    fig.add_shape(type="rect", x0=85, y0=26, x1=100, y1=74, line=dict(color="#d1d5db", width=1))
    fig.add_trace(go.Scatter(
        x=selected["x"],
        y=selected["y"],
        mode="markers+text",
        text=selected["Player"],
        textposition="bottom center",
        marker=dict(size=22, color=selected["Performance"], colorscale="Greens", cmin=50, cmax=95, line=dict(color="#111827", width=1)),
        hovertemplate="<b>%{text}</b><br>Performance: %{marker.color:.1f}<extra></extra>",
    ))
    fig.update_xaxes(visible=False, range=[-2, 102])
    fig.update_yaxes(visible=False, range=[-2, 102], scaleanchor="x", scaleratio=0.68)
    fig.update_layout(
        title=f"Tactical Shape: {formation}",
        template=CHART_TEMPLATE,
        height=520,
        plot_bgcolor="#f7faf7",
        margin=dict(l=8, r=8, t=48, b=8),
        showlegend=False,
    )
    return fig

