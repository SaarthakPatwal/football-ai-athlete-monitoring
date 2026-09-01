from utils.calculations import (
    calculate_fatigue_score,
    calculate_recovery_score,
    calculate_training_load,
    classify_fatigue,
    estimate_injury_risk,
)


def test_training_load_is_duration_times_rpe():
    assert calculate_training_load(75, 6) == 450


def test_recovery_score_stays_in_range():
    score = calculate_recovery_score(
        sleep_hours=7.5,
        sleep_quality=82,
        hrv=75,
        resting_hr=48,
        hydration=84,
        muscle_soreness=25,
        stress=20,
        mood=82,
    )
    assert 0 <= score <= 100
    assert score > 70


def test_fatigue_classification_increases_with_pressure():
    score = calculate_fatigue_score(
        training_load=720,
        baseline_workload=360,
        sleep_hours=5.8,
        recovery_score=52,
        muscle_soreness=76,
        hrv=58,
    )
    assert classify_fatigue(score) == "HIGH"


def test_injury_risk_is_higher_for_poor_readiness():
    low = estimate_injury_risk(23, 0, -5, 30, 85, 8.2, 300, 20)
    high = estimate_injury_risk(31, 3, 35, 78, 52, 5.7, 900, 80)
    assert high > low

