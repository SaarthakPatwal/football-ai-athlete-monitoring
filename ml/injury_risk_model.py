from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import pandas as pd

from utils.calculations import estimate_injury_risk, explain_injury_risk


MODEL_INFO = {
    "name": "transparent_injury_risk_estimator",
    "version": "0.1.0",
    "target": "AI-assisted injury-risk estimate, 0-100 percent",
    "limitations": "Synthetic demonstration model. Not clinically validated and not a medical diagnosis.",
}


def train_model(training_frame: pd.DataFrame | None = None) -> dict[str, Any]:
    """Return metadata for the transparent baseline model.

    Phase 1 uses deterministic scoring rather than a black-box estimator so coaches can inspect the
    inputs and reasons. A scikit-learn model can replace this behind the same interface later.
    """
    rows = 0 if training_frame is None else len(training_frame)
    return {**MODEL_INFO, "training_rows": rows, "metrics": {"calibration": "rule-based baseline"}}


def save_model(model: dict[str, Any], path: str | Path) -> None:
    target = Path(path)
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(json.dumps(model, indent=2), encoding="utf-8")


def load_model(path: str | Path) -> dict[str, Any]:
    target = Path(path)
    if not target.exists():
        return train_model()
    return json.loads(target.read_text(encoding="utf-8"))


def predict(features: dict[str, float | int]) -> dict[str, Any]:
    risk = estimate_injury_risk(
        age=int(features["age"]),
        previous_injuries=int(features["previous_injuries"]),
        workload_change_pct=float(features["workload_change_pct"]),
        fatigue_score=float(features["fatigue_score"]),
        recovery_score=float(features["recovery_score"]),
        sleep_hours=float(features["sleep_hours"]),
        sprint_distance_m=float(features["sprint_distance_m"]),
        soreness=float(features["muscle_soreness"]),
    )
    explanation = explain_injury_risk(
        previous_injuries=int(features["previous_injuries"]),
        workload_change_pct=float(features["workload_change_pct"]),
        fatigue_score=float(features["fatigue_score"]),
        recovery_score=float(features["recovery_score"]),
        sleep_hours=float(features["sleep_hours"]),
        sprint_distance_m=float(features["sprint_distance_m"]),
        soreness=float(features["muscle_soreness"]),
    )
    return {"risk_pct": risk, "explanation": explanation}

