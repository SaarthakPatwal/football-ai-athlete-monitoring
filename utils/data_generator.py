from __future__ import annotations

from collections import defaultdict
from datetime import date, timedelta

import numpy as np

from utils.calculations import (
    calculate_fatigue_score,
    calculate_recovery_score,
    calculate_training_load,
    clamp,
    estimate_injury_risk,
)


FIRST_NAMES = [
    "Adam", "Bruno", "Callum", "Diego", "Elias", "Fabian", "Gabriel", "Hugo", "Isaac",
    "Jonas", "Kai", "Luca", "Mateo", "Nico", "Oscar", "Pedro", "Rafael", "Samir",
    "Theo", "Victor", "Yusuf", "Marco", "Julian", "Andre", "Leo",
]
LAST_NAMES = [
    "Carter", "Silva", "Reed", "Morgan", "Khan", "Novak", "Torres", "Bennett", "Rossi",
    "Diallo", "Meyer", "Costa", "Hughes", "Ndiaye", "Fischer", "Alvarez", "Okafor",
    "Santos", "Wilson", "Mendes", "Ibrahim", "Clark", "Lopez", "Murphy", "Fernandes",
]
NATIONALITIES = ["England", "Spain", "Portugal", "France", "Germany", "Brazil", "Netherlands", "USA", "Senegal", "Italy"]
POSITIONS = ["GK", "RB", "CB", "CB", "LB", "DM", "CM", "CM", "AM", "RW", "LW", "ST"]
SESSION_TYPES = ["Tactical", "Strength", "Recovery", "Conditioning", "Match Prep", "Small-Sided Games"]
OPPONENTS = ["Northbridge FC", "Riverside United", "East City", "Harbor Athletic", "Forest Town", "Metro FC"]


def _normal(rng: np.random.Generator, mean: float, std: float, low: float, high: float) -> float:
    return round(float(np.clip(rng.normal(mean, std), low, high)), 1)


def _position_profile(position: str) -> dict[str, float]:
    if position == "GK":
        return {"pace": 55, "shooting": 35, "tackling": 45, "passing": 74, "height": 190, "weight": 84}
    if position in {"CB", "RB", "LB"}:
        return {"pace": 72, "shooting": 45, "tackling": 78, "passing": 70, "height": 184, "weight": 78}
    if position in {"DM", "CM", "AM"}:
        return {"pace": 75, "shooting": 68, "tackling": 68, "passing": 80, "height": 179, "weight": 73}
    return {"pace": 84, "shooting": 78, "tackling": 45, "passing": 73, "height": 181, "weight": 75}


def generate_demo_data(player_count: int = 25, days: int = 365, seed: int = 42) -> dict[str, list[dict]]:
    rng = np.random.default_rng(seed)
    end_date = date.today()
    start_date = end_date - timedelta(days=days - 1)
    positions = [POSITIONS[i % len(POSITIONS)] for i in range(player_count)]
    rng.shuffle(positions)

    players: list[dict] = []
    training_sessions: list[dict] = []
    recovery_records: list[dict] = []
    nutrition_records: list[dict] = []
    match_records: list[dict] = []
    injury_history: list[dict] = []

    cumulative_load: dict[int, list[float]] = defaultdict(list)
    latest_totals: dict[int, dict[str, int]] = defaultdict(lambda: {"matches": 0, "minutes": 0, "goals": 0, "assists": 0})
    hrv_baselines: dict[int, float] = {}

    for index in range(player_count):
        player_id = index + 1
        position = positions[index]
        profile = _position_profile(position)
        age = int(rng.integers(18, 34))
        previous_injuries = int(rng.poisson(0.8 if age < 28 else 1.3))
        hrv_baselines[player_id] = _normal(rng, 76 - previous_injuries * 1.5, 7, 52, 95)

        player = {
            "id": player_id,
            "name": f"{FIRST_NAMES[index % len(FIRST_NAMES)]} {LAST_NAMES[(index * 3) % len(LAST_NAMES)]}",
            "age": age,
            "position": position,
            "jersey_number": index + 1,
            "height_cm": _normal(rng, profile["height"], 5, 168, 202),
            "weight_kg": _normal(rng, profile["weight"], 5, 62, 95),
            "preferred_foot": rng.choice(["Right", "Left", "Both"], p=[0.62, 0.28, 0.10]).item(),
            "nationality": rng.choice(NATIONALITIES).item(),
            "squad_status": rng.choice(["Active", "Active", "Active", "Managed Load"]).item(),
            "sprint_speed": _normal(rng, profile["pace"] / 10 + 25, 1.2, 25, 36),
            "acceleration": _normal(rng, profile["pace"], 7, 45, 96),
            "vo2_max": _normal(rng, 58, 5, 45, 72),
            "resting_hr": _normal(rng, 48, 5, 38, 62),
            "max_hr": _normal(rng, 195 - (age * 0.35), 5, 176, 204),
            "body_fat_pct": _normal(rng, 10.5, 2.3, 6, 18),
            "strength": _normal(rng, 73, 8, 45, 95),
            "agility": _normal(rng, profile["pace"], 8, 45, 96),
            "passing": _normal(rng, profile["passing"], 8, 35, 96),
            "shooting": _normal(rng, profile["shooting"], 10, 25, 96),
            "dribbling": _normal(rng, (profile["pace"] + profile["passing"]) / 2, 8, 35, 96),
            "tackling": _normal(rng, profile["tackling"], 8, 25, 96),
            "crossing": _normal(rng, profile["passing"] - (5 if position == "CB" else 0), 9, 30, 94),
            "positioning": _normal(rng, 75, 8, 45, 96),
            "vision": _normal(rng, profile["passing"], 8, 35, 96),
            "decision_making": _normal(rng, 74, 7, 45, 96),
            "pace": _normal(rng, profile["pace"], 8, 45, 97),
            "matches_played": 0,
            "minutes_played": 0,
            "goals": 0,
            "assists": 0,
            "previous_injuries": previous_injuries,
            "historical_performance": _normal(rng, 72, 7, 50, 92),
            "historical_workload": _normal(rng, 420, 60, 260, 600),
        }
        players.append(player)

        if previous_injuries:
            for injury_idx in range(min(previous_injuries, 3)):
                injury_history.append({
                    "player_id": player_id,
                    "date": start_date + timedelta(days=int(rng.integers(1, max(days - 30, 2)))),
                    "injury_type": rng.choice(["Hamstring", "Ankle", "Groin", "Knee", "Calf"]).item(),
                    "severity": rng.choice(["Minor", "Moderate", "Major"], p=[0.6, 0.32, 0.08]).item(),
                    "days_missed": int(rng.integers(5, 45)),
                })

    for offset in range(days):
        current_date = start_date + timedelta(days=offset)
        weekday = current_date.weekday()
        match_day = weekday == 5 and offset > 14 and offset % 7 == 0

        for player in players:
            player_id = player["id"]
            is_rest_day = weekday == 6 or rng.random() < 0.08
            load_history = cumulative_load[player_id]
            baseline = float(np.mean(load_history[-28:])) if load_history else player["historical_workload"]

            if is_rest_day:
                duration = float(rng.integers(20, 45))
                rpe = _normal(rng, 2.2, 0.6, 1, 4)
                session_type = "Recovery"
            elif match_day:
                duration = float(rng.integers(35, 60))
                rpe = _normal(rng, 4.5, 0.8, 2.5, 7)
                session_type = "Match Prep"
            else:
                duration = float(rng.integers(55, 105))
                rpe = _normal(rng, 5.9, 1.3, 3, 9.5)
                session_type = rng.choice(SESSION_TYPES).item()

            training_load = calculate_training_load(duration, rpe)
            recent_7 = float(np.sum(load_history[-6:] + [training_load]))
            recent_28 = float(np.sum(load_history[-27:] + [training_load]))
            acute_workload = recent_7 / 7
            baseline_workload = max(recent_28 / min(28, len(load_history) + 1), 1)
            workload_change = ((acute_workload - baseline_workload) / baseline_workload) * 100

            sleep_hours = _normal(rng, 7.6 - max(workload_change, 0) * 0.01, 0.8, 4.8, 9.5)
            sleep_quality = _normal(rng, 78 - max(workload_change, 0) * 0.11, 9, 40, 96)
            soreness = _normal(rng, 32 + training_load / 28 + max(workload_change, 0) * 0.12, 14, 5, 95)
            hrv = _normal(rng, hrv_baselines[player_id] - max(workload_change, 0) * 0.06 - soreness * 0.04, 5, 45, 95)
            resting_hr = _normal(rng, player["resting_hr"] + max(workload_change, 0) * 0.03 + soreness * 0.02, 4, 38, 72)
            hydration = _normal(rng, 82 - soreness * 0.05, 7, 50, 98)
            stress = _normal(rng, 28 + max(workload_change, 0) * 0.09, 12, 4, 90)
            mood = _normal(rng, 78 - stress * 0.18, 9, 35, 98)
            recovery_score = calculate_recovery_score(
                sleep_hours, sleep_quality, hrv, resting_hr, hydration, soreness, stress, mood, is_rest_day
            )
            fatigue_score = calculate_fatigue_score(
                training_load, baseline_workload, sleep_hours, recovery_score, soreness, hrv, hrv_baselines[player_id]
            )
            risk_pct = estimate_injury_risk(
                player["age"], player["previous_injuries"], workload_change, fatigue_score,
                recovery_score, sleep_hours, sprint_distance_m=max(training_load * 1.15, 80), soreness=soreness
            )
            fitness_score = clamp(78 + np.mean(load_history[-21:] or [training_load]) / 35 - fatigue_score * 0.12 + rng.normal(0, 4))

            training_sessions.append({
                "player_id": player_id,
                "date": current_date,
                "session_type": session_type,
                "duration_min": round(duration, 1),
                "intensity": round(rpe * 10, 1),
                "rpe": rpe,
                "distance_km": _normal(rng, duration / 11, 1.2, 1.0, 13.5),
                "sprint_distance_m": _normal(rng, training_load * 1.1, 90, 40, 1150),
                "high_speed_running_m": _normal(rng, training_load * 1.8, 140, 80, 1800),
                "accelerations": int(np.clip(rng.normal(training_load / 18, 8), 4, 85)),
                "decelerations": int(np.clip(rng.normal(training_load / 20, 7), 3, 80)),
                "average_hr": _normal(rng, 120 + rpe * 8, 8, 95, 182),
                "max_hr": _normal(rng, 150 + rpe * 6, 8, 125, 204),
                "training_load": training_load,
                "acute_workload": round(acute_workload, 1),
                "baseline_workload": round(baseline_workload, 1),
                "workload_change_pct": round(workload_change, 1),
                "fatigue_score": fatigue_score,
                "fitness_score": round(fitness_score, 1),
                "injury_risk_pct": risk_pct,
            })
            cumulative_load[player_id].append(training_load)

            recovery_records.append({
                "player_id": player_id,
                "date": current_date,
                "sleep_hours": sleep_hours,
                "sleep_quality": sleep_quality,
                "hrv": hrv,
                "resting_hr": resting_hr,
                "hydration": hydration,
                "muscle_soreness": soreness,
                "stress": stress,
                "mood": mood,
                "recovery_session": bool(session_type == "Recovery"),
                "rest_day": bool(is_rest_day),
                "recovery_score": recovery_score,
            })

            nutrition_records.append({
                "player_id": player_id,
                "date": current_date,
                "calories": _normal(rng, 3300 + training_load * 0.9, 260, 2200, 4700),
                "protein_g": _normal(rng, player["weight_kg"] * 2.0, 18, 95, 230),
                "carbohydrates_g": _normal(rng, 390 + training_load * 0.25, 60, 180, 680),
                "fats_g": _normal(rng, 92, 16, 45, 155),
                "water_l": _normal(rng, 3.5 + training_load / 900, 0.5, 1.8, 6.5),
                "meal_timing_score": _normal(rng, 78, 10, 35, 98),
            })

        if match_day:
            match_number = offset // 7
            opponent = OPPONENTS[match_number % len(OPPONENTS)]
            selected_players = rng.choice([p["id"] for p in players], size=16, replace=False)
            for player_id in selected_players:
                player = players[player_id - 1]
                position = player["position"]
                minutes = int(rng.choice([18, 25, 35, 60, 72, 84, 90], p=[0.08, 0.08, 0.1, 0.14, 0.2, 0.15, 0.25]))
                attacking_bias = 1.4 if position in {"ST", "RW", "LW", "AM"} else 0.45 if position != "GK" else 0.05
                goals = int(rng.poisson(0.16 * attacking_bias))
                assists = int(rng.poisson(0.13 * attacking_bias))
                pass_accuracy = _normal(rng, player["passing"], 6, 55, 96)
                player_rating = _normal(
                    rng,
                    6.4 + goals * 0.8 + assists * 0.45 + (pass_accuracy - 75) * 0.015,
                    0.45,
                    4.8,
                    9.8,
                )
                performance_score = clamp(player_rating * 10 + goals * 2 + assists * 1.5 + rng.normal(0, 2), 35, 100)
                match_records.append({
                    "player_id": player_id,
                    "match_id": f"M{match_number:03d}",
                    "opponent": opponent,
                    "result": rng.choice(["Win", "Draw", "Loss"], p=[0.48, 0.24, 0.28]).item(),
                    "date": current_date,
                    "minutes_played": minutes,
                    "goals": goals,
                    "assists": assists,
                    "shots": int(rng.poisson(2.0 * attacking_bias)),
                    "shots_on_target": int(rng.poisson(0.9 * attacking_bias)),
                    "passes": int(np.clip(rng.normal(46 if position != "GK" else 30, 18), 4, 110)),
                    "pass_accuracy": pass_accuracy,
                    "key_passes": int(rng.poisson(1.2 * attacking_bias)),
                    "tackles": int(rng.poisson(3.2 if position in {"CB", "RB", "LB", "DM"} else 1.3)),
                    "interceptions": int(rng.poisson(2.6 if position in {"CB", "RB", "LB", "DM"} else 1.1)),
                    "duels_won": int(rng.poisson(5.2 if position in {"CB", "ST"} else 3.0)),
                    "distance_km": _normal(rng, minutes / 9.2, 0.8, 1.5, 12.8),
                    "sprint_distance_m": _normal(rng, minutes * (7.4 if position in {"RW", "LW", "ST", "RB", "LB"} else 4.8), 90, 40, 980),
                    "high_speed_running_m": _normal(rng, minutes * 12, 150, 80, 1600),
                    "progressive_passes": int(rng.poisson(4.0 if position in {"DM", "CM", "AM", "RB", "LB"} else 1.5)),
                    "player_rating": player_rating,
                    "performance_score": round(performance_score, 1),
                })
                latest_totals[player_id]["matches"] += 1
                latest_totals[player_id]["minutes"] += minutes
                latest_totals[player_id]["goals"] += goals
                latest_totals[player_id]["assists"] += assists

    for player in players:
        totals = latest_totals[player["id"]]
        player["matches_played"] = totals["matches"]
        player["minutes_played"] = totals["minutes"]
        player["goals"] = totals["goals"]
        player["assists"] = totals["assists"]
        player["historical_workload"] = round(float(np.mean(cumulative_load[player["id"]][-90:])), 1)

    return {
        "players": players,
        "training_sessions": training_sessions,
        "recovery_records": recovery_records,
        "nutrition_records": nutrition_records,
        "match_records": match_records,
        "injury_history": injury_history,
    }
