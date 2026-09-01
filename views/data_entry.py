from __future__ import annotations

from datetime import date

import pandas as pd
import streamlit as st
from sqlalchemy import select
from sqlalchemy.orm import Session

from database.models import MatchRecord, NutritionRecord, Player, RecoveryRecord, TrainingSession
from services.data_entry_service import (
    POSITION_CHOICES,
    add_match_record,
    add_nutrition_record,
    add_recovery_record,
    add_training_session,
    add_wellness_checkin,
    create_player,
    delete_player,
    delete_record,
    update_player,
    update_recovery_record,
    update_training_session,
)
from services.player_service import get_players
from utils.ui import page_header


def _player_select(session: Session, label: str = "Player", key: str = "player_select") -> Player | None:
    players = get_players(session)
    if not players:
        st.info("Add a player first.")
        return None
    return st.selectbox(
        label,
        players,
        format_func=lambda p: f"#{p.jersey_number} {p.name} - {p.position}",
        key=key,
    )


def _show_errors(errors: list[str]) -> None:
    for error in errors:
        st.error(error)


def _recent_dataframe(records: list[object], columns: list[str]) -> pd.DataFrame:
    rows = []
    for record in records:
        row = {column: getattr(record, column) for column in columns}
        row["id"] = record.id
        rows.append(row)
    return pd.DataFrame(rows)


def render(session: Session) -> None:
    page_header("Data Entry", "Manual updates for players, training, recovery, matches, nutrition and wellness.")
    st.caption("Submissions validate inputs, save to the database and refresh the analytics pipeline.")
    tab_player, tab_training, tab_recovery, tab_match, tab_nutrition, tab_wellness, tab_records = st.tabs(
        ["Player", "Training", "Recovery", "Match", "Nutrition", "Wellness", "Records"]
    )

    with tab_player:
        mode = st.radio("Mode", ["Add Player", "Edit Player", "Delete Player"], horizontal=True)
        if mode == "Add Player":
            with st.form("add_player_form"):
                name = st.text_input("Player name")
                col_a, col_b, col_c = st.columns(3)
                age = col_a.number_input("Age", 15, 45, 22)
                position = col_b.selectbox("Position", POSITION_CHOICES)
                jersey = col_c.number_input("Jersey number", 1, 99, 26)
                col_d, col_e, col_f = st.columns(3)
                height = col_d.number_input("Height cm", 140.0, 220.0, 180.0)
                weight = col_e.number_input("Weight kg", 45.0, 120.0, 74.0)
                foot = col_f.selectbox("Preferred foot", ["Right", "Left", "Both"])
                nationality = st.text_input("Nationality", "Not recorded")
                with st.expander("Physical and football attributes"):
                    sprint_speed = st.slider("Sprint speed km/h", 20.0, 38.0, 30.0)
                    passing = st.slider("Passing", 0, 100, 70)
                    shooting = st.slider("Shooting", 0, 100, 65)
                    tackling = st.slider("Tackling", 0, 100, 65)
                    previous_injuries = st.number_input("Previous injuries", 0, 20, 0)
                submitted = st.form_submit_button("Add Player", type="primary")
            if submitted:
                if not name.strip():
                    st.error("Player name is required.")
                else:
                    ok, errors = create_player(session, {
                        "name": name.strip(),
                        "age": int(age),
                        "position": position,
                        "jersey_number": int(jersey),
                        "height_cm": float(height),
                        "weight_kg": float(weight),
                        "preferred_foot": foot,
                        "nationality": nationality.strip() or "Not recorded",
                        "sprint_speed": float(sprint_speed),
                        "passing": float(passing),
                        "shooting": float(shooting),
                        "tackling": float(tackling),
                        "previous_injuries": int(previous_injuries),
                    })
                    st.success("Player added.") if ok else _show_errors(errors)

        elif mode == "Edit Player":
            player = _player_select(session, "Player to edit", key="edit_player_select")
            if player:
                with st.form("edit_player_form"):
                    name = st.text_input("Player name", player.name)
                    col_a, col_b, col_c = st.columns(3)
                    age = col_a.number_input("Age", 15, 45, player.age)
                    position = col_b.selectbox("Position", POSITION_CHOICES, index=POSITION_CHOICES.index(player.position) if player.position in POSITION_CHOICES else 0)
                    jersey = col_c.number_input("Jersey number", 1, 99, player.jersey_number)
                    col_d, col_e, col_f = st.columns(3)
                    height = col_d.number_input("Height cm", 140.0, 220.0, player.height_cm)
                    weight = col_e.number_input("Weight kg", 45.0, 120.0, player.weight_kg)
                    foot_options = ["Right", "Left", "Both"]
                    foot = col_f.selectbox("Preferred foot", foot_options, index=foot_options.index(player.preferred_foot) if player.preferred_foot in foot_options else 0)
                    status = st.selectbox("Squad status", ["Active", "Managed Load", "Injured", "Unavailable"], index=0 if player.squad_status not in ["Managed Load", "Injured", "Unavailable"] else ["Active", "Managed Load", "Injured", "Unavailable"].index(player.squad_status))
                    submitted = st.form_submit_button("Save Changes", type="primary")
                if submitted:
                    ok, errors = update_player(session, player, {
                        "name": name.strip(),
                        "age": int(age),
                        "position": position,
                        "jersey_number": int(jersey),
                        "height_cm": float(height),
                        "weight_kg": float(weight),
                        "preferred_foot": foot,
                        "squad_status": status,
                    })
                    st.success("Player updated.") if ok else _show_errors(errors)

        else:
            player = _player_select(session, "Player to delete", key="delete_player_select")
            confirm = st.checkbox("I understand this will delete the player and related records.")
            if st.button("Delete Player", disabled=not confirm, type="primary") and player:
                delete_player(session, player)
                st.success("Player deleted.")
                st.rerun()

    with tab_training:
        player = _player_select(session, key="training_player_select")
        if player:
            with st.form("training_form"):
                col_a, col_b, col_c = st.columns(3)
                training_date = col_a.date_input("Date", value=date.today(), key="training_date")
                session_type = col_b.selectbox("Training type", ["Tactical", "Strength", "Recovery", "Conditioning", "Match Prep", "Small-Sided Games"])
                duration = col_c.number_input("Duration min", 0.0, 180.0, 75.0, key="training_duration")
                col_d, col_e, col_f = st.columns(3)
                intensity = col_d.slider("Intensity", 0.0, 100.0, 70.0, key="training_intensity")
                rpe = col_e.slider("RPE", 0.0, 10.0, 6.0, key="training_rpe")
                distance = col_f.number_input("Distance km", 0.0, 18.0, 7.0, key="training_distance")
                with st.expander("Load details"):
                    sprint = st.number_input("Sprint distance m", 0.0, 1600.0, 450.0, key="training_sprint")
                    high_speed = st.number_input("High-speed running m", 0.0, 2600.0, 800.0, key="training_hsr")
                    accelerations = st.number_input("Accelerations", 0, 120, 24, key="training_acc")
                    decelerations = st.number_input("Decelerations", 0, 120, 22, key="training_dec")
                    avg_hr = st.number_input("Average heart rate", 40.0, 220.0, 145.0, key="training_avg_hr")
                    max_hr = st.number_input("Maximum heart rate", 40.0, 230.0, 178.0, key="training_max_hr")
                submitted = st.form_submit_button("Save Training", type="primary")
            if submitted:
                ok, errors = add_training_session(session, player, {
                    "date": training_date,
                    "session_type": session_type,
                    "duration_min": float(duration),
                    "intensity": float(intensity),
                    "rpe": float(rpe),
                    "distance_km": float(distance),
                    "sprint_distance_m": float(sprint),
                    "high_speed_running_m": float(high_speed),
                    "accelerations": int(accelerations),
                    "decelerations": int(decelerations),
                    "average_hr": float(avg_hr),
                    "max_hr": float(max_hr),
                })
                st.success("Training saved. Workload, fatigue, risk and alerts were updated.") if ok else _show_errors(errors)

    with tab_recovery:
        player = _player_select(session, key="recovery_player_select")
        if player:
            with st.form("recovery_form"):
                recovery_date = st.date_input("Date", value=date.today(), key="recovery_date")
                col_a, col_b, col_c = st.columns(3)
                sleep = col_a.number_input("Sleep hours", 0.0, 14.0, 7.5, key="recovery_sleep")
                sleep_quality = col_b.slider("Sleep quality", 0.0, 100.0, 78.0, key="recovery_sleep_quality")
                hrv = col_c.number_input("HRV", 20.0, 130.0, 75.0, key="recovery_hrv")
                col_d, col_e, col_f = st.columns(3)
                resting_hr = col_d.number_input("Resting HR", 30.0, 110.0, float(player.resting_hr), key="recovery_rhr")
                hydration = col_e.slider("Hydration", 0.0, 100.0, 82.0, key="recovery_hydration")
                soreness = col_f.slider("Muscle soreness", 0.0, 100.0, 32.0, key="recovery_soreness")
                col_g, col_h = st.columns(2)
                stress = col_g.slider("Stress", 0.0, 100.0, 25.0, key="recovery_stress")
                mood = col_h.slider("Mood", 0.0, 100.0, 80.0, key="recovery_mood")
                recovery_session = st.checkbox("Recovery session")
                rest_day = st.checkbox("Rest day")
                submitted = st.form_submit_button("Save Recovery", type="primary")
            if submitted:
                ok, errors = add_recovery_record(session, player, {
                    "date": recovery_date,
                    "sleep_hours": float(sleep),
                    "sleep_quality": float(sleep_quality),
                    "hrv": float(hrv),
                    "resting_hr": float(resting_hr),
                    "hydration": float(hydration),
                    "muscle_soreness": float(soreness),
                    "stress": float(stress),
                    "mood": float(mood),
                    "recovery_session": bool(recovery_session),
                    "rest_day": bool(rest_day),
                })
                st.success("Recovery saved. Recovery score, fatigue, risk and alerts were updated.") if ok else _show_errors(errors)

    with tab_match:
        player = _player_select(session, key="match_player_select")
        if player:
            with st.form("match_form"):
                col_a, col_b, col_c = st.columns(3)
                match_date = col_a.date_input("Match date", value=date.today())
                opponent = col_b.text_input("Opponent", "Opponent FC")
                result = col_c.selectbox("Result", ["Win", "Draw", "Loss", "Not recorded"])
                col_d, col_e, col_f = st.columns(3)
                minutes = col_d.number_input("Minutes played", 0, 130, 90)
                goals = col_e.number_input("Goals", 0, 10, 0)
                assists = col_f.number_input("Assists", 0, 10, 0)
                with st.expander("Match statistics"):
                    shots = st.number_input("Shots", 0, 20, 2, key="match_shots")
                    shots_on_target = st.number_input("Shots on target", 0, 20, 1, key="match_sot")
                    passes = st.number_input("Passes", 0, 160, 45, key="match_passes")
                    pass_accuracy = st.slider("Pass accuracy", 0.0, 100.0, 82.0, key="match_pass_acc")
                    key_passes = st.number_input("Key passes", 0, 20, 1, key="match_key_passes")
                    tackles = st.number_input("Tackles", 0, 25, 2, key="match_tackles")
                    interceptions = st.number_input("Interceptions", 0, 25, 1, key="match_interceptions")
                    duels_won = st.number_input("Duels won", 0, 35, 4, key="match_duels")
                    distance = st.number_input("Distance km", 0.0, 16.0, 10.2, key="match_distance")
                    sprint = st.number_input("Sprint distance m", 0.0, 1400.0, 520.0, key="match_sprint")
                    high_speed = st.number_input("High-speed running m", 0.0, 2400.0, 1050.0, key="match_hsr")
                    progressive = st.number_input("Progressive passes", 0, 40, 4, key="match_progressive")
                    rating = st.slider("Player rating", 0.0, 10.0, 7.0, key="match_rating")
                submitted = st.form_submit_button("Save Match", type="primary")
            if submitted:
                ok, errors = add_match_record(session, player, {
                    "date": match_date,
                    "opponent": opponent.strip() or "Opponent FC",
                    "result": result,
                    "minutes_played": int(minutes),
                    "goals": int(goals),
                    "assists": int(assists),
                    "shots": int(shots),
                    "shots_on_target": int(shots_on_target),
                    "passes": int(passes),
                    "pass_accuracy": float(pass_accuracy),
                    "key_passes": int(key_passes),
                    "tackles": int(tackles),
                    "interceptions": int(interceptions),
                    "duels_won": int(duels_won),
                    "distance_km": float(distance),
                    "sprint_distance_m": float(sprint),
                    "high_speed_running_m": float(high_speed),
                    "progressive_passes": int(progressive),
                    "player_rating": float(rating),
                })
                st.success("Match saved. Performance and form inputs were updated.") if ok else _show_errors(errors)

    with tab_nutrition:
        player = _player_select(session, key="nutrition_player_select")
        if player:
            with st.form("nutrition_form"):
                nutrition_date = st.date_input("Date", value=date.today(), key="nutrition_date")
                col_a, col_b, col_c = st.columns(3)
                calories = col_a.number_input("Calories", 0.0, 7000.0, 3400.0)
                protein = col_b.number_input("Protein g", 0.0, 350.0, round(player.weight_kg * 2.0, 1))
                carbs = col_c.number_input("Carbohydrates g", 0.0, 900.0, 420.0)
                col_d, col_e, col_f = st.columns(3)
                fats = col_d.number_input("Fats g", 0.0, 260.0, 95.0)
                water = col_e.number_input("Water L", 0.0, 10.0, 3.8)
                timing = col_f.slider("Meal timing", 0.0, 100.0, 80.0)
                submitted = st.form_submit_button("Save Nutrition", type="primary")
            if submitted:
                ok, errors = add_nutrition_record(session, player, {
                    "date": nutrition_date,
                    "calories": float(calories),
                    "protein_g": float(protein),
                    "carbohydrates_g": float(carbs),
                    "fats_g": float(fats),
                    "water_l": float(water),
                    "meal_timing_score": float(timing),
                })
                st.success("Nutrition saved.") if ok else _show_errors(errors)

    with tab_wellness:
        player = _player_select(session, key="wellness_player_select")
        if player:
            with st.form("wellness_form"):
                wellness_date = st.date_input("Date", value=date.today(), key="wellness_date")
                col_a, col_b, col_c = st.columns(3)
                sleep = col_a.number_input("Sleep hours", 0.0, 14.0, 6.8, key="wellness_sleep")
                sleep_quality = col_b.slider("Sleep quality /10", 0.0, 10.0, 7.0, key="wellness_sleep_quality")
                soreness = col_c.slider("Soreness /10", 0.0, 10.0, 4.0, key="wellness_soreness")
                col_d, col_e, col_f = st.columns(3)
                fatigue = col_d.slider("Fatigue /10", 0.0, 10.0, 4.0, key="wellness_fatigue")
                mood = col_e.slider("Mood /10", 0.0, 10.0, 7.0, key="wellness_mood")
                stress = col_f.slider("Stress /10", 0.0, 10.0, 3.0, key="wellness_stress")
                col_g, col_h = st.columns(2)
                hydration = col_g.number_input("Hydration L", 0.0, 10.0, 3.0, key="wellness_hydration")
                rpe = col_h.slider("RPE", 0.0, 10.0, 5.0, key="wellness_rpe")
                submitted = st.form_submit_button("Save Wellness Check-In", type="primary")
            if submitted:
                ok, errors = add_wellness_checkin(session, player, {
                    "date": wellness_date,
                    "sleep_hours": float(sleep),
                    "sleep_quality_10": float(sleep_quality),
                    "muscle_soreness_10": float(soreness),
                    "fatigue_10": float(fatigue),
                    "mood_10": float(mood),
                    "stress_10": float(stress),
                    "hydration_l": float(hydration),
                    "rpe": float(rpe),
                })
                st.success("Wellness check-in saved and recovery analytics updated.") if ok else _show_errors(errors)

    with tab_records:
        player = _player_select(session, "Review records for", key="records_player_select")
        if player:
            record_type = st.selectbox("Record type", ["Training", "Recovery", "Match", "Nutrition"])
            model_map = {
                "Training": TrainingSession,
                "Recovery": RecoveryRecord,
                "Match": MatchRecord,
                "Nutrition": NutritionRecord,
            }
            model = model_map[record_type]
            records = list(session.scalars(
                select(model).where(model.player_id == player.id).order_by(model.date.desc()).limit(20)
            ))
            if not records:
                st.info("No records found.")
            else:
                visible_columns = {
                    "Training": ["date", "duration_min", "rpe", "training_load", "fatigue_score", "injury_risk_pct"],
                    "Recovery": ["date", "sleep_hours", "sleep_quality", "recovery_score", "muscle_soreness"],
                    "Match": ["date", "opponent", "result", "minutes_played", "goals", "assists", "performance_score"],
                    "Nutrition": ["date", "calories", "protein_g", "carbohydrates_g", "water_l"],
                }[record_type]
                st.dataframe(_recent_dataframe(records, visible_columns), use_container_width=True, hide_index=True)
                selected_id = st.selectbox("Selected record", [r.id for r in records])
                record = next(r for r in records if r.id == selected_id)
                if record_type in {"Training", "Recovery"}:
                    with st.expander("Edit selected record"):
                        if record_type == "Training":
                            with st.form("edit_training"):
                                edited_date = st.date_input("Date", record.date, key="edit_training_date")
                                duration = st.number_input("Duration min", 0.0, 180.0, record.duration_min, key="edit_training_duration")
                                rpe = st.slider("RPE", 0.0, 10.0, record.rpe, key="edit_training_rpe")
                                distance = st.number_input("Distance km", 0.0, 18.0, record.distance_km, key="edit_training_distance")
                                submitted = st.form_submit_button("Save Edit")
                            if submitted:
                                ok, errors = update_training_session(session, record, {
                                    "date": edited_date,
                                    "session_type": record.session_type,
                                    "duration_min": float(duration),
                                    "intensity": record.intensity,
                                    "rpe": float(rpe),
                                    "distance_km": float(distance),
                                    "sprint_distance_m": record.sprint_distance_m,
                                    "high_speed_running_m": record.high_speed_running_m,
                                    "accelerations": record.accelerations,
                                    "decelerations": record.decelerations,
                                    "average_hr": record.average_hr,
                                    "max_hr": record.max_hr,
                                })
                                st.success("Training record updated.") if ok else _show_errors(errors)
                        else:
                            with st.form("edit_recovery"):
                                edited_date = st.date_input("Date", record.date, key="edit_recovery_date")
                                sleep = st.number_input("Sleep hours", 0.0, 14.0, record.sleep_hours, key="edit_recovery_sleep")
                                quality = st.slider("Sleep quality", 0.0, 100.0, record.sleep_quality, key="edit_recovery_quality")
                                soreness = st.slider("Muscle soreness", 0.0, 100.0, record.muscle_soreness, key="edit_recovery_soreness")
                                submitted = st.form_submit_button("Save Edit")
                            if submitted:
                                ok, errors = update_recovery_record(session, record, {
                                    "date": edited_date,
                                    "sleep_hours": float(sleep),
                                    "sleep_quality": float(quality),
                                    "hrv": record.hrv,
                                    "resting_hr": record.resting_hr,
                                    "hydration": record.hydration,
                                    "muscle_soreness": float(soreness),
                                    "stress": record.stress,
                                    "mood": record.mood,
                                    "recovery_session": record.recovery_session,
                                    "rest_day": record.rest_day,
                                })
                                st.success("Recovery record updated.") if ok else _show_errors(errors)
                confirm = st.checkbox("Confirm delete selected record")
                if st.button("Delete Record", disabled=not confirm):
                    delete_record(session, record)
                    st.success("Record deleted.")
                    st.rerun()

