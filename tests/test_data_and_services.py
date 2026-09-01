from datetime import date

from sqlalchemy.orm import sessionmaker

from database.database import get_engine, init_db
from database.models import Player, RecoveryRecord, TrainingSession
from services.data_entry_service import add_recovery_record, add_training_session
from services.analytics_service import latest_team_summary, team_kpis
from services.recommendation_service import recommendations_for_player
from utils.data_generator import generate_demo_data


def _build_session():
    engine = get_engine("sqlite:///:memory:")
    init_db(engine)
    Session = sessionmaker(bind=engine, future=True)
    return Session()


def test_demo_data_generator_creates_core_datasets():
    data = generate_demo_data(player_count=5, days=14, seed=7)
    assert len(data["players"]) == 5
    assert len(data["training_sessions"]) == 70
    assert len(data["recovery_records"]) == 70


def test_player_retrieval_summary_and_recommendations():
    session = _build_session()
    data = generate_demo_data(player_count=3, days=21, seed=9)
    session.add_all(Player(**row) for row in data["players"])
    session.add_all(TrainingSession(**row) for row in data["training_sessions"])
    session.add_all(RecoveryRecord(**row) for row in data["recovery_records"])
    session.commit()

    summary = latest_team_summary(session)
    kpis = team_kpis(summary)
    assert kpis["Squad Size"] == 3
    assert {"Fitness", "Recovery", "Fatigue", "Risk"}.issubset(summary.columns)

    player = session.get(Player, 1)
    recommendations = recommendations_for_player(session, player)
    assert recommendations
    assert "recommendation" in recommendations[0]


def test_manual_training_and_recovery_update_summary():
    session = _build_session()
    player = Player(**generate_demo_data(player_count=1, days=2, seed=15)["players"][0])
    session.add(player)
    session.commit()

    ok, errors = add_recovery_record(session, player, {
        "date": date.today(),
        "sleep_hours": 5.5,
        "sleep_quality": 52.0,
        "hrv": 58.0,
        "resting_hr": 60.0,
        "hydration": 62.0,
        "muscle_soreness": 78.0,
        "stress": 65.0,
        "mood": 55.0,
        "recovery_session": False,
        "rest_day": False,
    })
    assert ok, errors

    ok, errors = add_training_session(session, player, {
        "date": date.today(),
        "session_type": "Conditioning",
        "duration_min": 100.0,
        "intensity": 90.0,
        "rpe": 9.0,
        "distance_km": 10.5,
        "sprint_distance_m": 900.0,
        "high_speed_running_m": 1500.0,
        "accelerations": 44,
        "decelerations": 40,
        "average_hr": 162.0,
        "max_hr": 190.0,
    })
    assert ok, errors

    summary = latest_team_summary(session)
    assert len(summary) == 1
    assert summary.iloc[0]["Workload"] == 900.0
    assert summary.iloc[0]["Risk %"] > 0
