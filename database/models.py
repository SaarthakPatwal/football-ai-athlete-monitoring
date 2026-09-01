from __future__ import annotations

from sqlalchemy import Boolean, Date, Float, ForeignKey, Integer, String, Text
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


class Base(DeclarativeBase):
    pass


class Player(Base):
    __tablename__ = "players"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(120), nullable=False, index=True)
    age: Mapped[int] = mapped_column(Integer, nullable=False)
    position: Mapped[str] = mapped_column(String(8), nullable=False, index=True)
    jersey_number: Mapped[int] = mapped_column(Integer, nullable=False, unique=True)
    height_cm: Mapped[float] = mapped_column(Float, nullable=False)
    weight_kg: Mapped[float] = mapped_column(Float, nullable=False)
    preferred_foot: Mapped[str] = mapped_column(String(12), nullable=False)
    nationality: Mapped[str] = mapped_column(String(80), nullable=False)
    squad_status: Mapped[str] = mapped_column(String(40), nullable=False, default="Active")

    sprint_speed: Mapped[float] = mapped_column(Float, nullable=False)
    acceleration: Mapped[float] = mapped_column(Float, nullable=False)
    vo2_max: Mapped[float] = mapped_column(Float, nullable=False)
    resting_hr: Mapped[float] = mapped_column(Float, nullable=False)
    max_hr: Mapped[float] = mapped_column(Float, nullable=False)
    body_fat_pct: Mapped[float] = mapped_column(Float, nullable=False)
    strength: Mapped[float] = mapped_column(Float, nullable=False)
    agility: Mapped[float] = mapped_column(Float, nullable=False)

    passing: Mapped[float] = mapped_column(Float, nullable=False)
    shooting: Mapped[float] = mapped_column(Float, nullable=False)
    dribbling: Mapped[float] = mapped_column(Float, nullable=False)
    tackling: Mapped[float] = mapped_column(Float, nullable=False)
    crossing: Mapped[float] = mapped_column(Float, nullable=False)
    positioning: Mapped[float] = mapped_column(Float, nullable=False)
    vision: Mapped[float] = mapped_column(Float, nullable=False)
    decision_making: Mapped[float] = mapped_column(Float, nullable=False)
    pace: Mapped[float] = mapped_column(Float, nullable=False)

    matches_played: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    minutes_played: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    goals: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    assists: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    previous_injuries: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    historical_performance: Mapped[float] = mapped_column(Float, nullable=False)
    historical_workload: Mapped[float] = mapped_column(Float, nullable=False)

    training_sessions = relationship("TrainingSession", back_populates="player", cascade="all, delete-orphan")
    recovery_records = relationship("RecoveryRecord", back_populates="player", cascade="all, delete-orphan")
    match_records = relationship("MatchRecord", back_populates="player", cascade="all, delete-orphan")
    nutrition_records = relationship("NutritionRecord", back_populates="player", cascade="all, delete-orphan")
    wellness_checkins = relationship("WellnessCheckIn", back_populates="player", cascade="all, delete-orphan")
    injuries = relationship("InjuryHistory", back_populates="player", cascade="all, delete-orphan")
    alerts = relationship("Alert", back_populates="player", cascade="all, delete-orphan")


class TrainingSession(Base):
    __tablename__ = "training_sessions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    player_id: Mapped[int] = mapped_column(ForeignKey("players.id"), index=True)
    date: Mapped[Date] = mapped_column(Date, nullable=False, index=True)
    session_type: Mapped[str] = mapped_column(String(60), nullable=False)
    duration_min: Mapped[float] = mapped_column(Float, nullable=False)
    intensity: Mapped[float] = mapped_column(Float, nullable=False)
    rpe: Mapped[float] = mapped_column(Float, nullable=False)
    distance_km: Mapped[float] = mapped_column(Float, nullable=False)
    sprint_distance_m: Mapped[float] = mapped_column(Float, nullable=False)
    high_speed_running_m: Mapped[float] = mapped_column(Float, nullable=False)
    accelerations: Mapped[int] = mapped_column(Integer, nullable=False)
    decelerations: Mapped[int] = mapped_column(Integer, nullable=False)
    average_hr: Mapped[float] = mapped_column(Float, nullable=False)
    max_hr: Mapped[float] = mapped_column(Float, nullable=False)
    training_load: Mapped[float] = mapped_column(Float, nullable=False)
    acute_workload: Mapped[float] = mapped_column(Float, nullable=False)
    baseline_workload: Mapped[float] = mapped_column(Float, nullable=False)
    workload_change_pct: Mapped[float] = mapped_column(Float, nullable=False)
    fatigue_score: Mapped[float] = mapped_column(Float, nullable=False)
    fitness_score: Mapped[float] = mapped_column(Float, nullable=False)
    injury_risk_pct: Mapped[float] = mapped_column(Float, nullable=False)

    player = relationship("Player", back_populates="training_sessions")


class RecoveryRecord(Base):
    __tablename__ = "recovery_records"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    player_id: Mapped[int] = mapped_column(ForeignKey("players.id"), index=True)
    date: Mapped[Date] = mapped_column(Date, nullable=False, index=True)
    sleep_hours: Mapped[float] = mapped_column(Float, nullable=False)
    sleep_quality: Mapped[float] = mapped_column(Float, nullable=False)
    hrv: Mapped[float] = mapped_column(Float, nullable=False)
    resting_hr: Mapped[float] = mapped_column(Float, nullable=False)
    hydration: Mapped[float] = mapped_column(Float, nullable=False)
    muscle_soreness: Mapped[float] = mapped_column(Float, nullable=False)
    stress: Mapped[float] = mapped_column(Float, nullable=False)
    mood: Mapped[float] = mapped_column(Float, nullable=False)
    recovery_session: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    rest_day: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    recovery_score: Mapped[float] = mapped_column(Float, nullable=False)

    player = relationship("Player", back_populates="recovery_records")


class MatchRecord(Base):
    __tablename__ = "match_records"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    player_id: Mapped[int] = mapped_column(ForeignKey("players.id"), index=True)
    match_id: Mapped[str] = mapped_column(String(40), nullable=False, index=True)
    opponent: Mapped[str] = mapped_column(String(80), nullable=False)
    result: Mapped[str] = mapped_column(String(20), nullable=False, default="Not recorded")
    date: Mapped[Date] = mapped_column(Date, nullable=False, index=True)
    minutes_played: Mapped[int] = mapped_column(Integer, nullable=False)
    goals: Mapped[int] = mapped_column(Integer, nullable=False)
    assists: Mapped[int] = mapped_column(Integer, nullable=False)
    shots: Mapped[int] = mapped_column(Integer, nullable=False)
    shots_on_target: Mapped[int] = mapped_column(Integer, nullable=False)
    passes: Mapped[int] = mapped_column(Integer, nullable=False)
    pass_accuracy: Mapped[float] = mapped_column(Float, nullable=False)
    key_passes: Mapped[int] = mapped_column(Integer, nullable=False)
    tackles: Mapped[int] = mapped_column(Integer, nullable=False)
    interceptions: Mapped[int] = mapped_column(Integer, nullable=False)
    duels_won: Mapped[int] = mapped_column(Integer, nullable=False)
    distance_km: Mapped[float] = mapped_column(Float, nullable=False)
    sprint_distance_m: Mapped[float] = mapped_column(Float, nullable=False)
    high_speed_running_m: Mapped[float] = mapped_column(Float, nullable=False)
    progressive_passes: Mapped[int] = mapped_column(Integer, nullable=False)
    player_rating: Mapped[float] = mapped_column(Float, nullable=False)
    performance_score: Mapped[float] = mapped_column(Float, nullable=False)

    player = relationship("Player", back_populates="match_records")


class NutritionRecord(Base):
    __tablename__ = "nutrition_records"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    player_id: Mapped[int] = mapped_column(ForeignKey("players.id"), index=True)
    date: Mapped[Date] = mapped_column(Date, nullable=False, index=True)
    calories: Mapped[float] = mapped_column(Float, nullable=False)
    protein_g: Mapped[float] = mapped_column(Float, nullable=False)
    carbohydrates_g: Mapped[float] = mapped_column(Float, nullable=False)
    fats_g: Mapped[float] = mapped_column(Float, nullable=False)
    water_l: Mapped[float] = mapped_column(Float, nullable=False)
    meal_timing_score: Mapped[float] = mapped_column(Float, nullable=False)

    player = relationship("Player", back_populates="nutrition_records")


class WellnessCheckIn(Base):
    __tablename__ = "wellness_checkins"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    player_id: Mapped[int] = mapped_column(ForeignKey("players.id"), index=True)
    date: Mapped[Date] = mapped_column(Date, nullable=False, index=True)
    sleep_hours: Mapped[float] = mapped_column(Float, nullable=False)
    sleep_quality_10: Mapped[float] = mapped_column(Float, nullable=False)
    muscle_soreness_10: Mapped[float] = mapped_column(Float, nullable=False)
    fatigue_10: Mapped[float] = mapped_column(Float, nullable=False)
    mood_10: Mapped[float] = mapped_column(Float, nullable=False)
    stress_10: Mapped[float] = mapped_column(Float, nullable=False)
    hydration_l: Mapped[float] = mapped_column(Float, nullable=False)
    rpe: Mapped[float] = mapped_column(Float, nullable=False)

    player = relationship("Player", back_populates="wellness_checkins")


class InjuryHistory(Base):
    __tablename__ = "injury_history"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    player_id: Mapped[int] = mapped_column(ForeignKey("players.id"), index=True)
    date: Mapped[Date] = mapped_column(Date, nullable=False)
    injury_type: Mapped[str] = mapped_column(String(80), nullable=False)
    severity: Mapped[str] = mapped_column(String(40), nullable=False)
    days_missed: Mapped[int] = mapped_column(Integer, nullable=False)

    player = relationship("Player", back_populates="injuries")


class Alert(Base):
    __tablename__ = "alerts"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    player_id: Mapped[int] = mapped_column(ForeignKey("players.id"), nullable=True, index=True)
    date: Mapped[Date] = mapped_column(Date, nullable=False, index=True)
    priority: Mapped[str] = mapped_column(String(20), nullable=False)
    category: Mapped[str] = mapped_column(String(40), nullable=False)
    message: Mapped[str] = mapped_column(Text, nullable=False)
    reason: Mapped[str] = mapped_column(Text, nullable=False)

    player = relationship("Player", back_populates="alerts")
