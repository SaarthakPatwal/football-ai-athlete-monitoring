# Football ML Monitoring System — current project

This existing Streamlit app keeps Injury Prediction, Performance Prediction, and Health as separate analyses. It starts with no automatic imports or training. The eight CSVs in `demo_data_final/` are **fictional demonstration data — not real athlete or medical data**. Uploading them is a manual step.

| Page | What it does |
| --- | --- |
| Dashboard | Shows raw table counts, Injury/Performance readiness and available predictions, plus a small independent Health summary when a usable Health model and recent records exist. |
| Data | Downloads templates; maps, validates, previews, confirms, imports, manually enters, displays and exports records. |
| Players | Shows one player's stored training, recovery, injury and match history, engineered Injury/Performance snapshot and those predictions. |
| ML Predictions | Shows Injury probabilities and next-match rating predictions from saved models. |
| Model Analysis | Explicitly trains and evaluates Injury and Performance models. |
| Health | Three internal tabs: Health Monitoring, Health Trends and Health Clustering. |

The flow is `CSV → mapping/validation → existing SQLite database → dated historical features → train/validation/test → saved supervised model → prediction`. Health Trends uses descriptive statistics; Health Clustering uses unsupervised K-Means. There is no combined health/injury/performance score.

Start with [QUICK_START.md](QUICK_START.md), then use [DEMO_GUIDE.md](DEMO_GUIDE.md) for the complete upload order. [DATA_DICTIONARY.md](DATA_DICTIONARY.md) lists every accepted CSV column. No demo values are medical diagnoses or validated clearance decisions.
