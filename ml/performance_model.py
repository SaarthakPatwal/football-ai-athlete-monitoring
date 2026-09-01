from __future__ import annotations

from utils.calculations import clamp


def predict_performance(features: dict[str, float]) -> dict[str, float]:
    score = clamp(
        features.get("historical_performance", 72)
        + (features.get("recovery_score", 70) - 70) * 0.12
        - (features.get("fatigue_score", 45) - 45) * 0.14
        + (features.get("sleep_hours", 7.5) - 7.5) * 1.6
        - max(features.get("workload_change_pct", 0), 0) * 0.04
    )
    uncertainty = clamp(18 - abs(features.get("historical_performance", 72) - score) * 0.12, 6, 20)
    return {"expected_performance": round(score, 1), "uncertainty": round(uncertainty, 1)}

