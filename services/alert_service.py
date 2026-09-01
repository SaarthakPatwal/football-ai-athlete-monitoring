from __future__ import annotations

from datetime import date

from sqlalchemy import delete, select
from sqlalchemy.orm import Session

from database.models import Alert
from services.analytics_service import latest_team_summary


def generate_alerts(session: Session) -> list[Alert]:
    session.execute(delete(Alert))
    today = date.today()
    summary = latest_team_summary(session)
    alerts: list[Alert] = []
    if summary.empty:
        return alerts

    for row in summary.to_dict("records"):
        if row["Risk"] == "HIGH":
            alerts.append(Alert(
                player_id=int(row["Player ID"]),
                date=today,
                priority="HIGH",
                category="Injury Risk",
                message="AI-assisted injury-risk estimate is high.",
                reason=f"Risk {row['Risk %']:.1f}%, workload change {row['Workload Change %']:.1f}%, recovery {row['Recovery']:.1f}.",
            ))
        if row["Recovery"] < 60:
            alerts.append(Alert(
                player_id=int(row["Player ID"]),
                date=today,
                priority="MEDIUM",
                category="Recovery",
                message="Recovery score is below the preferred range.",
                reason=f"Recovery {row['Recovery']:.1f}, sleep {row['Sleep']:.1f}h, soreness {row['Soreness']:.1f}.",
            ))
        if row["Workload Change %"] > 20:
            alerts.append(Alert(
                player_id=int(row["Player ID"]),
                date=today,
                priority="HIGH" if row["Workload Change %"] > 35 else "MEDIUM",
                category="Workload",
                message="Player workload is above recent baseline.",
                reason=f"Current workload is {row['Workload Change %']:.1f}% above baseline.",
            ))
        if row["Fitness"] > 82 and row["Risk"] == "LOW":
            alerts.append(Alert(
                player_id=int(row["Player ID"]),
                date=today,
                priority="LOW",
                category="Fitness",
                message="Fitness profile is stable or improving.",
                reason=f"Fitness {row['Fitness']:.1f} with low estimated risk.",
            ))

    session.add_all(alerts)
    return alerts


def get_alerts(session: Session) -> list[Alert]:
    return list(session.scalars(select(Alert).order_by(Alert.priority.desc(), Alert.date.desc())))

