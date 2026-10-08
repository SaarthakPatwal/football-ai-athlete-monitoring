from datetime import date, timedelta
import pandas as pd
import plotly.express as px
import streamlit as st
from services.health_service import HealthHistory, trend_analysis, cluster_health
from services.health_schema import MEDICAL_FIELDS
from ml.health import assess_health, train_health_model, load_health_artifact, predict_health, explain_prediction

@st.cache_data(show_spinner=False, max_entries=8)
def labelled_frame(frames):
    return HealthHistory(None, frames=frames).training_frame()


def monitoring(session, history):
    health = history.frames['health']
    cols = st.columns(4)
    cols[0].metric('Health records', len(health))
    cols[1].metric('Players with health data', health.player_id.nunique())
    cols[2].metric('Daily outcome observations', len(history.frames['health_events']))
    cols[3].metric('Medical tests', len(history.frames['medical_tests']))
    if not health.empty:
        st.caption(f'Health date range: {health.date.min()} to {health.date.max()}')
    frame = labelled_frame(history.frames)
    status = assess_health(history, frame)
    st.write(f"Available labelled outcomes: {status['usable_windows']} windows ({status['positive_windows']} positive, {status['negative_windows']} confirmed negative).")
    for reason in status['reasons']:
        st.info(reason)
    st.caption('Upload health_events.csv to provide Health outcome labels.')
    if st.button('Train Health Model', disabled=not status['ready']):
        with st.spinner('Comparing models and evaluating test results...'):
            result = train_health_model(session)
        (st.success if result.trained else st.error)(result.message)
    artifact = load_health_artifact(session)
    if artifact is None:
        st.info('No trained Health model for this dataset.')
        return
    metadata = artifact['metadata']
    st.subheader('Model evaluation')
    st.write(f"Selected model: {metadata['best_model']}")
    st.caption(metadata['methodology'])
    st.caption(metadata['selection_metric'])
    st.dataframe(metadata['comparison'], hide_index=True, width='stretch')
    st.write('Held-out test results')
    st.dataframe(pd.DataFrame([{k: v for k, v in metadata['test_metrics'].items() if k != 'confusion_matrix'}]), hide_index=True)
    st.plotly_chart(px.imshow(metadata['test_metrics']['confusion_matrix'], text_auto=True,
                             x=['Predicted no event', 'Predicted event'], y=['Actual no event', 'Actual event']), width='stretch')
    with st.expander('Features and split dates'):
        st.json({'features': metadata['features'], 'date_ranges': metadata['date_ranges'], 'partitions': metadata['partitions']})
    roster = history.frames['players']
    player_id = st.selectbox('Player', roster.player_id.tolist(), key='health_predict_player')
    point = st.date_input('Prediction date', value=health.date.max() + timedelta(days=1), max_value=date.today() + timedelta(days=1), key='health_prediction_date')
    if st.button('Predict Health Risk'):
        if point < date.fromisoformat(metadata['fitted_through']):
            st.warning('Select a later prediction date.')
            return
        output = predict_health(session, point, artifact)
        selected = output[output.player_id == player_id] if not output.empty else output
        if selected.empty:
            st.info('Insufficient recent health measurements for this player and date.')
            return
        row = selected.iloc[0]
        st.metric('Health Risk', row.risk)
        st.metric('Probability', f'{row.probability:.1%}')
        st.dataframe(explain_prediction(artifact, history.snapshot(player_id, point)), hide_index=True)


def trends(history):
    roster = history.frames['players']
    if roster.empty:
        st.info('Upload players and health measurements to view trends.')
        return
    player = st.selectbox('Player', roster.player_id.tolist(), key='health_trends_player')
    groups = {'Heart': ['resting_hr', 'hrv'], 'Sleep': ['sleep_hours', 'sleep_quality'],
              'Recovery': ['soreness', 'fatigue', 'stress', 'energy_level'], 'Hydration': ['hydration_status'],
              'Body': ['weight', 'body_fat_pct'], 'Vitals': ['blood_pressure_sys', 'blood_pressure_dia', 'oxygen_saturation', 'body_temperature'],
              'Medical tests': list(MEDICAL_FIELDS)}
    for group, fields in groups.items():
        medical = group == 'Medical tests'
        records = history.records('medical_tests' if medical else 'health', player)
        available = [field for field in fields if records[field].notna().any()]
        with st.expander(group, expanded=group == 'Heart'):
            if not available:
                st.info('No recorded measurements.')
            for field in available:
                chart, summary = trend_analysis(records, field, 'test_date' if medical else 'date', 90 if medical else 7)
                st.write(field.replace('_', ' ').title())
                st.dataframe(pd.DataFrame([summary]), hide_index=True)
                st.line_chart(chart)


def clustering(session, history):
    health = history.frames['health']
    count = st.selectbox('Number of clusters', [2, 3, 4, 5], index=1)
    point = st.date_input('Profile date', value=health.date.max() + timedelta(days=1) if len(health) else date.today(), max_value=date.today() + timedelta(days=1))
    if st.button('Run Health Clustering'):
        try:
            result = cluster_health(session, point, count)
        except ValueError as exc:
            st.info(str(exc))
            return
        st.dataframe(result['assignments'][['player_id', 'name', 'cluster']], hide_index=True)
        st.subheader('Cluster profiles (observed means)')
        st.dataframe(result['profiles'])
        for cluster, summary in result['summaries'].items():
            st.write(f'Cluster {cluster}: {summary}')
        plotted = result['assignments'].assign(cluster=lambda f: f.cluster.astype(str))
        st.plotly_chart(px.scatter(plotted, x='PC1', y='PC2', color='cluster', hover_data=['player_id', 'name']), width='stretch')
        st.write('Features used:', result['features'])


def render(session):
    st.title('Health')
    history = HealthHistory(session)
    tabs = st.tabs(['Health Monitoring', 'Health Trends', 'Health Clustering'])
    with tabs[0]:
        monitoring(session, history)
    with tabs[1]:
        trends(history)
    with tabs[2]:
        clustering(session, history)


def dashboard_summary(session):
    st.subheader('Health Monitoring')
    artifact = load_health_artifact(session)
    if artifact is None:
        st.caption('No trained Health model. Upload Health data and train on the Health page.')
        return
    point = date.today()
    output = predict_health(session, point, artifact)
    if output.empty:
        st.caption('No eligible recent health history for today.')
        return
    highest = output.sort_values('probability', ascending=False).iloc[0]
    st.write(f"Players with elevated predicted health risk (MEDIUM/HIGH): {int((output.risk != 'LOW').sum())}")
    st.caption(f'As of {point} · Highest-risk player: {highest.player_id} — {highest.probability:.1%}')
