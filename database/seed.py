from __future__ import annotations

from sqlalchemy import delete, func, select
from sqlalchemy.orm import Session

from database.models import Alert, InjuryHistory, MatchRecord, NutritionRecord, Player, RecoveryRecord, TrainingSession, WellnessCheckIn
from services.alert_service import generate_alerts
from utils.data_generator import generate_demo_data


TABLES_IN_DELETE_ORDER = [
    Alert,
    WellnessCheckIn,
    InjuryHistory,
    MatchRecord,
    NutritionRecord,
    RecoveryRecord,
    TrainingSession,
    Player,
]


def has_players(session: Session) -> bool:
    return bool(session.scalar(select(func.count(Player.id))))


def clear_database(session: Session) -> None:
    for model in TABLES_IN_DELETE_ORDER:
        session.execute(delete(model))
    session.commit()


def seed_demo_data(session: Session, force: bool = False) -> None:
    if has_players(session) and not force:
        return
    if force:
        clear_database(session)

    demo_data = generate_demo_data()
    model_map = {
        "players": Player,
        "training_sessions": TrainingSession,
        "recovery_records": RecoveryRecord,
        "nutrition_records": NutritionRecord,
        "match_records": MatchRecord,
        "injury_history": InjuryHistory,
    }
    for key, model in model_map.items():
        session.add_all(model(**row) for row in demo_data[key])
    session.commit()
    generate_alerts(session)
    session.commit()
