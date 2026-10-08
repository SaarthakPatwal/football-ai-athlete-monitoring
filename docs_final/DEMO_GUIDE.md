# Manual demonstration guide

The eight CSVs in `demo_data_final/` are **fictional demonstration data — not real athlete or medical data**. They cover 18 linked players from 2026-04-10 through 2026-10-06. The app does not load them automatically. This cleanup did not alter your existing database or models. Import into a fresh database so previously uploaded player/date rows do not collide with this new set.

To use a separate empty demonstration database through the app's existing configuration, stop Streamlit and start it from the project directory with an **unused** filename:

```powershell
$env:FOOTBALL_ML_DATABASE_URL = 'sqlite:///data/final_demo_empty.db'
python -m streamlit run app.py
```

The app creates empty tables at startup. If you prefer to replace the usual `data/football_ml.db`, stop Streamlit and back up that database and `data/model_artifacts/` before starting again; the recoverable procedure is in [QUICK_START.md](QUICK_START.md). Neither option is performed by these documentation or CSV files.

## Upload order

On **Data → CSV Upload**, select each file, inspect the detected dataset and column mapping, review the valid-row preview and any errors, tick **Confirm import of the previewed rows**, then click **Import**. The eight files map to their same-named dataset choices, except `health.csv` uses **Health**. Do not import the same file twice into one database.

| Order | File | Expected rows | Why it is needed |
| --- | --- | ---: | --- |
| 1 | `players.csv` | 18 | Every other CSV references these IDs. |
| 2 | `training.csv` | 2,197 | Injury/Performance workloads. |
| 3 | `recovery.csv` | 3,240 | Injury/Performance recovery history. |
| 4 | `injuries.csv` | 3,240 | Explicit daily Injury outcomes, including zeros. |
| 5 | `matches.csv` | 420 | Actual match-rating targets and prior-match history. |
| 6 | `health.csv` | 3,240 | Daily Health measurements and trends. |
| 7 | `medical_tests.csv` | 126 | Less frequent, partly missing laboratory panels. |
| 8 | `health_events.csv` | 3,240 | Explicit daily Health outcomes, including zeros, required for supervised Health Monitoring. |

Check **Data → Records** and Dashboard counts after upload. There are 24 authored new injury onsets and 30 separately authored Health events. Their file rows cover the entire period, while model training builds fewer usable windows after feature and split rules. No event is generated from an HRV, workload or sleep cutoff.

## Show the three supervised and descriptive views

1. Open **Model Analysis → Injury classification**. Review readiness, click **Train injury model**, and inspect all three validation candidates, the chosen algorithm and held-out classification metrics. Then open **Performance regression**, click **Train performance model**, and inspect its validation and held-out regression metrics.
2. Open **ML Predictions**, choose prediction date **2026-10-07**, and compare Injury probabilities and next-match ratings across players. Do not promise that every Low/Medium/High band will be populated; actual outputs depend on the fitted model and test data.
3. Open **Health → Health Monitoring**, review the record counts and confirmed labelled windows, then click **Train Health Model**. Inspect its candidate comparison, selected model, confusion matrix and test metrics. Choose a player and prediction date **2026-10-07**, then click **Predict Health Risk**. Compare several players' model probabilities and their feature sensitivity displays.
4. Open **Health Trends**. Compare P001 (stable), P006/P014 (improving), P007/P011/P017 (declining), and P008/P018 (variable). Expand Heart, Sleep, Recovery, Hydration and Medical tests to show observed/rolling charts. These are statistics, not an extra prediction model.
5. Open **Health Clustering**. Set profile date **2026-10-07** and three clusters, then **Run Health Clustering**. Show assignments, observed cluster means, relative descriptions and PCA plot. Cluster numbers are descriptive IDs, not health grades.
6. Return to Dashboard. Its Health summary uses the current date and may show no eligible recent history when this dated fictional dataset is old. The selected historical date on Health remains usable if it is after the model's fit cutoff.

The profiles deliberately include stable and resilient players, high workload, poor recovery, combined burden, low workload, improving and declining trajectories, inconsistent days, varied match skill and trends, injury-free players, and authored events on some stable players. This creates overlap rather than a perfectly separable target. No disease diagnosis or clinical decision should be inferred from the demo.
