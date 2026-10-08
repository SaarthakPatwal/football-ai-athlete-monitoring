# System architecture

`app.py` routes Streamlit's sidebar to Dashboard, Data, Players, ML Predictions, Model Analysis and Health. The Health page has Monitoring, Trends and Clustering tabs.

`database/database.py` opens the existing `data/football_ml.db` by default. `FOOTBALL_ML_DATABASE_URL` can select another database. SQLAlchemy defines eight tables in `database/models.py`: `players`, `training`, `recovery`, `injuries`, `matches`, `health_records`, `medical_tests`, `health_events`. New table creation is additive; the app does not seed records. All dated tables have a player foreign key, a unique player/date pair and player/date indexes. Upload key `health` maps to `health_records`.

`services/validation_service.py` defines the exact schemas, aliases, ISO-date parsing, finite-number ranges, Boolean parsing, duplicate checks and cross-field rules. `views/data.py` provides template selection, column mapping, validation preview and explicit import confirmation. `services/data_service.py` performs the same transactional import for CSVs and manual forms. An invalid batch writes nothing unless the user selects valid rows only. Unknown player IDs and duplicate player/date rows are rejected. Optional medical values stay NULL.

`services/feature_service.py` builds Injury/Performance history; `services/health_service.py` builds separate Health history, trend statistics and K-Means profiles. Both exclude measurements on or after a prediction date. `ml/train.py` and `ml/health.py` compare candidates with a chronological split. `ml/predict.py` and `ml/health.py` reuse fitted preprocessing at inference. Models train only after button clicks.

Injury/Performance `.joblib` pipelines and `.json` metadata live directly in `data/model_artifacts/`; Health artifacts live in its `health/` child directory. Source signatures keep the Health datasets independent of the original five datasets. Historical edits can invalidate a model; retraining is then required. Files in `demo_data_final/` are never read automatically by application startup.

See [FEATURE_ENGINEERING.md](FEATURE_ENGINEERING.md), [ML_MODELS.md](ML_MODELS.md), and [EVALUATION.md](EVALUATION.md) for the actual calculations and controls.
