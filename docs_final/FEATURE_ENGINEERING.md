# Feature engineering and target construction

For prediction date `D`, all model features use records dated **strictly before D**. Date-only input cannot establish same-day order, so same-day measurements are excluded. Missing features remain missing until the saved preprocessing pipeline handles them.

## Injury and Performance features

Training load for each recorded day is `duration_min × rpe`. `workload_7d` and `workload_28d` sum this load over `[D−7,D)` and `[D−28,D)`. `workload_change_pct = (workload_7d / (workload_28d / 4) − 1) × 100`, only when there are at least 28 calendar days of recorded history and the baseline is positive. `sprint_load_7d` and `high_speed_load_7d` sum their respective distances over `[D−7,D)`. Unrecorded days contribute no session row; the app does not establish whether they were rest days.

For each of `sleep_hours,sleep_quality,hrv,resting_hr,soreness,stress`, the corresponding `*_7d_mean` is the arithmetic mean of Recovery records in `[D−7,D)`. Injury also uses `previous_injuries`, the count of recorded positive injury onsets before D. Both tasks use recorded `age` and `position` as static profile fields.

Performance adds the latest five earlier matches: `recent_rating_mean` is their mean rating; `rating_trend` is the least-squares slope across match order (requires two matches); `recent_minutes`, `recent_goals`, and `recent_assists` are their sums; `rating_consistency` is the population standard deviation of ratings (requires two). These are all missing when there is no prior match.

An Injury training sample is anchored at the day after a recorded training session. It excludes a training day with an injury onset. The target is 1 if a new injury onset is recorded on any of D through D+6. It is 0 only if all seven daily outcome observations are present and none is positive; otherwise the sample is omitted. A Performance sample is a match after that player's first match: the match's actual rating is the target and that match's own statistics are excluded from features.

## Health features and target

For each of the nine required daily Health measurements (`resting_hr,hrv,sleep_hours,sleep_quality,soreness,fatigue,stress,energy_level,hydration_status`), compute `*_7d_mean` from `[D−7,D)`, `*_trend` as the least-squares slope per calendar day, and `*_change` as the last minus first value in that window. Slope and change require at least two observations. The six optional daily fields use `latest_*` from that same window.

For every medical analyte in `medical_tests.csv`, `latest_*` is the last non-null result dated before D; `change_*` subtracts the previous non-null result from the latest; `days_since_*` is calendar days since that last measured result. A blank panel does not erase an earlier result. `health_observations_7d` counts recent daily records and `days_since_health` dates the most recent earlier one. The Health feature vector has 68 numeric fields. At least one Health record in the prior seven days is required for prediction; medical records are optional.

A Health training sample is anchored at the day after a Health record. Its target is a documented Health event in `[D,D+7)`. One positive event is sufficient for a positive sample. A negative needs explicit zeros on all seven dates; missing follow-up is unknown. Health outcomes never enter the feature vector. See [HEALTH_MODULE.md](HEALTH_MODULE.md) for clinical scope and interpretation.
