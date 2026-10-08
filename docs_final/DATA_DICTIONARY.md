# Data dictionary — exact current CSV headers

Every CSV has one row per player/date, except `players.csv`, which has one row per player. Import Players first. Dates are `YYYY-MM-DD` and may not be in the future. IDs are text (leading zeroes are preserved). Numeric values must be finite and within the application's input bounds. Empty required cells fail validation; empty optional cells become NULL. Bounds are input checks, not medical risk thresholds. Units below are the conventions used by this demo; the app does not convert units.

| File | Required columns, in file order | Optional columns, in file order |
| --- | --- | --- |
| `players.csv` | `player_id,name,age,position` | `height,weight` |
| `training.csv` | `player_id,date,duration_min,rpe,distance,sprint_distance,high_speed_distance` | none |
| `recovery.csv` | `player_id,date,sleep_hours,sleep_quality,hrv,resting_hr,soreness,stress` | none |
| `injuries.csv` | `player_id,injury_date,injury_occurred` | `injury_type,days_missed` |
| `matches.csv` | `player_id,match_date,minutes_played,goals,assists,shots,passes_completed,key_passes,rating` | none |
| `health.csv` | `player_id,date,resting_hr,hrv,sleep_hours,sleep_quality,soreness,fatigue,stress,energy_level,hydration_status` | `weight,body_fat_pct,blood_pressure_sys,blood_pressure_dia,oxygen_saturation,body_temperature` |
| `medical_tests.csv` | `player_id,test_date` | `hemoglobin,hematocrit,wbc_count,platelet_count,ferritin,serum_iron,vitamin_d,vitamin_b12,glucose,creatinine,crp` |
| `health_events.csv` | `player_id,event_date,health_event` | none |

## Field meanings and input bounds

**Players:** `player_id` is a unique string of at most 60 characters; `name` is a display name (at most 120 characters); `age` is an integer 10–70; `position` is a role string of at most 30 characters. Optional `height` is 100–250 cm and `weight` is 25–200 kg.

**Training:** `date` is the session day. `duration_min` is 1–360 minutes; `rpe` is 0–10 perceived exertion; `distance` is 0–60 km; `sprint_distance` and `high_speed_distance` are 0–60,000 m each, and neither may exceed total distance converted to metres. Each row represents the recorded daily total. No row is automatically interpreted as a rest day.

**Recovery:** `sleep_hours` is 0–24 hours; `sleep_quality` is 0–10; `hrv` is 1–300 ms; `resting_hr` is 20–220 bpm; `soreness` and `stress` are 0–10 reported scores.

**Injuries:** `injury_date` is the observation day. `injury_occurred` accepts `1/0`, `true/false` or `yes/no`: 1 records a new onset and 0 explicitly confirms no new onset. `injury_type` is optional text of at most 100 characters; `days_missed` is an optional integer 0–3,650. Missing days are unknown, never confirmed zeros.

**Matches:** `match_date` is the appearance date; `minutes_played` is integer 1–130; `goals` and `assists` integer 0–30; `shots` integer 0–100; `passes_completed` integer 0–300; `key_passes` integer 0–100; `rating` 0–10. Goals may not exceed shots. Match rating is the Performance target for that row and prior-match history for later rows.

**Health:** `date` is the daily observation day. `resting_hr` is 20–220 bpm, `hrv` 1–300 ms, `sleep_hours` 0–24 hours; `sleep_quality`, `soreness`, `fatigue`, `stress`, `energy_level`, and `hydration_status` are each 0–10 scores. Optional `weight` is 25–200 kg; `body_fat_pct` 0–100%; `blood_pressure_sys` 40–300 mmHg; `blood_pressure_dia` 20–200 mmHg; `oxygen_saturation` 0–100%; `body_temperature` 25–45 °C. If both pressures are given, systolic must exceed diastolic.

**Medical tests:** `test_date` should be when the result was available. All test values are optional. `hemoglobin` is g/dL; `hematocrit` %; `wbc_count` and `platelet_count` 10⁹/L; `ferritin` ng/mL; `serum_iron` µg/dL; `vitamin_d` ng/mL; `vitamin_b12` pg/mL; `glucose` and `creatinine` mg/dL; `crp` mg/L. Hematocrit accepts 0–100; other laboratory inputs accept 0–100,000. These broad software bounds are not medical reference intervals. A partial or blank panel is accepted; combine same-day panels for one player before import.

**Health events:** `event_date` is a daily outcome observation. `health_event` accepts the same Boolean forms as `injury_occurred`: 1 is a documented new health-related event and 0 explicitly confirms no new event. This is a separate label source for Health Monitoring. The fictional CSV provides authored scenario events; it does not derive labels from HRV, sleep or another measurement.

The three outcome fields (`injury_occurred`, `rating`, `health_event`) have different meanings. See [FEATURE_ENGINEERING.md](FEATURE_ENGINEERING.md) for how each becomes a model target.
