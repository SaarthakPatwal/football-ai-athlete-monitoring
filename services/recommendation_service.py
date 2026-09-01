from __future__ import annotations

from sqlalchemy.orm import Session

from database.models import Player
from services.analytics_service import latest_team_summary
from utils.calculations import explain_injury_risk


def recommendations_for_player(session: Session, player: Player) -> list[dict[str, str]]:
    summary = latest_team_summary(session)
    row_df = summary[summary["Player ID"] == player.id]
    if row_df.empty:
        return [{"recommendation": "Review player data availability.", "reason": "No recent monitoring data is available."}]
    row = row_df.iloc[0]
    recommendations: list[dict[str, str]] = []

    if row["Workload Change %"] > 20:
        recommendations.append({
            "recommendation": "Consider reducing high-intensity exposure in the next session.",
            "reason": f"Workload is {row['Workload Change %']:.1f}% above the recent baseline.",
        })
    if row["Recovery"] < 65:
        recommendations.append({
            "recommendation": "Prioritize recovery and reassess readiness before intense work.",
            "reason": f"Recovery score is {row['Recovery']:.1f}, below the preferred range.",
        })
    if row["Fatigue"] > 70:
        recommendations.append({
            "recommendation": "Monitor fatigue markers over the next 48 hours.",
            "reason": f"Fatigue score is {row['Fatigue']:.1f}.",
        })
    if row["Performance"] < 68:
        recommendations.append({
            "recommendation": "Review match and training context before changing role demands.",
            "reason": f"Recent performance score is {row['Performance']:.1f}.",
        })
    if not recommendations:
        recommendations.append({
            "recommendation": "Maintain the current training plan with normal monitoring.",
            "reason": "Workload, recovery and fatigue are currently within expected demo ranges.",
        })
    return recommendations


def risk_explanation_for_player(session: Session, player: Player) -> list[dict[str, str | float]]:
    summary = latest_team_summary(session)
    row_df = summary[summary["Player ID"] == player.id]
    if row_df.empty:
        return []
    row = row_df.iloc[0]
    return [item.__dict__ for item in explain_injury_risk(
        previous_injuries=player.previous_injuries,
        workload_change_pct=float(row["Workload Change %"]),
        fatigue_score=float(row["Fatigue"]),
        recovery_score=float(row["Recovery"]),
        sleep_hours=float(row["Sleep"]),
        sprint_distance_m=float(row["Workload"]) * 1.1,
        soreness=float(row["Soreness"]),
    )]


def answer_question(session: Session, question: str) -> str:
    summary = latest_team_summary(session)
    if summary.empty:
        return "No squad data is available yet. Generate demo data or import CSV files first."
    q = question.lower().strip()

    if "highest workload" in q or "most workload" in q:
        row = summary.sort_values("Workload", ascending=False).iloc[0]
        return f"{row['Player']} has the highest current workload at {row['Workload']:.1f}, {row['Workload Change %']:.1f}% versus baseline."
    if "poor recovery" in q or "low recovery" in q:
        players = summary.sort_values("Recovery").head(3)
        return "Lowest recovery today: " + "; ".join(f"{r.Player} ({r.Recovery:.1f})" for r in players.itertuples())
    if "fatigued" in q or "fatigue" in q:
        players = summary[summary["Fatigue"] >= 70].sort_values("Fatigue", ascending=False)
        if players.empty:
            return "No players are currently classified as high fatigue in the demo data."
        return "High fatigue players: " + "; ".join(f"{r.Player} ({r.Fatigue:.1f})" for r in players.itertuples())
    if "need attention" in q or "attention" in q:
        players = summary[(summary["Risk"] == "HIGH") | (summary["Recovery"] < 60) | (summary["Fatigue"] > 70)]
        if players.empty:
            return "No players currently meet the attention rule of high risk, low recovery or high fatigue."
        return "Players needing attention: " + "; ".join(
            f"{row['Player']}: risk {row['Risk']}, recovery {row['Recovery']:.1f}, fatigue {row['Fatigue']:.1f}"
            for row in players.to_dict("records")
        )
    if "workload trend" in q:
        change = summary["Workload Change %"].mean()
        direction = "above" if change >= 0 else "below"
        return f"Team workload is {abs(change):.1f}% {direction} the recent baseline on average."
    if "compare" in q:
        return "Use the Player Analysis page to select players for visual comparison. The current assistant can answer squad-level workload, recovery, fatigue and attention questions deterministically."
    return "I can answer questions about highest workload, poor recovery, fatigued players, team workload trend and players needing attention using the current database."
