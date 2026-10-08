# Quick start

1. From the project folder, install requirements if needed:

   ```powershell
   python -m pip install -r requirements.txt
   ```

2. Use a **fresh empty database** for this demo. The default is `data/football_ml.db`, which may still contain your previous uploads. A safe isolated run uses an unused filename with the existing `FOOTBALL_ML_DATABASE_URL` setting before starting Streamlit:

   ```powershell
   $env:FOOTBALL_ML_DATABASE_URL = 'sqlite:///data/final_demo_empty.db'
   python -m streamlit run app.py
   ```

   If you want to replace the default database instead, stop Streamlit and move `data/football_ml.db` and `data/model_artifacts/` to timestamped backups before restarting. This keeps old records and models recoverable. This cleanup did not move or delete either location. After the demo, `Remove-Item Env:FOOTBALL_ML_DATABASE_URL` returns a PowerShell session to the default database setting.

3. Confirm the Dashboard's eight table counts are zero. Go to **Data → CSV Upload** and import the eight files from `demo_data_final/` in the order in [DEMO_GUIDE.md](DEMO_GUIDE.md). Confirm each preview and inspect any validation errors. Players must be first. `health_events.csv` is required for a supervised Health model; Health Trends and Clustering can use the other Health files without it.

4. Train Injury and Performance on **Model Analysis**, then Health on **Health → Health Monitoring**. Training is never automatic. Use **2026-10-07** as the historical prediction/profile date for these files, then inspect ML Predictions, Health Trends and Health Clustering.

The CSVs are fictional, cannot be used as clinical evidence, and are not imported by this cleanup. See [PROJECT_OVERVIEW.md](PROJECT_OVERVIEW.md) for the current pages and [DATA_DICTIONARY.md](DATA_DICTIONARY.md) for exact headers and units.
