from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from datetime import datetime, timezone
import json
from pathlib import Path
import joblib
import numpy as np
import pandas as pd
from sklearn.compose import ColumnTransformer
from sklearn.ensemble import GradientBoostingClassifier, GradientBoostingRegressor, RandomForestClassifier, RandomForestRegressor
from sklearn.impute import SimpleImputer
from sklearn.linear_model import LinearRegression, LogisticRegression
from sklearn.metrics import accuracy_score, precision_score, recall_score, f1_score, roc_auc_score, confusion_matrix, mean_absolute_error, mean_squared_error, r2_score
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder, StandardScaler
from services.data_service import dataset_fingerprint, dataset_counts, read_dataset
from services.validation_service import SCHEMAS
from services.feature_service import History, INJURY_FEATURES, PERFORMANCE_FEATURES, FEATURE_VERSION, build_injury_training_frame, build_performance_training_frame

SAVED_MODEL_DIR = Path(__file__).resolve().parents[1] / "data" / "model_artifacts"
MINIMUM_ROWS = {"injury": 40, "performance": 35}


@dataclass(frozen=True)
class TrainingOutcome:
    trained: bool
    message: str
    metadata: dict


def temporal_split(frame):
    dates = sorted(frame.date.unique())
    if len(dates) < 10:
        raise ValueError("At least 10 distinct prediction dates are required for three temporal splits.")
    validation_start = dates[int(len(dates) * 0.6)]
    test_start = dates[int(len(dates) * 0.8)]
    # Group equal dates and purge labels whose outcomes cross the following boundary.
    train = frame[(frame.date < validation_start) & (frame.label_end <= validation_start)]
    validation = frame[(frame.date >= validation_start) & (frame.date < test_start) & (frame.label_end <= test_start)]
    test = frame[frame.date >= test_start]
    if min(len(train), len(validation), len(test)) < 5:
        raise ValueError("Each purged chronological train/validation/test partition needs at least 5 usable rows.")
    return train, validation, test


def assess_frame(frame, task, counts, injury_events, min_rows=None, min_positive=5):
    features = INJURY_FEATURES if task == "injury" else PERFORMANCE_FEATURES
    missing = {field: (float(frame[field].isna().mean()) if len(frame) else 1.0) for field in features}
    reasons = []
    minimum = min_rows if min_rows is not None else MINIMUM_ROWS[task]
    if len(frame) < minimum:
        reasons.append(f"Requires {minimum} usable historical samples; found {len(frame)}.")
    if not counts["players"]:
        reasons.append("Add players first.")
    if task == "injury":
        positives = int(frame.target.sum()) if len(frame) else 0
        if positives < min_positive:
            reasons.append(f"Requires {min_positive} positive injury samples; found {positives}.")
        if injury_events < 5:
            reasons.append(f"Requires at least 5 recorded injury events; found {injury_events}.")
        if frame.target.nunique() < 2:
            reasons.append("Both injury and confirmed injury-free outcome windows are required.")
    elif not counts["matches"]:
        reasons.append("Add historical matches and their actual ratings.")
    for feature in ("workload_7d", "sleep_hours_7d_mean", "hrv_7d_mean"):
        if missing[feature] > 0.5:
            reasons.append(f"{feature} is missing in more than 50% of samples. Add dated training/recovery history.")
    if task == "performance" and missing["recent_rating_mean"] > 0.5:
        reasons.append("Recent match history is missing.")
    partitions = {}
    try:
        train, validation, test = temporal_split(frame)
        partitions = {"train": len(train), "validation": len(validation), "test": len(test),
                      "purged": len(frame) - len(train) - len(validation) - len(test)}
        if task == "injury":
            for label, part in (("train", train), ("validation", validation)):
                if part.target.nunique() < 2:
                    reasons.append(f"The chronological {label} partition needs both injury classes.")
        if task == "performance" and train.target.nunique() < 2:
            reasons.append("Training ratings must have at least two distinct values.")
    except ValueError as exc:
        reasons.append(str(exc))
    return {"ready": not reasons, "reasons": reasons, "dataset_rows": len(frame),
            "players": counts["players"], "matches": counts["matches"], "injury_events": injury_events,
            "positive_labels": int(frame.target.sum()) if task == "injury" else None,
            "negative_labels": int((frame.target == 0).sum()) if task == "injury" else None,
            "missing_fraction": missing, "partitions": partitions}


def readiness(session):
    history = History(session)
    counts = dataset_counts(session)
    events = int(history.frames["injuries"].injury_occurred.sum())
    return {task: assess_frame(history.training_frame(task), task, counts, events) for task in MINIMUM_ROWS}


def preprocessing(features):
    numeric = [feature for feature in features if feature != "position"]
    return ColumnTransformer([
        ("numeric", Pipeline([("imputer", SimpleImputer(strategy="median", keep_empty_features=True, add_indicator=True)),
                              ("scaler", StandardScaler())]), numeric),
        ("position", OneHotEncoder(handle_unknown="ignore", sparse_output=False), ["position"]),
    ], verbose_feature_names_out=False)


def evaluate(task, pipeline, frame, features):
    actual = frame.target.to_numpy()
    predicted = pipeline.predict(frame[features])
    if task == "injury":
        probabilities = pipeline.predict_proba(frame[features])[:, 1]
        return {"accuracy": float(accuracy_score(actual, predicted)),
                "precision": float(precision_score(actual, predicted, zero_division=0)),
                "recall": float(recall_score(actual, predicted, zero_division=0)),
                "f1": float(f1_score(actual, predicted, zero_division=0)),
                "roc_auc": float(roc_auc_score(actual, probabilities)) if len(set(actual)) == 2 else None,
                "confusion_matrix": confusion_matrix(actual, predicted, labels=[0, 1]).tolist()}
    return {"mae": float(mean_absolute_error(actual, predicted)),
            "rmse": float(np.sqrt(mean_squared_error(actual, predicted))),
            "r2": float(r2_score(actual, predicted)) if len(set(actual)) > 1 else None}


def contributors(pipeline):
    estimator = pipeline.named_steps["model"]
    names = pipeline.named_steps["preprocess"].get_feature_names_out()
    values = estimator.feature_importances_ if hasattr(estimator, "feature_importances_") else np.ravel(estimator.coef_)
    return sorted([{"feature": str(name), "value": float(value), "absolute_value": abs(float(value))}
                   for name, value in zip(names, values)], key=lambda row: row["absolute_value"], reverse=True)


def artifact_path(session, task):
    return SAVED_MODEL_DIR / f"{task}_{dataset_fingerprint(session)}.joblib"


def load_artifact(session, task):
    path = artifact_path(session, task)
    candidates = [path] if path.exists() else sorted(SAVED_MODEL_DIR.glob(f"{task}_*.joblib"), key=lambda item: item.stat().st_mtime, reverse=True)
    for candidate in candidates:
        artifact = joblib.load(candidate)
        metadata = artifact["metadata"]
        if metadata.get("feature_version") != FEATURE_VERSION:
            continue
        signature = dataset_fingerprint(session, date.fromisoformat(metadata["data_cutoff"]), metadata["training_player_ids"])
        if signature == metadata["dataset_fingerprint"]:
            return artifact
    return None


def train_model(session, task, min_rows=None, min_positive=5):
    frame = History(session).training_frame(task)
    events = int(read_dataset(session, "injuries").injury_occurred.sum())
    status = assess_frame(frame, task, dataset_counts(session), events, min_rows, min_positive)
    if not status["ready"]:
        return TrainingOutcome(False, " ".join(status["reasons"]), status)
    train, validation, test = temporal_split(frame)
    features = INJURY_FEATURES if task == "injury" else PERFORMANCE_FEATURES
    if task == "injury":
        models = {"Logistic Regression": LogisticRegression(max_iter=2000, class_weight="balanced"),
                  "Random Forest": RandomForestClassifier(n_estimators=100, random_state=42, class_weight="balanced", min_samples_leaf=2),
                  "Gradient Boosting": GradientBoostingClassifier(random_state=42)}
    else:
        models = {"Linear Regression": LinearRegression(),
                  "Random Forest Regressor": RandomForestRegressor(n_estimators=100, random_state=42, min_samples_leaf=2),
                  "Gradient Boosting Regressor": GradientBoostingRegressor(random_state=42)}
    comparison, best_name, best_score = [], None, -float("inf")
    for name, estimator in models.items():
        pipeline = Pipeline([("preprocess", preprocessing(features)), ("model", estimator)])
        pipeline.fit(train[features], train.target.astype(int) if task == "injury" else train.target.astype(float))
        metrics = evaluate(task, pipeline, validation, features)
        comparison.append({"model": name, **{key: value for key, value in metrics.items() if key != "confusion_matrix"}})
        score = 0.7 * metrics["recall"] + 0.3 * metrics["f1"] if task == "injury" else -metrics["mae"]
        if score > best_score:
            best_name, best_score = name, score
    # Select on validation only; the final chronological test is evaluated once.
    fit = pd.concat([train, validation]).sort_values("date")
    best = Pipeline([("preprocess", preprocessing(features)), ("model", models[best_name])])
    best.fit(fit[features], fit.target.astype(int) if task == "injury" else fit.target.astype(float))
    metrics = evaluate(task, best, test, features)
    predicted = best.predict(test[features])
    dated = [read_dataset(session, key)[SCHEMAS[key].date_columns[0]].max()
             for key in ("training", "recovery", "injuries", "matches") if not read_dataset(session, key).empty]
    data_cutoff = max(dated)
    player_ids = read_dataset(session, "players").player_id.tolist()
    examples = [{"player_id": row.player_id, "date": str(row.date), "actual": float(row.target), "predicted": float(value)}
                for row, value in zip(test.itertuples(index=False), predicted)][:20]
    metadata = {**status, "trained_at": datetime.now(timezone.utc).isoformat(),
                "feature_version": FEATURE_VERSION, "dataset_fingerprint": dataset_fingerprint(session),
                "data_cutoff": str(data_cutoff), "training_player_ids": player_ids,
                "features": features, "target": "injury within next 7 calendar days" if task == "injury" else "next match rating",
                "fitted_through": str(fit.label_end.max()),
                "best_model": best_name, "comparison": comparison, "test_metrics": metrics,
                "selection_metric": "0.7 * validation recall + 0.3 * validation F1" if task == "injury" else "lowest validation MAE",
                "methodology": "Chronological 60/20/20 by distinct dates. Labels crossing boundaries are purged. Select on validation, refit on train + validation, evaluate on untouched test. No random split.",
                "date_ranges": {name: [str(part.date.min()), str(part.date.max())] for name, part in (("train", train), ("validation", validation), ("test", test))},
                "top_model_contributors": contributors(best), "prediction_examples": examples,
                "limitations": ["Recorded age and position are static profile inputs; historical age changes are not inferred.",
                               "Injury-free labels require explicit daily outcome records for all seven days.",
                               "Unrecorded training/rest days cannot be distinguished; workload totals cover recorded sessions only.",
                               "Players can occur in multiple time partitions; metrics measure future records, not unseen-player generalization.",
                               "Global feature importance is not a causal explanation or a player-specific attribution.",
                               "Probabilities are uncalibrated research outputs, not medical advice."]}
    path = artifact_path(session, task)
    path.parent.mkdir(parents=True, exist_ok=True)
    joblib.dump({"pipeline": best, "metadata": metadata}, path)
    path.with_suffix(".json").write_text(json.dumps(metadata, indent=2, allow_nan=False), encoding="utf-8")
    return TrainingOutcome(True, f"Trained {best_name}.", metadata)


def train_injury_model(session, min_rows=40, min_positive=5):
    return train_model(session, "injury", min_rows, min_positive)


def train_performance_model(session, min_rows=35):
    return train_model(session, "performance", min_rows)
