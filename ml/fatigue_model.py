from __future__ import annotations

from utils.calculations import calculate_fatigue_score, classify_fatigue


def predict_fatigue(features: dict[str, float]) -> dict[str, float | str]:
    score = calculate_fatigue_score(
        training_load=features["training_load"],
        baseline_workload=features["baseline_workload"],
        sleep_hours=features["sleep_hours"],
        recovery_score=features["recovery_score"],
        muscle_soreness=features["muscle_soreness"],
        hrv=features["hrv"],
        hrv_baseline=features.get("hrv_baseline", 75.0),
    )
    return {"fatigue_score": score, "classification": classify_fatigue(score)}

