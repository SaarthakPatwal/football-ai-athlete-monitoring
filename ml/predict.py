from __future__ import annotations

from datetime import date, timedelta
import pandas as pd
from services.feature_service import History
from ml.train import load_artifact


def predict(session, task, point=None):
    artifact = load_artifact(session, task)
    if artifact is None:
        return pd.DataFrame()
    point = point or date.today() + timedelta(days=1)
    # Backdated forecasts cannot use an artifact fitted on outcomes after that date.
    if point < date.fromisoformat(artifact["metadata"]["fitted_through"]):
        return pd.DataFrame()
    frame = History(session).prediction_frame(task, point)
    if frame.empty:
        return pd.DataFrame()
    output = frame[["player_id", "name", "as_of"]].copy()
    pipeline = artifact["pipeline"]
    features = artifact["metadata"]["features"]
    if task == "injury":
        probability = pipeline.predict_proba(frame[features])[:, 1]
        output["probability"] = probability
        # Display bins only; the probabilities come exclusively from the fitted classifier.
        output["risk"] = ["High" if value >= 0.7 else "Medium" if value >= 0.4 else "Low" for value in probability]
    else:
        output["predicted_next_rating"] = pipeline.predict(frame[features])
    return output


def predict_injury_probabilities(session, point=None):
    return predict(session, "injury", point)


def predict_next_match_ratings(session, point=None):
    return predict(session, "performance", point)
