import pandas as pd
import plotly.express as px
import streamlit as st
from ml.train import readiness, train_model, load_artifact


def render(session):
    st.title("Model Analysis")
    statuses = readiness(session)
    injury, performance = st.tabs(["Injury classification", "Performance regression"])
    for task, tab in (("injury", injury), ("performance", performance)):
        with tab:
            status = statuses[task]
            st.subheader("Dataset readiness")
            st.json({key: value for key, value in status.items() if key not in ("missing_fraction", "reasons")})
            for reason in status["reasons"]:
                st.warning(reason)
            with st.expander("Missing feature values"):
                st.dataframe(pd.DataFrame([{"Feature": key, "Missing fraction": value}
                                          for key, value in status["missing_fraction"].items()]), hide_index=True, width="stretch")
            if st.button(f"Train {task} model", key=f"train_{task}", icon=":material/model_training:", disabled=not status["ready"]):
                with st.spinner("Comparing models and evaluating the held-out test period..."):
                    outcome = train_model(session, task)
                if outcome.trained:
                    st.success(outcome.message)
                else:
                    st.error(outcome.message)
            artifact = load_artifact(session, task)
            if artifact is None:
                st.info(f"No trained {task} model for the current dataset.")
                continue
            metadata = artifact["metadata"]
            st.subheader(metadata["best_model"])
            st.write(f"Target: {metadata['target']}")
            st.write(f"Selection: {metadata['selection_metric']}")
            st.caption(f"Trained: {metadata['trained_at']}")
            st.dataframe(pd.DataFrame(metadata["date_ranges"], index=["First date", "Last date"]).T, width="stretch")
            st.subheader("Validation comparison")
            st.dataframe(metadata["comparison"], hide_index=True, width="stretch")
            st.subheader("Held-out test metrics")
            st.json({key: value for key, value in metadata["test_metrics"].items() if key != "confusion_matrix"})
            if task == "injury":
                matrix = metadata["test_metrics"]["confusion_matrix"]
                st.plotly_chart(px.imshow(matrix, x=["Predicted no injury", "Predicted injury"],
                                          y=["Actual no injury", "Actual injury"], text_auto=True,
                                          color_continuous_scale="Greens"), width="stretch")
            st.subheader("Global feature importance")
            importance = pd.DataFrame(metadata["top_model_contributors"])
            st.plotly_chart(px.bar(importance.head(15).sort_values("absolute_value"), x="absolute_value", y="feature",
                                  orientation="h", color_discrete_sequence=["#16806a"]), width="stretch")
            with st.expander("Features and evaluation examples"):
                st.write(metadata["features"])
                st.dataframe(metadata["prediction_examples"], hide_index=True, width="stretch")
