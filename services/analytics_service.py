from __future__ import annotations

from datetime import date, timedelta

import pandas as pd
from sqlalchemy import select
from sqlalchemy.orm import Session

from database.models import MatchRecord, Player, RecoveryRecord, TrainingSession
from utils.calculations import classify_risk


SUMMARY_COLUMNS = [
    "Player ID",
    "Player",
    "Position",
    "Fitness",
    "Recovery",
    "Fatigue",
    "Performance",
    "Workload",
    "Baseline",
    "Workload Change %",
    "Risk %",
    "Risk",
    "Sleep",
    "Soreness",
]


def _records_to_dataframe(records: list[object]) -> pd.DataFrame:
    df = pd.DataFrame([record.__dict__ for record in records])
    if not df.empty and "_sa_instance_state" in df:
        df = df.drop(columns=["_sa_instance_state"])
    return df


def latest_team_summary(session: Session) -> pd.DataFrame:
    players = list(session.scalars(select(Player).order_by(Player.jersey_number)))
    rows: list[dict] = []
    for player in players:
        latest_training = session.scalars(
            select(TrainingSession)
            .where(TrainingSession.player_id == player.id)
            .order_by(TrainingSession.date.desc())
            .limit(1)
        ).first()
        latest_recovery = session.scalars(
            select(RecoveryRecord)
            .where(RecoveryRecord.player_id == player.id)
            .order_by(RecoveryRecord.date.desc())
            .limit(1)
        ).first()
        recent_matches = list(session.scalars(
            select(MatchRecord)
            .where(MatchRecord.player_id == player.id)
            .order_by(MatchRecord.date.desc())
            .limit(5)
        ))
        performance = (
            sum(match.performance_score for match in recent_matches) / len(recent_matches)
            if recent_matches else player.historical_performance
        )
        rows.append({
            "Player ID": player.id,
            "Player": player.name,
            "Position": player.position,
            "Fitness": latest_training.fitness_score if latest_training else round(player.historical_performance, 1),
            "Recovery": latest_recovery.recovery_score if latest_recovery else 70.0,
            "Fatigue": latest_training.fatigue_score if latest_training else 0.0,
            "Performance": round(performance, 1),
            "Workload": latest_training.training_load if latest_training else 0.0,
            "Baseline": latest_training.baseline_workload if latest_training else player.historical_workload,
            "Workload Change %": latest_training.workload_change_pct if latest_training else 0.0,
            "Risk %": latest_training.injury_risk_pct if latest_training else 0.0,
            "Risk": classify_risk(latest_training.injury_risk_pct) if latest_training else "LOW",
            "Sleep": latest_recovery.sleep_hours if latest_recovery else 0.0,
            "Soreness": latest_recovery.muscle_soreness if latest_recovery else 0.0,
        })
    return pd.DataFrame(rows, columns=SUMMARY_COLUMNS)


def team_kpis(summary: pd.DataFrame) -> dict[str, float | int]:
    if summary.empty:
        return {
            "Squad Size": 0,
            "Average Fitness": 0,
            "Average Recovery": 0,
            "Average Fatigue": 0,
            "Average Performance": 0,
            "High Risk Players": 0,
            "Players Needing Attention": 0,
        }
    return {
        "Squad Size": len(summary),
        "Average Fitness": round(summary["Fitness"].mean(), 1),
        "Average Recovery": round(summary["Recovery"].mean(), 1),
        "Average Fatigue": round(summary["Fatigue"].mean(), 1),
        "Average Performance": round(summary["Performance"].mean(), 1),
        "High Risk Players": int((summary["Risk"] == "HIGH").sum()),
        "Players Needing Attention": int(((summary["Risk"] == "HIGH") | (summary["Recovery"] < 60) | (summary["Fatigue"] > 70)).sum()),
    }


def training_dataframe(session: Session, days: int = 30) -> pd.DataFrame:
    since = date.today() - timedelta(days=days)
    records = list(session.scalars(select(TrainingSession).where(TrainingSession.date >= since)))
    return _records_to_dataframe(records)


def recovery_dataframe(session: Session, days: int = 30) -> pd.DataFrame:
    since = date.today() - timedelta(days=days)
    records = list(session.scalars(select(RecoveryRecord).where(RecoveryRecord.date >= since)))
    return _records_to_dataframe(records)


def match_dataframe(session: Session, limit: int = 400) -> pd.DataFrame:
    records = list(session.scalars(select(MatchRecord).order_by(MatchRecord.date.desc()).limit(limit)))
    return _records_to_dataframe(records)


def daily_team_trends(session: Session, days: int = 30) -> pd.DataFrame:
    training = training_dataframe(session, days)
    recovery = recovery_dataframe(session, days)
    if training.empty or recovery.empty:
        return pd.DataFrame()
    training_grouped = training.groupby("date", as_index=False).agg({
        "training_load": "mean",
        "fitness_score": "mean",
        "fatigue_score": "mean",
        "injury_risk_pct": "mean",
    })
    recovery_grouped = recovery.groupby("date", as_index=False).agg({
        "recovery_score": "mean",
        "sleep_hours": "mean",
    })
    return training_grouped.merge(recovery_grouped, on="date", how="inner")

