from __future__ import annotations

import pandas as pd


INJURY_RISK_FEATURES = [
    "age",
    "previous_injuries",
    "workload_change_pct",
    "fatigue_score",
    "recovery_score",
    "sleep_hours",
    "sprint_distance_m",
    "muscle_soreness",
]


PERFORMANCE_FEATURES = [
    "historical_performance",
    "training_load",
    "recovery_score",
    "fatigue_score",
    "sleep_hours",
    "minutes_played",
    "position",
]


def ensure_feature_columns(df: pd.DataFrame, columns: list[str]) -> pd.DataFrame:
    missing = [column for column in columns if column not in df.columns]
    if missing:
        raise ValueError(f"Missing feature columns: {', '.join(missing)}")
    return df[columns].copy()

