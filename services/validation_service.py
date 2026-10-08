from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime
import math
import re
import pandas as pd
from services.health_schema import HEALTH_REQUIRED, HEALTH_OPTIONAL, MEDICAL_FIELDS


@dataclass(frozen=True)
class DatasetSchema:
    required: tuple[str, ...]
    optional: tuple[str, ...] = ()
    date_columns: tuple[str, ...] = ()
    numeric_columns: tuple[str, ...] = ()

    @property
    def columns(self):
        return self.required + self.optional


SCHEMAS = {
    "players": DatasetSchema(("player_id", "name", "age", "position"), ("height", "weight"),
                             numeric_columns=("age", "height", "weight")),
    "training": DatasetSchema(("player_id", "date", "duration_min", "rpe", "distance", "sprint_distance", "high_speed_distance"),
                              date_columns=("date",), numeric_columns=("duration_min", "rpe", "distance", "sprint_distance", "high_speed_distance")),
    "recovery": DatasetSchema(("player_id", "date", "sleep_hours", "sleep_quality", "hrv", "resting_hr", "soreness", "stress"),
                              date_columns=("date",), numeric_columns=("sleep_hours", "sleep_quality", "hrv", "resting_hr", "soreness", "stress")),
    "injuries": DatasetSchema(("player_id", "injury_date", "injury_occurred"), ("injury_type", "days_missed"),
                              date_columns=("injury_date",), numeric_columns=("days_missed",)),
    "matches": DatasetSchema(("player_id", "match_date", "minutes_played", "goals", "assists", "shots", "passes_completed", "key_passes", "rating"),
                             date_columns=("match_date",), numeric_columns=("minutes_played", "goals", "assists", "shots", "passes_completed", "key_passes", "rating")),
}
SCHEMAS.update({
    "health": DatasetSchema(("player_id", "date", *HEALTH_REQUIRED), HEALTH_OPTIONAL, ("date",), (*HEALTH_REQUIRED, *HEALTH_OPTIONAL)),
    "medical_tests": DatasetSchema(("player_id", "test_date"), MEDICAL_FIELDS, ("test_date",), MEDICAL_FIELDS),
    "health_events": DatasetSchema(("player_id", "event_date", "health_event"), date_columns=("event_date",)),
})
ALIASES = {
    "player_id": ("athlete id", "player number", "external player id"),
    "name": ("full name", "player name", "athlete name"),
    "age": ("years",), "position": ("role",),
    "height": ("height cm", "height_cm"), "weight": ("body mass", "weight kg"),
    "duration_min": ("duration", "duration minutes", "training duration"),
    "rpe": ("session rpe",), "distance": ("distance km", "distance_km", "total distance"),
    "sprint_distance": ("sprint distance m", "sprint_distance_m"),
    "high_speed_distance": ("high intensity distance", "high_intensity_distance", "high speed running m", "high_speed_running_m"),
    "date": ("session date", "record date"),
    "injury_date": ("date",), "match_date": ("date",),
    "sleep_hours": ("sleep",), "hrv": ("heart rate variability",),
    "resting_hr": ("resting heart rate",), "soreness": ("muscle soreness",),
    "injury_occurred": ("injured", "label"), "days_missed": ("days unavailable",),
    "rating": ("player rating", "match rating"),
    "passes_completed": ("completed passes",), "minutes_played": ("minutes", "mins"),
}
LIMITS = {
    "age": (10, 70), "height": (100, 250), "weight": (25, 200),
    "duration_min": (1, 360), "rpe": (0, 10), "distance": (0, 60),
    "sprint_distance": (0, 60000), "high_speed_distance": (0, 60000),
    "sleep_hours": (0, 24), "sleep_quality": (0, 10), "hrv": (1, 300),
    "resting_hr": (20, 220), "soreness": (0, 10), "stress": (0, 10),
    "days_missed": (0, 3650), "minutes_played": (1, 130), "rating": (0, 10),
    "goals": (0, 30), "assists": (0, 30), "shots": (0, 100),
    "passes_completed": (0, 300), "key_passes": (0, 100),
}
LIMITS.update({
    "fatigue": (0, 10), "energy_level": (0, 10), "hydration_status": (0, 10),
    "body_fat_pct": (0, 100), "blood_pressure_sys": (40, 300), "blood_pressure_dia": (20, 200),
    "oxygen_saturation": (0, 100), "body_temperature": (25, 45),
    **{field: (0, 100000) for field in MEDICAL_FIELDS},
    "hematocrit": (0, 100),
})
INTEGERS = {"age", "days_missed", "minutes_played", "goals", "assists", "shots", "passes_completed", "key_passes"}


def _clean_name(value):
    return re.sub(r"[^a-z0-9]+", " ", str(value).strip().lower()).strip()


def detect_column_mapping(columns, dataset_key):
    source = {_clean_name(column): column for column in columns}
    mapping = {}
    for target in SCHEMAS[dataset_key].columns:
        for candidate in (target, *ALIASES.get(target, ())):
            if _clean_name(candidate) in source:
                mapping[target] = source[_clean_name(candidate)]
                break
    return mapping, [field for field in SCHEMAS[dataset_key].required if field not in mapping]


def detect_dataset(columns):
    for key, marker in (("health", "hydration_status"), ("medical_tests", "test_date"), ("health_events", "health_event")):
        if _clean_name(marker) in {_clean_name(c) for c in columns}:
            return key
    scored = []
    for key, schema in SCHEMAS.items():
        mapping, _ = detect_column_mapping(columns, key)
        scored.append((len(set(mapping) & set(schema.required)) / len(schema.required), key))
    scored.sort(reverse=True)
    return scored[0][1] if scored[0][0] >= 0.6 and scored[0][0] > scored[1][0] else None


def apply_mapping(frame, mapping, dataset_key):
    return pd.DataFrame({target: frame[source] for target, source in mapping.items()
                         if target in SCHEMAS[dataset_key].columns and source in frame}, index=frame.index)


def template_csv(dataset_key):
    return pd.DataFrame(columns=SCHEMAS[dataset_key].columns).to_csv(index=False)


def parse_date(value):
    if isinstance(value, datetime):
        return value.date()
    if isinstance(value, date):
        return value
    text = str(value).strip()
    # ISO dates avoid silently interpreting ambiguous day/month CSV values.
    if not re.fullmatch(r"\d{4}-\d{2}-\d{2}", text):
        raise ValueError("Use YYYY-MM-DD.")
    return date.fromisoformat(text)


def parse_bool(value):
    text = str(value).strip().lower()
    if text in {"1", "true", "yes"}:
        return True
    if text in {"0", "false", "no"}:
        return False
    raise ValueError("Use 0/1, true/false or yes/no.")


def normalize_frame(frame, dataset_key, known_player_ids, existing_keys):
    schema = SCHEMAS[dataset_key]
    problems, rows = [], []
    raw = frame.reset_index(drop=True)
    for field in schema.required:
        if field not in raw:
            problems.append({"row": "-", "field": field, "message": "Required column is missing."})
    if problems:
        return pd.DataFrame(columns=schema.columns), problems
    seen = set()
    for index, row in raw.iterrows():
        normalized = {}
        def issue(field, message):
            problems.append({"row": index + 2, "row_index": index, "field": field, "message": message})
        before = len(problems)
        for field in schema.columns:
            value = row.get(field)
            if pd.isna(value) or (isinstance(value, str) and not value.strip()):
                if field in schema.required:
                    issue(field, "Required value is missing.")
                normalized[field] = None
                continue
            try:
                if field in schema.date_columns:
                    value = parse_date(value)
                    if value > date.today():
                        raise ValueError("Historical dates cannot be in the future.")
                elif field in schema.numeric_columns:
                    value = float(value)
                    low, high = LIMITS[field]
                    if not math.isfinite(value) or not low <= value <= high:
                        raise ValueError(f"Must be between {low} and {high}.")
                    if field in INTEGERS:
                        if not value.is_integer():
                            raise ValueError("Must be a whole number.")
                        value = int(value)
                elif field in ("injury_occurred", "health_event"):
                    value = parse_bool(value)
                else:
                    value = str(value).strip()
                    maximum = {"player_id": 60, "name": 120, "position": 30, "injury_type": 100}[field]
                    if len(value) > maximum:
                        raise ValueError(f"Maximum length is {maximum}.")
                normalized[field] = value
            except (ValueError, TypeError, OverflowError) as exc:
                issue(field, str(exc))
                normalized[field] = None
        player_id = normalized.get("player_id")
        if dataset_key != "players" and player_id and player_id not in known_player_ids:
            issue("player_id", "Unknown player_id. Add the player first.")
        if dataset_key == "training" and all(normalized.get(f) is not None for f in ("distance", "sprint_distance", "high_speed_distance")):
            total = normalized["distance"] * 1000
            if normalized["sprint_distance"] > total or normalized["high_speed_distance"] > total:
                issue("distance", "Sprint and high-speed distances cannot exceed total distance (km converted to m).")
        if dataset_key == "matches" and normalized.get("goals") is not None and normalized.get("shots") is not None:
            if normalized["goals"] > normalized["shots"]:
                issue("goals", "Goals cannot exceed shots.")
        if dataset_key == "health" and all(normalized.get(f) is not None for f in ("blood_pressure_sys", "blood_pressure_dia")):
            if normalized["blood_pressure_sys"] <= normalized["blood_pressure_dia"]:
                issue("blood_pressure_sys", "Systolic pressure must exceed diastolic pressure.")
        key = (player_id,) if dataset_key == "players" else (player_id, normalized.get(schema.date_columns[0]))
        if key in seen or key in existing_keys:
            issue("player_id", "Duplicate player or player/date record.")
        seen.add(key)
        if len(problems) == before:
            normalized["_source_row"] = index + 2
            rows.append(normalized)
    return pd.DataFrame(rows, columns=(*schema.columns, "_source_row")), problems
