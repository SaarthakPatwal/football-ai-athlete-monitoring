# Supervised models and inference

All three tasks train only after an explicit button click. The application compares real scikit-learn estimators; it does not compute labels from a risk threshold. Model features, fitted preprocessing, comparison results, evaluation metrics and source signatures are retained with saved artifacts.

| Task | Candidate estimators | Validation selection | Prediction |
| --- | --- | --- | --- |
| Injury Prediction | Logistic Regression (`class_weight=balanced`); Random Forest Classifier (`n_estimators=100`, `min_samples_leaf=2`, balanced); Gradient Boosting Classifier | Maximize `0.7 × recall + 0.3 × F1` | `predict_proba` of injury onset within seven days |
| Performance Prediction | Linear Regression; Random Forest Regressor (`n_estimators=100`, `min_samples_leaf=2`); Gradient Boosting Regressor | Lowest MAE | Predicted next-match rating |
| Health Monitoring | Logistic Regression (`class_weight=balanced`); Random Forest Classifier (`n_estimators=100`, `min_samples_leaf=2`, balanced); Gradient Boosting Classifier | Maximize `0.7 × recall + 0.3 × F1` | `predict_proba` of a documented health event within seven days |

Tree estimators use `random_state=42`. The original Injury/Performance numeric pipeline median-imputes values, retains empty feature slots, adds missing indicators and scales; position is one-hot encoded with unknown categories tolerated. Health has only numeric features and uses median imputation, missing indicators and scaling. Each candidate's preprocessing fits only on its fitting data. The chosen algorithm is refit on retained train plus validation rows and tested once on the newest period.

Training readiness: Injury requires at least 40 usable samples, five positive windows, five recorded onsets, both classes, adequate workload/Recovery coverage and usable chronological partitions. Performance requires at least 35 samples, varying target ratings, prior match history, adequate workload/Recovery coverage and usable partitions. Health requires at least 40 usable windows, five documented events, both classes and usable partitions with both classes in train and validation. These minimums enable an educational demo; they do not establish statistical or clinical reliability.

The ML Predictions page displays Injury classifier probabilities as Low below 40%, Medium from 40% to below 70%, and High at least 70%. Health uses the same display bands in uppercase. These are presentation cutoffs, not clinical decisions or separate models. Performance shows the regressor's raw rating output. Backdated inference before outcomes used to fit an artifact is refused. Newer records can inform a prediction while unchanged original history preserves artifact compatibility.

Model Analysis shows global feature importance: tree impurity importances or scaled linear coefficients. Health Monitoring additionally ranks a player's features by the change in model probability when each is replaced individually with its fitting-data median. Neither is a medical cause or a complete causal explanation. Health artifacts are separate under `data/model_artifacts/health/`; the original tasks use `data/model_artifacts/`.
