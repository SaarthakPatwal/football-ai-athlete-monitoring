"""Independent supervised health artifacts, using the existing evaluation/split machinery."""
from datetime import date, datetime, timezone
from pathlib import Path
import json
import joblib
import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestClassifier, GradientBoostingClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.impute import SimpleImputer
from sklearn.preprocessing import StandardScaler
from sklearn.pipeline import Pipeline
from ml.train import temporal_split, evaluate, TrainingOutcome, contributors
from services.data_service import dataset_fingerprint
from services.health_service import HealthHistory, HEALTH_FEATURES, FEATURE_VERSION

SAVED_MODEL_DIR = Path(__file__).resolve().parents[1] / 'data' / 'model_artifacts' / 'health'
DATASET_KEYS = ('players', 'health', 'medical_tests', 'health_events')


def signature(session, cutoff=None, player_ids=None):
    return dataset_fingerprint(session, cutoff, player_ids, DATASET_KEYS)


def assess_health(history, frame):
    reasons = []
    events = int(history.frames['health_events'].health_event.sum())
    if len(frame) < 40:
        reasons.append(f'Insufficient labelled data: at least 40 usable windows required; found {len(frame)}.')
    if events < 5:
        reasons.append(f'At least five documented health events required; found {events}.')
    if frame.target.nunique() < 2:
        reasons.append('Both documented event and confirmed event-free windows are required. Missing follow-up is unknown.')
    partitions = {}
    try:
        train, validation, test = temporal_split(frame)
        for name, part in (('train', train), ('validation', validation), ('test', test)):
            partitions[name] = len(part)
            if name != 'test' and part.target.nunique() < 2:
                reasons.append(f'The {name} period must contain both outcome classes.')
        partitions['purged'] = len(frame) - sum(partitions.values())
    except ValueError as exc:
        reasons.append(str(exc))
    return {'ready': not reasons, 'reasons': reasons, 'usable_windows': len(frame),
            'positive_windows': int(frame.target.sum()), 'negative_windows': int((frame.target == 0).sum()),
            'documented_events': events, 'partitions': partitions}


def preprocessing():
    return Pipeline([('imputer', SimpleImputer(strategy='median', keep_empty_features=True, add_indicator=True)),
                     ('scaler', StandardScaler())])


def train_health_model(session):
    history = HealthHistory(session)
    frame = history.training_frame()
    status = assess_health(history, frame)
    if not status['ready']:
        return TrainingOutcome(False, ' '.join(status['reasons']), status)
    train, validation, test = temporal_split(frame)
    candidates = {
        'Logistic Regression': LogisticRegression(max_iter=2000, class_weight='balanced'),
        'Random Forest Classifier': RandomForestClassifier(n_estimators=100, min_samples_leaf=2, class_weight='balanced', random_state=42),
        'Gradient Boosting Classifier': GradientBoostingClassifier(random_state=42)}
    comparisons, best_name, best_score = [], None, -1
    for name, model in candidates.items():
        pipeline = Pipeline([('preprocess', preprocessing()), ('model', model)])
        pipeline.fit(train[HEALTH_FEATURES], train.target.astype(int))
        metrics = evaluate('injury', pipeline, validation, HEALTH_FEATURES)
        score = 0.7 * metrics['recall'] + 0.3 * metrics['f1']
        comparisons.append({'model': name, 'selection_score': score, **{k: v for k, v in metrics.items() if k != 'confusion_matrix'}})
        if score > best_score:
            best_name, best_score = name, score
    fit = pd.concat([train, validation]).sort_values('date')
    best = Pipeline([('preprocess', preprocessing()), ('model', candidates[best_name])])
    best.fit(fit[HEALTH_FEATURES], fit.target.astype(int))
    metrics = evaluate('injury', best, test, HEALTH_FEATURES)
    cutoff = max(history.frames[key][field].max()
                 for key, field in (('health', 'date'), ('medical_tests', 'test_date'), ('health_events', 'event_date'))
                 if not history.frames[key].empty)
    metadata = {**status, 'features': HEALTH_FEATURES, 'feature_version': FEATURE_VERSION,
                'trained_at': datetime.now(timezone.utc).isoformat(), 'data_cutoff': str(cutoff),
                'training_player_ids': history.frames['players'].player_id.tolist(),
                'dataset_fingerprint': signature(session), 'fitted_through': str(fit.label_end.max()),
                'best_model': best_name, 'comparison': comparisons, 'test_metrics': metrics,
                'selection_metric': '0.7 * validation recall + 0.3 * validation F1; ties use listed candidate order',
                'target': 'Documented health event in [prediction date, prediction date + 7 days)',
                'methodology': '60/20/20 chronological distinct dates; purge crossing label windows; select on validation; refit retained train + validation; evaluate untouched test.',
                'date_ranges': {name: [str(part.date.min()), str(part.date.max())] for name, part in (('train', train), ('validation', validation), ('test', test))},
                'top_model_contributors': contributors(best),
                'reference_values': {key: None if pd.isna(value) else float(value) for key, value in fit[HEALTH_FEATURES].median().items()}}
    SAVED_MODEL_DIR.mkdir(parents=True, exist_ok=True)
    path = SAVED_MODEL_DIR / (metadata['dataset_fingerprint'] + '.joblib')
    joblib.dump({'pipeline': best, 'metadata': metadata}, path)
    path.with_suffix('.json').write_text(json.dumps(metadata, indent=2, allow_nan=False), encoding='utf-8')
    return TrainingOutcome(True, f'Trained {best_name}.', metadata)


def load_health_artifact(session):
    for path in sorted(SAVED_MODEL_DIR.glob('*.joblib'), key=lambda p: p.stat().st_mtime, reverse=True):
        artifact = joblib.load(path)
        metadata = artifact['metadata']
        if metadata.get('feature_version') != FEATURE_VERSION:
            continue
        if signature(session, date.fromisoformat(metadata['data_cutoff']), metadata['training_player_ids']) == metadata['dataset_fingerprint']:
            return artifact
    return None


def predict_health(session, point, artifact=None):
    artifact = artifact or load_health_artifact(session)
    if artifact is None or point < date.fromisoformat(artifact['metadata']['fitted_through']):
        return pd.DataFrame()
    frame = HealthHistory(session).prediction_frame(point)
    if frame.empty:
        return pd.DataFrame()
    output = frame[['player_id', 'name', 'as_of']].copy()
    output['probability'] = artifact['pipeline'].predict_proba(frame[HEALTH_FEATURES])[:, 1]
    output['risk'] = ['HIGH' if p >= .7 else 'MEDIUM' if p >= .4 else 'LOW' for p in output.probability]
    return output


def explain_prediction(artifact, features):
    """Local one-feature-at-a-time reference substitution, not causal attribution."""
    row = pd.DataFrame([features], columns=HEALTH_FEATURES)
    baseline = artifact['pipeline'].predict_proba(row)[0, 1]
    variants = pd.concat([row] * len(HEALTH_FEATURES), ignore_index=True)
    for i, field in enumerate(HEALTH_FEATURES):
        reference = artifact['metadata']['reference_values'][field]
        variants.loc[i, field] = np.nan if reference is None else reference
    changed = artifact['pipeline'].predict_proba(variants)[:, 1]
    return pd.DataFrame({'feature': HEALTH_FEATURES, 'observed_feature': row.iloc[0].to_numpy(),
                         'probability_difference': baseline - changed}).assign(
                             magnitude=lambda f: f.probability_difference.abs()).sort_values('magnitude', ascending=False).head(8)
