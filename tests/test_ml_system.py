"""Isolated test fixtures only; this module is never imported by the application."""
from datetime import date, timedelta
import pandas as pd
import pytest
from sqlalchemy import inspect, select, func
from sqlalchemy.orm import Session
from database.database import get_engine, init_db, DEFAULT_DATABASE_PATH
from database.models import DATASETS, Player, TrainingSession, RecoveryRecord, InjuryHistory, MatchRecord
from services.data_service import import_records, read_dataset, validate_input, dataset_counts
from services.validation_service import template_csv, detect_dataset, detect_column_mapping, apply_mapping
from services.feature_service import History, calculate_training_features
from ml.train import train_model, readiness, temporal_split, load_artifact
from ml.predict import predict


@pytest.fixture
def session():
    engine = get_engine("sqlite:///:memory:")
    init_db(engine)
    with Session(engine) as active:
        yield active
    engine.dispose()


def add_player(session, player_id="001"):
    result = import_records(session, pd.DataFrame([{"player_id": player_id, "name": "Test Player", "age": 24, "position": "CM"}]), "players")
    assert result.ok
    return player_id


def test_fresh_schema_has_only_registered_empty_tables(session):
    assert set(inspect(session.bind).get_table_names()) == {model.__tablename__ for model in DATASETS.values()}
    assert all(count == 0 for count in dataset_counts(session).values())
    assert DEFAULT_DATABASE_PATH.name == "football_ml.db"
    assert all(not status["ready"] for status in readiness(session).values())


def test_legacy_database_rejected():
    engine = get_engine("sqlite:///:memory:")
    with engine.begin() as connection:
        connection.exec_driver_sql("CREATE TABLE players (id INTEGER PRIMARY KEY, name TEXT)")
    with pytest.raises(ValueError, match="Incompatible"):
        init_db(engine)


@pytest.mark.parametrize("key", list(DATASETS))
def test_templates_contain_headers_only(key):
    template = pd.read_csv(__import__("io").StringIO(template_csv(key)))
    assert template.empty
    assert detect_dataset(template.columns) == key


def test_aliases_and_id_preservation(session):
    raw = pd.DataFrame([{"Player Number": "001", "Full Name": "Test", "Years": "24", "Role": "CM"}])
    mapping, missing = detect_column_mapping(raw.columns, "players")
    assert not missing
    result = import_records(session, apply_mapping(raw, mapping, "players"), "players")
    assert result.ok
    assert session.get(Player, "001").height is None


def test_manual_and_csv_use_same_storage_and_validation(session):
    add_player(session)
    record = {"player_id": "001", "date": "2024-01-01", "duration_min": 60, "rpe": 6,
              "distance": 8, "sprint_distance": 200, "high_speed_distance": 700}
    first = import_records(session, pd.DataFrame([record]), "training")
    assert first.ok
    assert read_dataset(session, "training").iloc[0].duration_min == 60
    duplicate = import_records(session, pd.DataFrame([record]), "training")
    assert not duplicate.ok and duplicate.imported_rows == 0
    record["date"] = "2024-01-02"
    record["rpe"] = 11
    assert not import_records(session, pd.DataFrame([record]), "training").ok


def test_unknown_id_invalid_bool_and_future_date_rejected(session):
    frame = pd.DataFrame([{"player_id": "missing", "injury_date": "2099-01-01", "injury_occurred": "maybe"}])
    valid, issues = validate_input(session, frame, "injuries")
    assert valid.empty
    assert {issue["field"] for issue in issues} == {"player_id", "injury_date", "injury_occurred"}


def test_all_or_nothing_and_confirmed_valid_only(session):
    frame = pd.DataFrame([{"player_id": "A", "name": "A", "age": 22, "position": "ST"},
                          {"player_id": "B", "name": "B", "age": "nan", "position": "CM"}])
    assert import_records(session, frame, "players").imported_rows == 0
    assert dataset_counts(session)["players"] == 0
    assert import_records(session, frame, "players", valid_only=True).imported_rows == 1


def test_missing_raw_fields_are_not_defaulted(session):
    add_player(session)
    result = import_records(session, pd.DataFrame([{"player_id": "001", "date": "2024-01-01", "duration_min": 60, "rpe": 6}]), "training")
    assert not result.ok
    assert dataset_counts(session)["training"] == 0


@pytest.mark.parametrize("value", ["inf", "-inf", "NaN", "24.5"])
def test_invalid_age_rejected(session, value):
    assert not import_records(session, pd.DataFrame([{"player_id": "A", "name": "A", "age": value, "position": "ST"}]), "players").ok


def test_rolling_windows_use_calendar_days(session):
    add_player(session)
    rows = [{"player_id": "001", "date": day, "duration_min": 60, "rpe": 6, "distance": 8,
             "sprint_distance": 200, "high_speed_distance": 700}
            for day in (date(2024, 1, 1), date(2024, 1, 29), date(2024, 2, 1))]
    assert import_records(session, pd.DataFrame(rows), "training").ok
    history = History(session)
    player = next(history.frames["players"].itertuples(index=False))
    features = history.snapshot(player, date(2024, 2, 1))
    assert features["workload_7d"] == 360
    assert features["workload_28d"] == 360
    assert features["workload_change_pct"] == 300


def test_no_future_recovery_or_injury_history_in_features(session):
    add_player(session)
    session.add_all([
        RecoveryRecord(player_id="001", date=date(2024, 1, 1), sleep_hours=8, sleep_quality=8, hrv=70, resting_hr=55, soreness=2, stress=2),
        RecoveryRecord(player_id="001", date=date(2024, 1, 3), sleep_hours=1, sleep_quality=1, hrv=20, resting_hr=90, soreness=9, stress=9),
        InjuryHistory(player_id="001", injury_date=date(2024, 1, 3), injury_occurred=True),
    ])
    session.flush()
    history = History(session)
    player = next(history.frames["players"].itertuples(index=False))
    features = history.snapshot(player, date(2024, 1, 3))
    assert features["sleep_hours_7d_mean"] == 8
    assert features["previous_injuries"] == 0


def test_unobserved_injury_windows_are_not_negative_labels(session):
    add_player(session)
    session.add(TrainingSession(player_id="001", date=date(2024, 1, 1), duration_min=60, rpe=6, distance=8, sprint_distance=200, high_speed_distance=700))
    session.flush()
    assert History(session).training_frame("injury").empty
    for day in range(2, 9):
        session.add(InjuryHistory(player_id="001", injury_date=date(2024, 1, day), injury_occurred=False))
    session.flush()
    frame = History(session).training_frame("injury")
    assert len(frame) == 1 and frame.iloc[0].target == 0


def test_target_match_stats_never_enter_own_features(session):
    add_player(session)
    for day, goals, rating in [(1, 1, 6), (8, 9, 10)]:
        session.add(MatchRecord(player_id="001", match_date=date(2024, 1, day), minutes_played=90,
                                goals=goals, assists=0, shots=10, passes_completed=40, key_passes=2, rating=rating))
    session.flush()
    row = History(session).training_frame("performance").iloc[0]
    assert row.target == 10 and row.recent_goals == 1 and row.recent_rating_mean == 6


@pytest.fixture
def historical_session(session):
    # Model smoke tests use disposable fixtures, never the user's database or production artifacts.
    start = date(2024, 1, 1)
    for number in range(3):
        pid = add_player(session, f"T{number}")
        for day in range(180):
            when = start + timedelta(days=day)
            session.add(TrainingSession(player_id=pid, date=when, duration_min=60 + day % 15,
                                        rpe=4 + day % 5, distance=8, sprint_distance=200 + day % 40, high_speed_distance=700))
            session.add(RecoveryRecord(player_id=pid, date=when, sleep_hours=7 + day % 3 / 2,
                                       sleep_quality=7, hrv=65 + day % 20, resting_hr=50 + day % 10, soreness=day % 5, stress=day % 4))
            session.add(InjuryHistory(player_id=pid, injury_date=when, injury_occurred=(day % 19 == 14)))
            if day % 6 == 0:
                session.add(MatchRecord(player_id=pid, match_date=when, minutes_played=90,
                                        goals=day % 2, assists=day % 3, shots=3, passes_completed=40,
                                        key_passes=2, rating=6 + day % 7 / 3))
    session.flush()
    return session


@pytest.mark.parametrize("task", ["injury", "performance"])
def test_real_models_evaluation_persistence_and_predictions(historical_session, tmp_path, monkeypatch, task):
    import ml.train as module
    monkeypatch.setattr(module, "SAVED_MODEL_DIR", tmp_path)
    outcome = train_model(historical_session, task)
    assert outcome.trained, outcome.message
    metadata = outcome.metadata
    assert len(metadata["comparison"]) == 3
    assert metadata["top_model_contributors"]
    assert len(metadata["prediction_examples"]) > 0
    artifact = load_artifact(historical_session, task)
    frame = History(historical_session).training_frame(task)
    train, validation, test = temporal_split(frame)
    assert train.label_end.max() <= validation.date.min()
    assert validation.label_end.max() <= test.date.min()
    current = History(historical_session).prediction_frame(task, date(2024, 6, 29))
    output = predict(historical_session, task, date(2024, 6, 29))
    assert len(output) == 3
    features = metadata["features"]
    assert features == module.INJURY_FEATURES if task == "injury" else features == module.PERFORMANCE_FEATURES
    assert not current.empty
    assert predict(historical_session, task, date(2024, 1, 5)).empty
    assert metadata["test_metrics"]
    if task == "injury":
        assert len(metadata["test_metrics"]["confusion_matrix"]) == 2
        assert output.probability.between(0, 1).all()
    assert artifact["metadata"]["dataset_fingerprint"] == metadata["dataset_fingerprint"]
    # Exercise trained metrics, confusion/importance charts and prediction tables.
    from streamlit.testing.v1 import AppTest
    import views.model_analysis as analysis
    import views.predictions as prediction_view
    monkeypatch.setattr(analysis, "readiness", lambda _: {
        key: {"ready": True, "reasons": [], "missing_fraction": metadata["missing_fraction"],
              "dataset_rows": metadata["dataset_rows"]} for key in ("injury", "performance")})
    monkeypatch.setattr(analysis, "load_artifact", lambda _, key: artifact if key == task else None)
    rendered = AppTest.from_string("from views.model_analysis import render\nrender(None)", default_timeout=30).run()
    assert not rendered.exception, list(rendered.exception)
    monkeypatch.setattr(prediction_view, "load_artifact", lambda _, key: artifact if key == task else None)
    monkeypatch.setattr(prediction_view, "predict", lambda _, key, point=None: output if key == task else pd.DataFrame())
    rendered = AppTest.from_string("from views.predictions import prediction_tables\nprediction_tables(None)", default_timeout=30).run()
    assert not rendered.exception, list(rendered.exception)
    historical_session.add(TrainingSession(player_id="T0", date=date(2024, 6, 29), duration_min=75,
                                           rpe=6, distance=8, sprint_distance=200, high_speed_distance=700))
    historical_session.flush()
    assert load_artifact(historical_session, task) is not None
    assert import_records(historical_session, pd.DataFrame([{"player_id": "NEW", "name": "New Test Player",
                                                           "age": 25, "position": "ST", "height": 180, "weight": 75}]), "players").ok
    assert load_artifact(historical_session, task) is not None
    historical_session.get(Player, "T0").age = 26
    historical_session.flush()
    assert load_artifact(historical_session, task) is None
    assert predict(historical_session, task).empty


def test_no_model_no_prediction(session):
    add_player(session)
    assert predict(session, "injury").empty
    assert predict(session, "performance").empty
    assert not train_model(session, "injury").trained
    assert not train_model(session, "performance").trained


@pytest.mark.parametrize("key,record", [
    ("training", {"player_id": "001", "date": "2024-01-01", "duration_min": "60", "rpe": "6",
                  "distance": "8", "sprint_distance": "200", "high_speed_distance": "700"}),
    ("recovery", {"player_id": "001", "date": "2024-01-01", "sleep_hours": "8", "sleep_quality": "8",
                  "hrv": "70", "resting_hr": "55", "soreness": "2", "stress": "2"}),
    ("injuries", {"player_id": "001", "injury_date": "2024-01-01", "injury_occurred": "0"}),
    ("matches", {"player_id": "001", "match_date": "2024-01-01", "minutes_played": "90", "goals": "1",
                 "assists": "0", "shots": "3", "passes_completed": "40", "key_passes": "2", "rating": "7"}),
])
def test_csv_string_rows_for_every_history_dataset(session, key, record):
    add_player(session)
    import io
    uploaded = pd.read_csv(io.StringIO(pd.DataFrame([record]).to_csv(index=False)), dtype=str, keep_default_na=False)
    mapping, missing = detect_column_mapping(uploaded.columns, key)
    assert not missing
    result = import_records(session, apply_mapping(uploaded, mapping, key), key)
    assert result.ok and result.imported_rows == 1
