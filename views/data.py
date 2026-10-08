from datetime import date
import pandas as pd
import streamlit as st
from services.validation_service import SCHEMAS, LIMITS, INTEGERS, detect_dataset, detect_column_mapping, apply_mapping, template_csv
from services.data_service import validate_input, import_records, read_dataset
from utils.ui import show_table

UNITS = {"height": "cm", "weight": "kg", "duration_min": "minutes", "distance": "km",
         "sprint_distance": "m", "high_speed_distance": "m", "sleep_hours": "hours",
         "hrv": "ms", "resting_hr": "bpm", "sleep_quality": "0-10", "soreness": "0-10", "stress": "0-10", "rpe": "0-10", "rating": "0-10"}


def save(session, frame, key, valid_only=False):
    outcome = import_records(session, frame, key, valid_only)
    if outcome.imported_rows:
        session.commit()
        st.session_state["data_notice"] = f"Saved {outcome.imported_rows} {key} record(s)."
        st.rerun()
    if outcome.problems:
        st.dataframe(pd.DataFrame(outcome.problems), hide_index=True, width="stretch")


def upload(session):
    st.caption("Upload Health CSV, Medical Tests CSV or Health Events CSV here. Select the matching template/dataset and review validation before import.")
    template = st.selectbox("CSV template", list(SCHEMAS), format_func=str.title)
    st.download_button("Download template", template_csv(template), f"{template}_template.csv",
                       mime="text/csv", icon=":material/download:")
    upload_label = {"health": "Upload Health CSV", "medical_tests": "Upload Medical Tests CSV",
                    "health_events": "Upload Health Events CSV"}.get(template, "CSV Upload")
    file = st.file_uploader(upload_label, type=["csv"])
    if file is None:
        return
    try:
        raw = pd.read_csv(file, dtype=str, keep_default_na=False)
    except (pd.errors.ParserError, pd.errors.EmptyDataError, UnicodeDecodeError) as exc:
        st.error(f"Could not read CSV: {exc}")
        return
    if raw.empty:
        st.info("The CSV contains no records.")
        return
    detected = detect_dataset(raw.columns)
    options = list(SCHEMAS)
    key = st.selectbox("Dataset", options, index=options.index(detected) if detected else options.index(template),
                       format_func=str.title, key=f"upload_dataset_{file.name}")
    if detected:
        st.caption(f"Detected dataset: {detected.title()}")
    else:
        st.warning("Dataset type is ambiguous. Select the dataset and review its columns.")
    schema = SCHEMAS[key]
    mapping, _ = detect_column_mapping(raw.columns, key)
    with st.expander("Column mapping", expanded=any(field not in mapping for field in schema.required)):
        selections = ["Not mapped", *raw.columns]
        edited = {}
        for field in schema.columns:
            selected = st.selectbox(field + (" *" if field in schema.required else ""), selections,
                                    index=selections.index(mapping[field]) if field in mapping else 0,
                                    key=f"map_{file.name}_{key}_{field}")
            if selected != "Not mapped":
                edited[field] = selected
    if len(set(edited.values())) < len(edited):
        st.error("Each input column can map to only one field.")
        return
    unmapped = [column for column in raw.columns if column not in edited.values()]
    if unmapped:
        st.warning("Unmapped columns will not be imported: " + ", ".join(unmapped))
    standard = apply_mapping(raw, edited, key)
    valid, problems = validate_input(session, standard, key)
    if problems:
        st.error(f"{len(problems)} validation issue(s).")
        st.dataframe(pd.DataFrame(problems), hide_index=True, width="stretch")
    if key == "medical_tests" and not valid.empty and valid[list(schema.optional)].isna().all(axis=1).any():
        st.warning("Some medical panels contain no measured tests. These rows add no medical feature values.")
    st.subheader(f"Valid rows: {len(valid)} / {len(raw)}")
    show_table(valid)
    if valid.empty:
        return
    valid_only = st.checkbox("Import valid rows only", value=False) if problems else False
    confirmed = st.checkbox("Confirm import of the previewed rows", key=f"confirm_{file.name}_{key}")
    if st.button("Import", icon=":material/upload:", disabled=not confirmed or (bool(problems) and not valid_only)):
        save(session, standard, key, valid_only)


def manual(session):
    key = st.selectbox("Dataset", list(SCHEMAS), format_func=str.title, key="manual_dataset")
    schema = SCHEMAS[key]
    roster = read_dataset(session, "players")
    if key != "players" and roster.empty:
        st.info("Add players first.")
        return
    with st.form(f"manual_{key}", clear_on_submit=True):
        row = {}
        for index, field in enumerate(schema.columns):
            if index % 2 == 0:
                columns = st.columns(2)
            label = field.replace("_", " ").title()
            if field in UNITS:
                label += f" ({UNITS[field]})"
            if field in schema.optional:
                label += " (optional)"
            with columns[index % 2]:
                if field == "player_id" and key != "players":
                    names = dict(zip(roster.player_id, roster.name))
                    row[field] = st.selectbox(label, list(names), format_func=lambda value: f"{value} - {names[value]}", index=None)
                elif field in schema.date_columns:
                    row[field] = st.date_input(label, value=None, max_value=date.today())
                elif field in ("injury_occurred", "health_event"):
                    row[field] = st.selectbox(label, [False, True], index=None,
                                             format_func=lambda value: "Documented event" if value else "Confirmed no event")
                elif field in schema.numeric_columns:
                    low, high = LIMITS[field]
                    integer = field in INTEGERS
                    row[field] = st.number_input(label, value=None,
                                                 min_value=int(low) if integer else float(low),
                                                 max_value=int(high) if integer else float(high),
                                                 step=1 if integer else 0.1)
                else:
                    row[field] = st.text_input(label)
        submitted = st.form_submit_button("Save record", icon=":material/save:")
    if submitted:
        save(session, pd.DataFrame([row]), key)


def render(session):
    st.title("Data")
    if "data_notice" in st.session_state:
        st.success(st.session_state.pop("data_notice"))
    upload_tab, manual_tab, records_tab = st.tabs(["CSV Upload", "Manual Entry", "Records"])
    with upload_tab:
        upload(session)
    with manual_tab:
        manual(session)
    with records_tab:
        key = st.selectbox("Stored dataset", list(SCHEMAS), format_func=str.title)
        frame = read_dataset(session, key)
        show_table(frame)
        if not frame.empty:
            st.download_button("Export records", frame.to_csv(index=False), f"{key}.csv",
                               mime="text/csv", icon=":material/download:")
    with st.expander("Data definitions"):
        st.write("Training distance is in km; sprint and high-speed distance are in m. Sleep quality, soreness, stress and RPE use a 0-10 scale. Match ratings use 0-10. Dates use YYYY-MM-DD. One record per player and date in each dataset; training records represent daily totals.")
        st.write("Health uses the same daily units as Recovery. Fatigue, energy and hydration use 0-10; higher hydration means greater hydration. Body fat/SpO2 are %, pressure mmHg, temperature Celsius. Medical units and limits are in DATA_DICTIONARY.md and HEALTH_MODULE.md. Health Events is an independent daily documented-event log: 1 = new event; 0 = confirmed no event. Demo Health CSVs are fictional demonstration data, not real medical data.")
        st.write("Injuries is a daily outcome log: 1 records an injury onset; 0 confirms no new injury.")

