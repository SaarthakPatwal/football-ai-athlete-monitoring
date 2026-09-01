from __future__ import annotations

import pandas as pd
from sqlalchemy import select
from sqlalchemy.orm import Session

from database.models import MatchRecord, Player, RecoveryRecord, TrainingSession


def get_players(session: Session) -> list[Player]:
    return list(session.scalars(select(Player).order_by(Player.jersey_number)))


def get_player(session: Session, player_id: int) -> Player | None:
    return session.get(Player, player_id)


def players_dataframe(session: Session) -> pd.DataFrame:
    players = get_players(session)
    return pd.DataFrame([{
        "ID": p.id,
        "Name": p.name,
        "Position": p.position,
        "Age": p.age,
        "Jersey": p.jersey_number,
        "Status": p.squad_status,
        "Foot": p.preferred_foot,
        "Nationality": p.nationality,
        "Matches": p.matches_played,
        "Goals": p.goals,
        "Assists": p.assists,
    } for p in players])


def player_attribute_dataframe(player: Player) -> pd.DataFrame:
    return pd.DataFrame([
        {"Attribute": "Passing", "Score": player.passing},
        {"Attribute": "Shooting", "Score": player.shooting},
        {"Attribute": "Dribbling", "Score": player.dribbling},
        {"Attribute": "Tackling", "Score": player.tackling},
        {"Attribute": "Crossing", "Score": player.crossing},
        {"Attribute": "Positioning", "Score": player.positioning},
        {"Attribute": "Vision", "Score": player.vision},
        {"Attribute": "Decision Making", "Score": player.decision_making},
        {"Attribute": "Pace", "Score": player.pace},
    ])


def player_time_series(session: Session, player_id: int, days: int = 30) -> dict[str, pd.DataFrame]:
    training_query = (
        select(TrainingSession)
        .where(TrainingSession.player_id == player_id)
        .order_by(TrainingSession.date.desc())
        .limit(days)
    )
    recovery_query = (
        select(RecoveryRecord)
        .where(RecoveryRecord.player_id == player_id)
        .order_by(RecoveryRecord.date.desc())
        .limit(days)
    )
    match_query = (
        select(MatchRecord)
        .where(MatchRecord.player_id == player_id)
        .order_by(MatchRecord.date.desc())
        .limit(12)
    )
    training = pd.DataFrame([row.__dict__ for row in session.scalars(training_query)])
    recovery = pd.DataFrame([row.__dict__ for row in session.scalars(recovery_query)])
    matches = pd.DataFrame([row.__dict__ for row in session.scalars(match_query)])
    for df in [training, recovery, matches]:
        if not df.empty and "_sa_instance_state" in df:
            df.drop(columns=["_sa_instance_state"], inplace=True)
        if not df.empty and "date" in df:
            df.sort_values("date", inplace=True)
    return {"training": training, "recovery": recovery, "matches": matches}

