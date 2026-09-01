from __future__ import annotations

from dataclasses import dataclass


def clamp(value: float, low: float = 0.0, high: float = 100.0) -> float:
    return max(low, min(high, float(value)))


def calculate_training_load(duration_min: float, rpe: float) -> float:
    return round(max(duration_min, 0) * max(rpe, 0), 2)


def calculate_recovery_score(
    sleep_hours: float,
    sleep_quality: float,
    hrv: float,
    resting_hr: float,
    hydration: float,
    muscle_soreness: float,
    stress: float,
    mood: float,
    rest_day: bool = False,
) -> float:
    sleep_component = clamp((sleep_hours / 8.5) * 100) * 0.16 + clamp(sleep_quality) * 0.14
    hrv_component = clamp((hrv / 90) * 100) * 0.18
    heart_rate_component = clamp(100 - max(resting_hr - 45, 0) * 2.0) * 0.12
    hydration_component = clamp(hydration) * 0.13
    soreness_component = clamp(100 - muscle_soreness) * 0.12
    stress_component = clamp(100 - stress) * 0.08
    mood_component = clamp(mood) * 0.05
    rest_component = 2.0 if rest_day else 0.0
    return round(clamp(
        sleep_component
        + hrv_component
        + heart_rate_component
        + hydration_component
        + soreness_component
        + stress_component
        + mood_component
        + rest_component
    ), 1)


def calculate_fatigue_score(
    training_load: float,
    baseline_workload: float,
    sleep_hours: float,
    recovery_score: float,
    muscle_soreness: float,
    hrv: float,
    hrv_baseline: float = 75.0,
) -> float:
    load_pressure = clamp((training_load / max(baseline_workload, 1)) * 55, 0, 85)
    sleep_pressure = clamp((8 - sleep_hours) * 9, 0, 35)
    recovery_pressure = clamp(100 - recovery_score) * 0.32
    soreness_pressure = clamp(muscle_soreness) * 0.22
    hrv_pressure = clamp((hrv_baseline - hrv) * 1.2, 0, 25)
    return round(clamp(load_pressure + sleep_pressure + recovery_pressure + soreness_pressure + hrv_pressure), 1)


def classify_fatigue(score: float) -> str:
    if score >= 70:
        return "HIGH"
    if score >= 45:
        return "MEDIUM"
    return "LOW"


def classify_risk(risk_pct: float) -> str:
    if risk_pct >= 70:
        return "HIGH"
    if risk_pct >= 40:
        return "MEDIUM"
    return "LOW"


def estimate_injury_risk(
    age: int,
    previous_injuries: int,
    workload_change_pct: float,
    fatigue_score: float,
    recovery_score: float,
    sleep_hours: float,
    sprint_distance_m: float,
    soreness: float,
) -> float:
    risk = 8.0
    risk += max(age - 27, 0) * 1.1
    risk += min(previous_injuries, 5) * 5.5
    risk += max(workload_change_pct, 0) * 0.34
    risk += fatigue_score * 0.28
    risk += max(70 - recovery_score, 0) * 0.35
    risk += max(7.2 - sleep_hours, 0) * 4.2
    risk += max(sprint_distance_m - 600, 0) * 0.018
    risk += soreness * 0.14
    return round(clamp(risk), 1)


@dataclass(frozen=True)
class RiskContribution:
    factor: str
    impact_pct: float
    reason: str


def explain_injury_risk(
    previous_injuries: int,
    workload_change_pct: float,
    fatigue_score: float,
    recovery_score: float,
    sleep_hours: float,
    sprint_distance_m: float,
    soreness: float,
) -> list[RiskContribution]:
    contributions = [
        RiskContribution("Workload change", round(max(workload_change_pct, 0) * 0.34, 1), "Recent load is above baseline."),
        RiskContribution("Fatigue", round(fatigue_score * 0.28, 1), "Fatigue score is contributing to readiness risk."),
        RiskContribution("Recovery", round(max(70 - recovery_score, 0) * 0.35, 1), "Recovery is below the preferred operating range."),
        RiskContribution("Sleep", round(max(7.2 - sleep_hours, 0) * 4.2, 1), "Sleep duration is below target."),
        RiskContribution("Sprint load", round(max(sprint_distance_m - 600, 0) * 0.018, 1), "High-speed exposure is elevated."),
        RiskContribution("Soreness", round(soreness * 0.14, 1), "Self-reported soreness adds load-management concern."),
        RiskContribution("Previous injuries", round(min(previous_injuries, 5) * 5.5, 1), "Historical injury count increases the estimate."),
    ]
    return [item for item in sorted(contributions, key=lambda c: c.impact_pct, reverse=True) if item.impact_pct > 0][:5]

