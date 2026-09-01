from __future__ import annotations

from datetime import date

import numpy as np
from sqlalchemy import select
from sqlalchemy.orm import Session

from database.models import MatchRecord, NutritionRecord, Player, RecoveryRecord, TrainingSession, WellnessCheckIn
from services.alert_service import generate_alerts
from utils.calculations import (
    calculate_fatigue_score,
    calculate_recovery_score,
    calculate_training_load,
    clamp,
    estimate_injury_risk,
)


POSITION_CHOICES = ["GK", "RB", "CB", "LB", "DM", "CM", "AM", "RW", "LW", "ST"]


def validate_range(label: str, value: float, low: float, high: float) -> list[str]:
    if value < low or value > high:
        return [f"{label} must be between {low:g} and {high:g}."]
    return []


def create_player(session: Session, data: dict) -> tuple[bool, list[str]]:
    errors: list[str] = []
    errors += validate_range("Age", data["age"], 15, 45)
    errors += validate_range("Height", data["height_cm"], 140, 220)
    errors += validate_range("Weight", data["weight_kg"], 45, 120)
    errors += validate_range("Jersey number", data["jersey_number"], 1, 99)
    if data["position"] not in POSITION_CHOICES:
        errors.append("Position must be a recognized football position.")
    if session.scalar(select(Player).where(Player.jersey_number == data["jersey_number"])):
        errors.append("Jersey number is already assigned.")
    if errors:
        return False, errors

    defaults = {
        "nationality": "Not recorded",
        "squad_status": "Active",
        "sprint_speed": 30.0,
        "acceleration": 70.0,
        "vo2_max": 56.0,
        "resting_hr": 50.0,
        "max_hr": 190.0,
        "body_fat_pct": 11.0,
        "strength": 70.0,
        "agility": 70.0,
        "passing": 70.0,
        "shooting": 65.0,
        "dribbling": 70.0,
        "tackling": 65.0,
        "crossing": 65.0,
        "positioning": 70.0,
        "vision": 70.0,
        "decision_making": 70.0,
        "pace": 70.0,
        "matches_played": 0,
        "minutes_played": 0,
        "goals": 0,
        "assists": 0,
        "previous_injuries": 0,
        "historical_performance": 70.0,
        "historical_workload": 360.0,
    }
    session.add(Player(**{**defaults, **data}))
    session.commit()
    return True, []


def update_player(session: Session, player: Player, data: dict) -> tuple[bool, list[str]]:
    errors: list[str] = []
    errors += validate_range("Age", data["age"], 15, 45)
    errors += validate_range("Height", data["height_cm"], 140, 220)
    errors += validate_range("Weight", data["weight_kg"], 45, 120)
    existing = session.scalar(select(Player).where(Player.jersey_number == data["jersey_number"], Player.id != player.id))
    if existing:
        errors.append("Jersey number is already assigned.")
    if errors:
        return False, errors
    for key, value in data.items():
        setattr(player, key, value)
    session.commit()
    return True, []


def delete_player(session: Session, player: Player) -> None:
    session.delete(player)
    session.commit()
    generate_alerts(session)
    session.commit()


def _latest_recovery(session: Session, player_id: int, target_date: date | None = None) -> RecoveryRecord | None:
    query = select(RecoveryRecord).where(RecoveryRecord.player_id == player_id)
    if target_date:
        query = query.where(RecoveryRecord.date <= target_date)
    return session.scalars(query.order_by(RecoveryRecord.date.desc()).limit(1)).first()


def _latest_training(session: Session, player_id: int, target_date: date | None = None) -> TrainingSession | None:
    query = select(TrainingSession).where(TrainingSession.player_id == player_id)
    if target_date:
        query = query.where(TrainingSession.date <= target_date)
    return session.scalars(query.order_by(TrainingSession.date.desc()).limit(1)).first()


def _workload_context(session: Session, player_id: int, load: float, target_date: date) -> tuple[float, float, float]:
    recent = list(session.scalars(
        select(TrainingSession)
        .where(TrainingSession.player_id == player_id, TrainingSession.date < target_date)
        .order_by(TrainingSession.date.desc())
        .limit(28)
    ))
    previous_loads = [record.training_load for record in recent]
    acute = (sum(previous_loads[:6]) + load) / min(len(previous_loads[:6]) + 1, 7)
    baseline = (sum(previous_loads) + load) / min(len(previous_loads) + 1, 28) if previous_loads else max(load, 1)
    change = ((acute - baseline) / max(baseline, 1)) * 100
    return round(acute, 1), round(baseline, 1), round(change, 1)


def add_training_session(session: Session, player: Player, data: dict) -> tuple[bool, list[str]]:
    errors: list[str] = []
    errors += validate_range("Duration", data["duration_min"], 0, 180)
    errors += validate_range("RPE", data["rpe"], 0, 10)
    errors += validate_range("Distance", data["distance_km"], 0, 18)
    errors += validate_range("Sprint distance", data["sprint_distance_m"], 0, 1600)
    errors += validate_range("High-speed running", data["high_speed_running_m"], 0, 2600)
    errors += validate_range("Average heart rate", data["average_hr"], 40, 220)
    errors += validate_range("Maximum heart rate", data["max_hr"], 40, 230)
    if data["max_hr"] < data["average_hr"]:
        errors.append("Maximum heart rate cannot be lower than average heart rate.")
    if errors:
        return False, errors

    load = calculate_training_load(data["duration_min"], data["rpe"])
    acute, baseline, change = _workload_context(session, player.id, load, data["date"])
    recovery = _latest_recovery(session, player.id, data["date"])
    recovery_score = recovery.recovery_score if recovery else 72.0
    sleep_hours = recovery.sleep_hours if recovery else 7.5
    soreness = recovery.muscle_soreness if recovery else 35.0
    hrv = recovery.hrv if recovery else 75.0
    fatigue = calculate_fatigue_score(load, baseline, sleep_hours, recovery_score, soreness, hrv)
    risk = estimate_injury_risk(player.age, player.previous_injuries, change, fatigue, recovery_score, sleep_hours, data["sprint_distance_m"], soreness)
    recent_fitness = _latest_training(session, player.id, data["date"])
    fitness_base = recent_fitness.fitness_score if recent_fitness else 76.0
    fitness = clamp(fitness_base + min(load - baseline, 160) / 90 - fatigue * 0.04)

    session.add(TrainingSession(
        player_id=player.id,
        training_load=load,
        acute_workload=acute,
        baseline_workload=baseline,
        workload_change_pct=change,
        fatigue_score=fatigue,
        fitness_score=round(fitness, 1),
        injury_risk_pct=risk,
        **data,
    ))
    session.commit()
    generate_alerts(session)
    session.commit()
    return True, []


def update_training_session(session: Session, record: TrainingSession, data: dict) -> tuple[bool, list[str]]:
    player = session.get(Player, record.player_id)
    if not player:
        return False, ["Player was not found."]
    errors: list[str] = []
    errors += validate_range("Duration", data["duration_min"], 0, 180)
    errors += validate_range("RPE", data["rpe"], 0, 10)
    errors += validate_range("Distance", data["distance_km"], 0, 18)
    errors += validate_range("Sprint distance", data["sprint_distance_m"], 0, 1600)
    errors += validate_range("High-speed running", data["high_speed_running_m"], 0, 2600)
    errors += validate_range("Average heart rate", data["average_hr"], 40, 220)
    errors += validate_range("Maximum heart rate", data["max_hr"], 40, 230)
    if data["max_hr"] < data["average_hr"]:
        errors.append("Maximum heart rate cannot be lower than average heart rate.")
    if errors:
        return False, errors

    load = calculate_training_load(data["duration_min"], data["rpe"])
    acute, baseline, change = _workload_context(session, player.id, load, data["date"])
    recovery = _latest_recovery(session, player.id, data["date"])
    recovery_score = recovery.recovery_score if recovery else 72.0
    sleep_hours = recovery.sleep_hours if recovery else 7.5
    soreness = recovery.muscle_soreness if recovery else 35.0
    hrv = recovery.hrv if recovery else 75.0
    fatigue = calculate_fatigue_score(load, baseline, sleep_hours, recovery_score, soreness, hrv)
    risk = estimate_injury_risk(player.age, player.previous_injuries, change, fatigue, recovery_score, sleep_hours, data["sprint_distance_m"], soreness)

    for key, value in data.items():
        setattr(record, key, value)
    record.training_load = load
    record.acute_workload = acute
    record.baseline_workload = baseline
    record.workload_change_pct = change
    record.fatigue_score = fatigue
    record.fitness_score = round(clamp(record.fitness_score - fatigue * 0.01), 1)
    record.injury_risk_pct = risk
    session.commit()
    generate_alerts(session)
    session.commit()
    return True, []


def add_recovery_record(session: Session, player: Player, data: dict) -> tuple[bool, list[str]]:
    errors: list[str] = []
    errors += validate_range("Sleep duration", data["sleep_hours"], 0, 14)
    errors += validate_range("Sleep quality", data["sleep_quality"], 0, 100)
    errors += validate_range("HRV", data["hrv"], 20, 130)
    errors += validate_range("Resting heart rate", data["resting_hr"], 30, 110)
    errors += validate_range("Hydration", data["hydration"], 0, 100)
    errors += validate_range("Muscle soreness", data["muscle_soreness"], 0, 100)
    errors += validate_range("Stress", data["stress"], 0, 100)
    errors += validate_range("Mood", data["mood"], 0, 100)
    if errors:
        return False, errors

    recovery_score = calculate_recovery_score(
        sleep_hours=data["sleep_hours"],
        sleep_quality=data["sleep_quality"],
        hrv=data["hrv"],
        resting_hr=data["resting_hr"],
        hydration=data["hydration"],
        muscle_soreness=data["muscle_soreness"],
        stress=data["stress"],
        mood=data["mood"],
        rest_day=data["rest_day"],
    )
    session.add(RecoveryRecord(player_id=player.id, recovery_score=recovery_score, **data))
    latest_training = _latest_training(session, player.id, data["date"])
    if latest_training:
        latest_training.fatigue_score = calculate_fatigue_score(
            latest_training.training_load,
            latest_training.baseline_workload,
            data["sleep_hours"],
            recovery_score,
            data["muscle_soreness"],
            data["hrv"],
        )
        latest_training.injury_risk_pct = estimate_injury_risk(
            player.age,
            player.previous_injuries,
            latest_training.workload_change_pct,
            latest_training.fatigue_score,
            recovery_score,
            data["sleep_hours"],
            latest_training.sprint_distance_m,
            data["muscle_soreness"],
        )
    session.commit()
    generate_alerts(session)
    session.commit()
    return True, []


def add_match_record(session: Session, player: Player, data: dict) -> tuple[bool, list[str]]:
    errors: list[str] = []
    for label, key in [
        ("Minutes played", "minutes_played"),
        ("Goals", "goals"),
        ("Assists", "assists"),
        ("Shots", "shots"),
        ("Shots on target", "shots_on_target"),
        ("Passes", "passes"),
        ("Key passes", "key_passes"),
        ("Tackles", "tackles"),
        ("Interceptions", "interceptions"),
        ("Duels won", "duels_won"),
        ("Progressive passes", "progressive_passes"),
    ]:
        if data[key] < 0:
            errors.append(f"{label} cannot be negative.")
    errors += validate_range("Minutes played", data["minutes_played"], 0, 130)
    errors += validate_range("Pass accuracy", data["pass_accuracy"], 0, 100)
    errors += validate_range("Distance", data["distance_km"], 0, 16)
    errors += validate_range("Sprint distance", data["sprint_distance_m"], 0, 1400)
    errors += validate_range("High-speed running", data["high_speed_running_m"], 0, 2400)
    errors += validate_range("Player rating", data["player_rating"], 0, 10)
    if data["shots_on_target"] > data["shots"]:
        errors.append("Shots on target cannot exceed total shots.")
    if errors:
        return False, errors

    performance = clamp(
        data["player_rating"] * 10
        + data["goals"] * 3
        + data["assists"] * 2
        + data["key_passes"] * 0.5
        + (data["pass_accuracy"] - 75) * 0.1
    )
    player.matches_played += 1 if data["minutes_played"] > 0 else 0
    player.minutes_played += data["minutes_played"]
    player.goals += data["goals"]
    player.assists += data["assists"]
    player.historical_performance = round((player.historical_performance * 0.85) + (performance * 0.15), 1)
    match_id = f"MAN-{data['date'].strftime('%Y%m%d')}-{player.id}-{int(np.random.default_rng().integers(100, 999))}"
    session.add(MatchRecord(player_id=player.id, match_id=match_id, performance_score=round(performance, 1), **data))
    session.commit()
    return True, []


def add_nutrition_record(session: Session, player: Player, data: dict) -> tuple[bool, list[str]]:
    errors: list[str] = []
    errors += validate_range("Calories", data["calories"], 0, 7000)
    errors += validate_range("Protein", data["protein_g"], 0, 350)
    errors += validate_range("Carbohydrates", data["carbohydrates_g"], 0, 900)
    errors += validate_range("Fats", data["fats_g"], 0, 260)
    errors += validate_range("Water", data["water_l"], 0, 10)
    errors += validate_range("Meal timing", data["meal_timing_score"], 0, 100)
    if errors:
        return False, errors
    session.add(NutritionRecord(player_id=player.id, **data))
    session.commit()
    return True, []


def update_recovery_record(session: Session, record: RecoveryRecord, data: dict) -> tuple[bool, list[str]]:
    player = session.get(Player, record.player_id)
    if not player:
        return False, ["Player was not found."]
    errors: list[str] = []
    errors += validate_range("Sleep duration", data["sleep_hours"], 0, 14)
    errors += validate_range("Sleep quality", data["sleep_quality"], 0, 100)
    errors += validate_range("HRV", data["hrv"], 20, 130)
    errors += validate_range("Resting heart rate", data["resting_hr"], 30, 110)
    errors += validate_range("Hydration", data["hydration"], 0, 100)
    errors += validate_range("Muscle soreness", data["muscle_soreness"], 0, 100)
    errors += validate_range("Stress", data["stress"], 0, 100)
    errors += validate_range("Mood", data["mood"], 0, 100)
    if errors:
        return False, errors

    recovery_score = calculate_recovery_score(
        sleep_hours=data["sleep_hours"],
        sleep_quality=data["sleep_quality"],
        hrv=data["hrv"],
        resting_hr=data["resting_hr"],
        hydration=data["hydration"],
        muscle_soreness=data["muscle_soreness"],
        stress=data["stress"],
        mood=data["mood"],
        rest_day=data["rest_day"],
    )
    for key, value in data.items():
        setattr(record, key, value)
    record.recovery_score = recovery_score
    latest_training = _latest_training(session, player.id, data["date"])
    if latest_training:
        latest_training.fatigue_score = calculate_fatigue_score(
            latest_training.training_load,
            latest_training.baseline_workload,
            data["sleep_hours"],
            recovery_score,
            data["muscle_soreness"],
            data["hrv"],
        )
        latest_training.injury_risk_pct = estimate_injury_risk(
            player.age,
            player.previous_injuries,
            latest_training.workload_change_pct,
            latest_training.fatigue_score,
            recovery_score,
            data["sleep_hours"],
            latest_training.sprint_distance_m,
            data["muscle_soreness"],
        )
    session.commit()
    generate_alerts(session)
    session.commit()
    return True, []


def add_wellness_checkin(session: Session, player: Player, data: dict) -> tuple[bool, list[str]]:
    errors: list[str] = []
    errors += validate_range("Sleep", data["sleep_hours"], 0, 14)
    errors += validate_range("Sleep quality", data["sleep_quality_10"], 0, 10)
    errors += validate_range("Muscle soreness", data["muscle_soreness_10"], 0, 10)
    errors += validate_range("Fatigue", data["fatigue_10"], 0, 10)
    errors += validate_range("Mood", data["mood_10"], 0, 10)
    errors += validate_range("Stress", data["stress_10"], 0, 10)
    errors += validate_range("Hydration", data["hydration_l"], 0, 10)
    errors += validate_range("RPE", data["rpe"], 0, 10)
    if errors:
        return False, errors

    latest = _latest_recovery(session, player.id, data["date"])
    hrv = latest.hrv if latest else 75.0
    resting_hr = latest.resting_hr if latest else player.resting_hr
    hydration_score = clamp(data["hydration_l"] / 4.0 * 100)
    recovery_payload = {
        "date": data["date"],
        "sleep_hours": data["sleep_hours"],
        "sleep_quality": data["sleep_quality_10"] * 10,
        "hrv": hrv,
        "resting_hr": resting_hr,
        "hydration": hydration_score,
        "muscle_soreness": data["muscle_soreness_10"] * 10,
        "stress": data["stress_10"] * 10,
        "mood": data["mood_10"] * 10,
        "recovery_session": False,
        "rest_day": False,
    }
    session.add(WellnessCheckIn(player_id=player.id, **data))
    session.flush()
    return add_recovery_record(session, player, recovery_payload)


def delete_record(session: Session, record: object) -> None:
    session.delete(record)
    session.commit()
    generate_alerts(session)
    session.commit()
