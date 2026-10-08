from datetime import date
from pathlib import Path
import pytest
from sqlalchemy.orm import sessionmaker
from streamlit.testing.v1 import AppTest
from database.database import get_engine, init_db
from services.data_service import dataset_counts


@pytest.fixture
def app(monkeypatch):
    import database.database as database
    engine = get_engine("sqlite:///:memory:")
    # AppTest runs in a script thread; share the same in-memory connection.
    from sqlalchemy import create_engine
    from sqlalchemy.pool import StaticPool
    engine.dispose()
    engine = create_engine("sqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool)
    init_db(engine)
    monkeypatch.setattr(database, "engine", engine)
    monkeypatch.setattr(database, "SessionLocal", sessionmaker(bind=engine, expire_on_commit=False))
    test = AppTest.from_file(str(Path(__file__).resolve().parents[1] / "app.py"), default_timeout=30).run()
    yield test, engine
    engine.dispose()


def widget(elements, label):
    return next(element for element in elements if element.label == label)


def test_every_empty_page_renders_without_predictions(app):
    test, engine = app
    for page in ("Dashboard", "Data", "Players", "ML Predictions", "Model Analysis", "Health"):
        test.sidebar.radio[0].set_value(page).run()
        assert not test.exception, list(test.exception)
    from sqlalchemy.orm import Session
    with Session(engine) as session:
        assert all(value == 0 for value in dataset_counts(session).values())


def test_manual_forms_save_all_five_datasets(app):
    test, engine = app
    test.sidebar.radio[0].set_value("Data").run()
    widget(test.text_input, "Player Id").set_value("UI001")
    widget(test.text_input, "Name").set_value("Form Test")
    widget(test.text_input, "Position").set_value("CM")
    widget(test.number_input, "Age").set_value(23)
    widget(test.button, "Save record").click().run()
    assert not test.exception
    for key in ("training", "recovery", "injuries", "matches"):
        test.selectbox(key="manual_dataset").set_value(key).run()
        player = next(element for element in test.selectbox if element.label == "Player Id")
        player.set_value("UI001")
        for element in test.date_input:
            element.set_value(date(2024, 1, 1))
        values = {
            "Duration Min (minutes)": 60.0, "Rpe (0-10)": 6.0, "Distance (km)": 8.0,
            "Sprint Distance (m)": 200.0, "High Speed Distance (m)": 700.0,
            "Sleep Hours (hours)": 8.0, "Sleep Quality (0-10)": 8.0, "Hrv (ms)": 70.0,
            "Resting Hr (bpm)": 55.0, "Soreness (0-10)": 2.0, "Stress (0-10)": 2.0,
            "Minutes Played": 90, "Goals": 1, "Assists": 0, "Shots": 3,
            "Passes Completed": 40, "Key Passes": 2, "Rating (0-10)": 7.0,
        }
        for element in test.number_input:
            if element.label in values:
                element.set_value(values[element.label])
        if key == "injuries":
            widget(test.selectbox, "Injury Occurred").set_value(False)
        widget(test.button, "Save record").click().run()
        assert not test.exception, list(test.exception)
    from sqlalchemy.orm import Session
    with Session(engine) as session:
        counts = dataset_counts(session)
        assert {key: counts[key] for key in ("players", "training", "recovery", "injuries", "matches")} == dict.fromkeys(("players", "training", "recovery", "injuries", "matches"), 1)
        assert all(counts[key] == 0 for key in ("health", "medical_tests", "health_events"))
    test.sidebar.radio[0].set_value("Players").run()
    assert not test.exception


def test_health_manual_forms(app):
    test, engine = app
    from sqlalchemy.orm import Session
    from services.data_service import import_records
    import pandas as pd
    with Session(engine) as session:
        assert import_records(session, pd.DataFrame([{'player_id': 'H001', 'name': 'Health Test', 'age': 24, 'position': 'CM'}]), 'players').ok
        session.commit()
    test.sidebar.radio[0].set_value('Data').run()
    for key in ('health', 'medical_tests', 'health_events'):
        test.selectbox(key='manual_dataset').set_value(key).run()
        widget(test.selectbox, 'Player Id').set_value('H001')
        for control in test.date_input:
            control.set_value(date(2024, 1, 1))
        if key == 'health':
            for control in test.number_input:
                if '(optional)' not in control.label:
                    control.set_value(60.0 if control.label in ('Resting Hr (bpm)', 'Hrv (ms)') else 7.0)
        if key == 'health_events':
            widget(test.selectbox, 'Health Event').set_value(False)
        widget(test.button, 'Save record').click().run()
        assert not test.exception, list(test.exception)
    with Session(engine) as session:
        assert all(dataset_counts(session)[key] == 1 for key in ('health', 'medical_tests', 'health_events'))
