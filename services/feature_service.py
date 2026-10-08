from __future__ import annotations

from datetime import date, timedelta
import numpy as np
import pandas as pd
from services.data_service import read_dataset

TRAINING_FEATURES = ["workload_7d", "workload_28d", "workload_change_pct", "sprint_load_7d", "high_speed_load_7d"]
RECOVERY_FIELDS = ["sleep_hours", "sleep_quality", "hrv", "resting_hr", "soreness", "stress"]
RECOVERY_FEATURES = [field + "_7d_mean" for field in RECOVERY_FIELDS]
PERFORMANCE_HISTORY = ["recent_rating_mean", "rating_trend", "recent_minutes", "recent_goals", "recent_assists", "rating_consistency"]
INJURY_FEATURES = ["age", "position", *TRAINING_FEATURES, *RECOVERY_FEATURES, "previous_injuries"]
PERFORMANCE_FEATURES = ["age", "position", *PERFORMANCE_HISTORY, *TRAINING_FEATURES, *RECOVERY_FEATURES]
FEATURE_VERSION = 1


def calculate_training_load(duration_min, rpe):
    return duration_min * rpe


def calculate_training_features(training, point):
    recent = training[(training.date < point) & (training.date >= point - timedelta(days=7))]
    baseline = training[(training.date < point) & (training.date >= point - timedelta(days=28))]
    def load(frame):
        return float(calculate_training_load(frame.duration_min, frame.rpe).sum()) if not frame.empty else np.nan
    seven, twenty_eight = load(recent), load(baseline)
    # Compare seven-day totals to a seven-day equivalent of the 28-day baseline.
    # Before 28 calendar days of history, the baseline change is unknown.
    full_window = not training.empty and training.date.min() <= point - timedelta(days=28)
    change = (seven / (twenty_eight / 4) - 1) * 100 if full_window and twenty_eight > 0 else np.nan
    return {"workload_7d": seven, "workload_28d": twenty_eight, "workload_change_pct": change,
            "sprint_load_7d": float(recent.sprint_distance.sum()) if not recent.empty else np.nan,
            "high_speed_load_7d": float(recent.high_speed_distance.sum()) if not recent.empty else np.nan}


def calculate_recovery_features(recovery, point):
    recent = recovery[(recovery.date < point) & (recovery.date >= point - timedelta(days=7))]
    return {field + "_7d_mean": float(recent[field].mean()) if not recent.empty else np.nan
            for field in RECOVERY_FIELDS}


def calculate_performance_features(matches, point):
    recent = matches[matches.match_date < point].sort_values("match_date").tail(5)
    if recent.empty:
        return dict.fromkeys(PERFORMANCE_HISTORY, np.nan)
    ratings = recent.rating.to_numpy(dtype=float)
    return {"recent_rating_mean": float(ratings.mean()),
            "rating_trend": float(np.polyfit(np.arange(len(ratings)), ratings, 1)[0]) if len(ratings) >= 2 else np.nan,
            "recent_minutes": float(recent.minutes_played.sum()),
            "recent_goals": float(recent.goals.sum()), "recent_assists": float(recent.assists.sum()),
            "rating_consistency": float(ratings.std(ddof=0)) if len(ratings) >= 2 else np.nan}


class History:
    def __init__(self, session):
        self.frames = {key: read_dataset(session, key) for key in ("players", "training", "recovery", "injuries", "matches")}
        self.grouped = {key: {player_id: frame.reset_index(drop=True) for player_id, frame in values.groupby("player_id")}
                        for key, values in self.frames.items() if key != "players"}

    def records(self, key, player_id):
        return self.grouped[key].get(player_id, self.frames[key].iloc[:0])

    def snapshot(self, player, point):
        # All features use strictly earlier calendar dates; same-day ordering is unknown.
        training = self.records("training", player.player_id)
        training = training[training.date < point]
        recovery = self.records("recovery", player.player_id)
        matches = self.records("matches", player.player_id)
        injuries = self.records("injuries", player.player_id)
        prior = injuries[(injuries.injury_date < point) & (injuries.injury_occurred == True)]
        return {"age": player.age, "position": player.position,
                **calculate_training_features(training, point),
                **calculate_recovery_features(recovery, point),
                **calculate_performance_features(matches, point),
                "previous_injuries": len(prior)}

    def training_frame(self, task):
        rows = []
        for player in self.frames["players"].itertuples(index=False):
            training = self.records("training", player.player_id)
            injuries = self.records("injuries", player.player_id)
            matches = self.records("matches", player.player_id).sort_values("match_date")
            if task == "injury":
                for recorded in training.date:
                    # Prediction at midnight after the recorded session, covering the next seven dates.
                    point = recorded + timedelta(days=1)
                    end = point + timedelta(days=7)
                    if ((injuries.injury_date == recorded) & injuries.injury_occurred).any():
                        continue
                    future = injuries[(injuries.injury_date >= point) & (injuries.injury_date < end)]
                    positive = bool(future.injury_occurred.any())
                    observed = set(future.injury_date)
                    # Silence in an injury-event log is NOT proof of an injury-free week.
                    if not positive and not all(point + timedelta(days=i) in observed for i in range(7)):
                        continue
                    rows.append({"player_id": player.player_id, "date": point, "label_end": end,
                                 "target": int(positive), **self.snapshot(player, point)})
            else:
                for match in matches.itertuples(index=False):
                    if not (matches.match_date < match.match_date).any():
                        continue
                    point = match.match_date
                    rows.append({"player_id": player.player_id, "date": point,
                                 "label_end": point + timedelta(days=1), "target": match.rating,
                                 **self.snapshot(player, point)})
        features = INJURY_FEATURES if task == "injury" else PERFORMANCE_FEATURES
        return pd.DataFrame(rows, columns=["player_id", "date", "label_end", "target", *features]).sort_values(["date", "player_id"]).reset_index(drop=True)

    def prediction_frame(self, task, point=None):
        point = point or date.today() + timedelta(days=1)
        rows = []
        for player in self.frames["players"].itertuples(index=False):
            features = self.snapshot(player, point)
            if pd.isna(features["workload_7d"]) or pd.isna(features["sleep_hours_7d_mean"]):
                continue
            if task == "performance" and pd.isna(features["recent_rating_mean"]):
                continue
            rows.append({"player_id": player.player_id, "name": player.name, "as_of": point, **features})
        return pd.DataFrame(rows)


def build_injury_training_frame(session):
    return History(session).training_frame("injury")


def build_performance_training_frame(session):
    return History(session).training_frame("performance")
