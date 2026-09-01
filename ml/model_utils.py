from __future__ import annotations

from pathlib import Path


MODEL_DIR = Path(__file__).resolve().parents[1] / "models"


def model_path(name: str) -> Path:
    MODEL_DIR.mkdir(parents=True, exist_ok=True)
    return MODEL_DIR / name

