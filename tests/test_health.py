from datetime import date, timedelta
from pathlib import Path
import numpy as np
import pandas as pd
import pytest
from sqlalchemy import inspect
from tests.test_ml_system import session, add_player
from services.data_service import import_records, dataset_counts, dataset_fingerprint, read_dataset
from services.health_service import HealthHistory, trend_analysis, cluster_health
from services.health_schema import HEALTH_REQUIRED
from ml.health import train_health_model, predict_health, load_health_artifact, explain_prediction
from ml.train import temporal_split


def health_row(day='2024-01-01', **changes):
    return {'player_id': '001', 'date': day, **dict(zip(HEALTH_REQUIRED, [55, 70, 8, 8, 2, 2, 2, 8, 8])), **changes}


@pytest.mark.parametrize('changes', [{'hrv': ''}, {'fatigue': 11}, {'energy_level': 'bad'}, {'hydration_status': 'inf'},
                                      {'date': '01/02/2024'}, {'player_id': 'missing'}, {'blood_pressure_sys': 70, 'blood_pressure_dia': 80}])
def test_invalid_health(session, changes):
    add_player(session)
    result = import_records(session, pd.DataFrame([health_row(**changes)]), 'health')
    assert not result.ok and result.imported_rows == 0
    assert dataset_counts(session)['health'] == 0


def test_health_insert_optional_nulls_duplicates_and_independence(session):
    add_player(session)
    original = dataset_fingerprint(session)
    assert import_records(session, pd.DataFrame([health_row()]), 'health').ok
    assert read_dataset(session, 'health').weight.isna().all()
    assert not import_records(session, pd.DataFrame([health_row()]), 'health').ok
    assert original == dataset_fingerprint(session)  # Health cannot invalidate injury/performance artifacts.
    assert {'health_records', 'medical_tests', 'health_events'} <= set(inspect(session.bind).get_table_names())


@pytest.mark.parametrize('values,valid', [({'hemoglobin': 14}, True), ({}, True), ({'crp': ''}, True),
                                        ({'crp': -1}, False), ({'ferritin': 'x'}, False),
                                        ({'player_id': 'unknown'}, False), ({'test_date': '2099-01-01'}, False)])
def test_medical_validation(session, values, valid):
    add_player(session)
    row = {'player_id': '001', 'test_date': '2024-01-01', **values}
    result = import_records(session, pd.DataFrame([row]), 'medical_tests')
    assert result.ok == valid
    if valid:
        assert read_dataset(session, 'medical_tests').vitamin_b12.isna().all()
        assert not import_records(session, pd.DataFrame([row]), 'medical_tests').ok


def test_temporal_health_features_and_sparse_labs(session):
    add_player(session)
    rows = [health_row('2024-01-01', hrv=100), health_row('2024-01-08', hrv=70),
            health_row('2024-01-10', hrv=60), health_row('2024-01-11', hrv=1)]
    assert import_records(session, pd.DataFrame(rows), 'health').ok
    tests = [{'player_id': '001', 'test_date': day, 'ferritin': value}
             for day, value in [('2024-01-01', 90), ('2024-01-09', 80), ('2024-01-10', None), ('2024-01-11', 1)]]
    assert import_records(session, pd.DataFrame(tests), 'medical_tests').ok
    before = HealthHistory(session).snapshot('001', date(2024, 1, 11))
    assert before['hrv_7d_mean'] == 65
    assert before['hrv_change'] == -10
    assert before['hrv_trend'] == pytest.approx(-5)
    assert before['latest_ferritin'] == 80
    assert before['change_ferritin'] == -10
    assert before['days_since_ferritin'] == 2
    assert np.isnan(before['latest_crp'])
    assert import_records(session, pd.DataFrame([health_row('2024-01-12', hrv=200)]), 'health').ok
    after = HealthHistory(session).snapshot('001', date(2024, 1, 11))
    pd.testing.assert_series_equal(pd.Series(before), pd.Series(after))


def test_explicit_followup_and_horizon(session):
    add_player(session)
    assert import_records(session, pd.DataFrame([health_row()]), 'health').ok
    assert HealthHistory(session).training_frame().empty
    # Event on D+7 is outside [D,D+7).
    events = [{'player_id': '001', 'event_date': '2024-01-09', 'health_event': 1}]
    assert import_records(session, pd.DataFrame(events), 'health_events').ok
    assert HealthHistory(session).training_frame().empty
    for i in range(2, 9):
        event = {'player_id': '001', 'event_date': date(2024, 1, i), 'health_event': 0}
        assert import_records(session, pd.DataFrame([event]), 'health_events').ok
    frame = HealthHistory(session).training_frame()
    assert frame.target.tolist() == [0]
    assert not train_health_model(session).trained


def test_trends_calendar_missing_and_zero_change():
    frame = pd.DataFrame({'date': [date(2024, 1, d) for d in (1, 9, 10, 11)], 'hrv': [100, 70, None, 60]})
    chart, result = trend_analysis(frame, 'hrv')
    assert result['rolling_average'] == 65
    assert result['change_pct'] == pytest.approx(-100 / 7)
    assert result['trend'] == 'Declining'
    assert len(chart) == 3
    assert trend_analysis(frame.assign(hrv=np.nan), 'hrv')[1] == {}
    assert trend_analysis(frame.iloc[:2].assign(hrv=[0, 2]), 'hrv')[1]['change_pct'] is None


@pytest.fixture
def demo_session(session):
    root = Path(__file__).resolve().parents[1] / 'demo_data'
    for key in ('players', 'health', 'medical_tests', 'health_events'):
        result = import_records(session, pd.read_csv(root / f'{key}.csv', dtype=str, keep_default_na=False), key)
        assert result.ok, result.problems[:3]
    return session


def test_health_end_to_end(demo_session, tmp_path, monkeypatch):
    import ml.health as module
    monkeypatch.setattr(module, 'SAVED_MODEL_DIR', tmp_path / 'health')
    result = train_health_model(demo_session)
    assert result.trained, result.message
    assert len(result.metadata['comparison']) == 3
    assert set(result.metadata['test_metrics']) == {'accuracy', 'precision', 'recall', 'f1', 'roc_auc', 'confusion_matrix'}
    artifact = load_health_artifact(demo_session)
    assert artifact is not None
    frame = HealthHistory(demo_session).training_frame()
    train, validation, test = temporal_split(frame)
    assert train.label_end.max() <= validation.date.min()
    assert validation.label_end.max() <= test.date.min()
    expected_reference = pd.concat([train, validation])[result.metadata['features']].median()
    for field, value in expected_reference.items():
        assert result.metadata['reference_values'][field] == (None if pd.isna(value) else value)
    point = date(2026, 10, 7)
    output = predict_health(demo_session, point)
    assert len(output) == 12 and output.probability.between(0, 1).all()
    assert predict_health(demo_session, date(2026, 5, 20)).empty
    assert predict_health(demo_session, date(2027, 1, 1)).empty
    explanation = explain_prediction(artifact, HealthHistory(demo_session).snapshot('P001', point))
    assert len(explanation) == 8 and explanation.magnitude.notna().all()
    assert list((tmp_path / 'health').glob('*.json'))
    # Render the populated Health page and exercise its prediction and clustering controls.
    from streamlit.testing.v1 import AppTest
    import views.health as view
    history = HealthHistory(demo_session)
    monkeypatch.setattr(view, 'HealthHistory', lambda *args, **kwargs: history)
    monkeypatch.setattr(view, 'load_health_artifact', lambda _: artifact)
    monkeypatch.setattr(view, 'train_health_model', lambda _: result)
    monkeypatch.setattr(view, 'predict_health', lambda _, when, model=None: predict_health(demo_session, when, model))
    monkeypatch.setattr(view, 'cluster_health', lambda _, when, count: cluster_health(demo_session, when, count))
    rendered = AppTest.from_string("from views.health import render\nrender(None)", default_timeout=90).run()
    assert not rendered.exception, list(rendered.exception)
    assert [tab.label for tab in rendered.tabs] == ['Health Monitoring', 'Health Trends', 'Health Clustering']
    next(button for button in rendered.button if button.label == 'Train Health Model').click().run()
    assert not rendered.exception
    next(button for button in rendered.button if button.label == 'Predict Health Risk').click().run()
    assert not rendered.exception
    assert any(metric.label == 'Probability' for metric in rendered.metric)
    next(button for button in rendered.button if button.label == 'Run Health Clustering').click().run()
    assert not rendered.exception
    assert any('Cluster profiles' in heading.value for heading in rendered.subheader)
    # Genuine historical edits invalidate the health artifact.
    from database.models import HealthRecord
    from sqlalchemy import select
    demo_session.scalars(select(HealthRecord)).first().hrv += 1
    demo_session.flush()
    assert load_health_artifact(demo_session) is None


def test_clustering(demo_session):
    result = cluster_health(demo_session, date(2026, 10, 7), 3)
    assert len(result['assignments']) == 12
    assert result['assignments'].cluster.nunique() == 3
    assert len(result['profiles']) == 3
    assert np.isfinite(result['assignments'][['PC1', 'PC2']]).all().all()
    assert not any('days_since' in feature for feature in result['features'])
    with pytest.raises(ValueError):
        cluster_health(demo_session, date(2026, 10, 7), 6)
    with pytest.raises(ValueError):
        cluster_health(demo_session, date(2027, 1, 1), 3)


def test_empty_health_has_no_model_or_predictions(session, tmp_path, monkeypatch):
    import ml.health as module
    monkeypatch.setattr(module, 'SAVED_MODEL_DIR', tmp_path)
    assert predict_health(session, date.today()).empty
    assert not train_health_model(session).trained
    assert not list(tmp_path.iterdir())


def test_positive_window_does_not_require_unobserved_negative_days(session):
    add_player(session)
    assert import_records(session, pd.DataFrame([health_row()]), 'health').ok
    assert import_records(session, pd.DataFrame([{'player_id': '001', 'event_date': '2024-01-08', 'health_event': 1}]), 'health_events').ok
    assert HealthHistory(session).training_frame().target.tolist() == [1]


def test_upgrade_existing_tables_is_additive():
    from database.models import Base, Player, TrainingSession, RecoveryRecord, InjuryHistory, MatchRecord
    from database.database import get_engine, init_db
    from sqlalchemy.orm import Session
    engine = get_engine('sqlite:///:memory:')
    Base.metadata.create_all(engine, tables=[model.__table__ for model in (Player, TrainingSession, RecoveryRecord, InjuryHistory, MatchRecord)])
    with Session(engine) as active:
        add_player(active)
        active.commit()
    init_db(engine)
    with Session(engine) as active:
        assert active.get(Player, '001') is not None
        assert all(dataset_counts(active)[key] == 0 for key in ('health', 'medical_tests', 'health_events'))
    engine.dispose()


def test_model_handles_entirely_absent_medical_history(demo_session, tmp_path, monkeypatch):
    from sqlalchemy import delete
    from database.models import MedicalTest
    import ml.health as module
    demo_session.execute(delete(MedicalTest))
    demo_session.flush()
    monkeypatch.setattr(module, 'SAVED_MODEL_DIR', tmp_path)
    result = train_health_model(demo_session)
    assert result.trained, result.message
    assert result.metadata['reference_values']['latest_ferritin'] is None
    assert predict_health(demo_session, date(2026, 10, 7)).probability.between(0, 1).all()
