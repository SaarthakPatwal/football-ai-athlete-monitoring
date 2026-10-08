from __future__ import annotations

from dataclasses import dataclass
import hashlib
import json
import pandas as pd
from sqlalchemy import select, func
from sqlalchemy.exc import IntegrityError
from database.models import DATASETS, Player
from services.validation_service import SCHEMAS, normalize_frame


@dataclass
class ImportResult:
    imported_rows: int
    problems: list[dict]

    @property
    def ok(self):
        return not self.problems


def read_dataset(session, key):
    model = DATASETS[key]
    records = list(session.scalars(select(model)))
    return pd.DataFrame([{column: getattr(record, column) for column in SCHEMAS[key].columns}
                         for record in records], columns=SCHEMAS[key].columns)


def dataset_counts(session):
    return {key: session.scalar(select(func.count()).select_from(model)) for key, model in DATASETS.items()}


def validate_input(session, frame, key):
    known = set(session.scalars(select(Player.player_id)))
    stored = read_dataset(session, key)
    keys = {(row.player_id,) if key == "players" else (row.player_id, getattr(row, SCHEMAS[key].date_columns[0]))
            for row in stored.itertuples(index=False)}
    return normalize_frame(frame, key, known, keys)


def import_records(session, frame, key, valid_only=False):
    # CSV and manual forms both enter through this transaction and validation path.
    valid, problems = validate_input(session, frame, key)
    if problems and not valid_only:
        return ImportResult(0, problems)
    if valid.empty:
        return ImportResult(0, problems)
    try:
        with session.begin_nested():
            for row in valid.drop(columns="_source_row").to_dict("records"):
                row = {field: None if pd.isna(value) else value for field, value in row.items()}
                session.add(DATASETS[key](**row))
            session.flush()
    except IntegrityError:
        return ImportResult(0, [{"row": "-", "field": "record", "message": "A duplicate or invalid relationship was detected. Refresh and validate again."}])
    return ImportResult(len(valid), problems)


def dataset_fingerprint(session, cutoff=None, player_ids=None, dataset_keys=None):
    # Keep the original five-dataset signature stable for existing injury/performance artifacts.
    # Health explicitly supplies its own dataset keys; unrelated uploads cannot invalidate a model.
    content = {}
    for key in (dataset_keys or ("players", "training", "recovery", "injuries", "matches")):
        frame = read_dataset(session, key)
        if player_ids is not None:
            frame = frame[frame.player_id.isin(player_ids)]
        if cutoff is not None and key != "players":
            frame = frame[frame[SCHEMAS[key].date_columns[0]] <= cutoff]
        records = [{field: None if pd.isna(value) else value for field, value in record.items()}
                   for record in frame.to_dict("records")]
        content[key] = sorted(records, key=lambda row: json.dumps(row, sort_keys=True, default=str))
    return hashlib.sha256(json.dumps(content, sort_keys=True, default=str, allow_nan=False).encode()).hexdigest()
