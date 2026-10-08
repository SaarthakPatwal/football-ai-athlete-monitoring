"""Calendar-based health history, explicit follow-up labels, trends and clustering."""
from datetime import timedelta
import numpy as np
import pandas as pd
from sklearn.cluster import KMeans
from sklearn.decomposition import PCA
from sklearn.impute import SimpleImputer
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler
from services.data_service import read_dataset
from services.health_schema import HEALTH_REQUIRED, HEALTH_OPTIONAL, MEDICAL_FIELDS

HEALTH_FEATURES = [f'{field}_{suffix}' for field in HEALTH_REQUIRED
                  for suffix in ('7d_mean', 'trend', 'change')]
HEALTH_FEATURES += [f'latest_{field}' for field in HEALTH_OPTIONAL]
HEALTH_FEATURES += [f'{prefix}{field}' for field in MEDICAL_FIELDS for prefix in ('latest_', 'change_', 'days_since_')]
HEALTH_FEATURES += ['health_observations_7d', 'days_since_health']
FEATURE_VERSION = 1


def slope(values):
    if len(values) < 2:
        return np.nan
    days = (values.index - values.index.min()).days.to_numpy(dtype=float)
    return float(np.polyfit(days, values.to_numpy(dtype=float), 1)[0]) if days.max() > 0 else np.nan


class HealthHistory:
    def __init__(self, session, frames=None):
        self.frames = frames if frames is not None else {key: read_dataset(session, key) for key in ('players', 'health', 'medical_tests', 'health_events')}
        self.grouped = {key: dict(tuple(frame.groupby('player_id'))) for key, frame in self.frames.items() if key != 'players'}
        self.medical_series = {}
        for pid, records in self.grouped['medical_tests'].items():
            records = records.sort_values('test_date')
            self.medical_series[pid] = {field: (records.loc[records[field].notna(), 'test_date'].to_numpy(),
                                                records[field].dropna().to_numpy(dtype=float)) for field in MEDICAL_FIELDS}

    def records(self, key, player_id):
        return self.grouped[key].get(player_id, self.frames[key].iloc[:0])

    def snapshot(self, player_id, point):
        health = self.records('health', player_id)
        prior = health[health.date < point].sort_values('date')
        recent = prior[prior.date >= point - timedelta(days=7)]
        output = {'health_observations_7d': len(recent),
                  'days_since_health': (point - prior.date.max()).days if len(prior) else np.nan}
        for field in HEALTH_REQUIRED:
            values = pd.Series(recent[field].to_numpy(dtype=float), index=pd.to_datetime(recent.date)).dropna()
            output[field + '_7d_mean'] = float(values.mean()) if len(values) else np.nan
            output[field + '_trend'] = slope(values)
            output[field + '_change'] = float(values.iloc[-1] - values.iloc[0]) if len(values) >= 2 else np.nan
        for field in HEALTH_OPTIONAL:
            values = recent[field].dropna()
            output['latest_' + field] = float(values.iloc[-1]) if len(values) else np.nan
        for field in MEDICAL_FIELDS:
            dates, values = self.medical_series.get(player_id, {}).get(field, (np.array([], dtype=object), np.array([])))
            count = int(np.searchsorted(dates, point, side='left'))
            output['latest_' + field] = float(values[count - 1]) if count else np.nan
            output['change_' + field] = float(values[count - 1] - values[count - 2]) if count >= 2 else np.nan
            output['days_since_' + field] = (point - dates[count - 1]).days if count else np.nan
        return output

    def prediction_frame(self, point):
        rows = []
        for player in self.frames['players'].itertuples(index=False):
            features = self.snapshot(player.player_id, point)
            if features['health_observations_7d']:
                rows.append({'player_id': player.player_id, 'name': player.name, 'as_of': point, **features})
        return pd.DataFrame(rows, columns=['player_id', 'name', 'as_of', *HEALTH_FEATURES])

    def training_frame(self):
        rows = []
        for pid, health in self.grouped['health'].items():
            events = self.records('health_events', pid)
            for recorded in sorted(health.date):
                point = recorded + timedelta(days=1)
                end = point + timedelta(days=7)
                future = events[(events.event_date >= point) & (events.event_date < end)]
                positive = bool(future.health_event.any())
                if not positive and len(set(future.event_date)) != 7:
                    continue
                rows.append({'player_id': pid, 'date': point, 'label_end': end,
                             'target': int(positive), **self.snapshot(pid, point)})
        return pd.DataFrame(rows, columns=['player_id', 'date', 'label_end', 'target', *HEALTH_FEATURES]).sort_values(['date', 'player_id']).reset_index(drop=True)


def trend_analysis(frame, field, date_field='date', window_days=7):
    """Observed values only; rolling means are calendar windows, not row counts."""
    selected = frame[[date_field, field]].dropna().sort_values(date_field)
    values = pd.Series(selected[field].to_numpy(dtype=float), index=pd.to_datetime(selected[date_field]), name=field)
    if values.empty:
        return pd.DataFrame(), {}
    rolling = values.rolling(f'{window_days}D', min_periods=1).mean()
    change = float((values.iloc[-1] / values.iloc[-2] - 1) * 100) if len(values) >= 2 and values.iloc[-2] != 0 else None
    gradient = slope(values.tail(7))
    return pd.DataFrame({'Observed': values, f'{window_days}-day mean': rolling}), {
        'recent_value': float(values.iloc[-1]), 'rolling_average': float(rolling.iloc[-1]),
        'change_pct': change, 'trend': 'Insufficient history' if pd.isna(gradient) else
        ('Rising' if gradient > 1e-8 else 'Declining' if gradient < -1e-8 else 'Stable')}


CLUSTER_FEATURES = [f'{field}_7d_mean' for field in HEALTH_REQUIRED] + [f'latest_{field}' for field in ('hemoglobin', 'ferritin', 'vitamin_d', 'crp')]


def cluster_health(session, point, n_clusters=3):
    if n_clusters not in (2, 3, 4, 5):
        raise ValueError('Choose 2, 3, 4 or 5 clusters.')
    frame = HealthHistory(session).prediction_frame(point)
    if len(frame) < n_clusters:
        raise ValueError(f'At least {n_clusters} players with health records in the prior seven days are required.')
    # Drop unavailable or mostly absent optional labs rather than clustering missingness.
    fields = [f for f in CLUSTER_FEATURES if frame[f].notna().mean() >= 0.5 and frame[f].nunique() > 1]
    if not fields:
        raise ValueError('No varying health features are available for clustering.')
    preprocess = Pipeline([('imputer', SimpleImputer(strategy='median')), ('scale', StandardScaler())])
    scaled = preprocess.fit_transform(frame[fields])
    if len(np.unique(scaled, axis=0)) < n_clusters:
        raise ValueError('Fewer distinct health profiles than requested clusters.')
    model = KMeans(n_clusters=n_clusters, random_state=42, n_init=10)
    labels = model.fit_predict(scaled) + 1
    assignments = frame[['player_id', 'name']].assign(cluster=labels)
    profiles = frame[fields].assign(cluster=labels).groupby('cluster').mean()
    overall, spread = frame[fields].mean(), frame[fields].std().replace(0, np.nan)
    summaries = {}
    for cluster, row in profiles.iterrows():
        differences = ((row - overall) / spread).dropna()
        strongest = differences.abs().nlargest(3).index
        summaries[int(cluster)] = '; '.join(f'{"higher" if differences[f] > 0 else "lower"} average {f}' for f in strongest) + ' relative to this roster.'
    components = min(2, scaled.shape[1])
    coordinates = PCA(n_components=components).fit_transform(scaled)
    assignments['PC1'] = coordinates[:, 0]
    assignments['PC2'] = coordinates[:, 1] if components == 2 else 0.0
    return {'assignments': assignments, 'profiles': profiles, 'summaries': summaries,
            'features': fields, 'model': model, 'preprocess': preprocess}
