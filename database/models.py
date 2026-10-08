from __future__ import annotations

from datetime import date
from sqlalchemy import Boolean, Date, Float, ForeignKey, Integer, String, UniqueConstraint
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class Base(DeclarativeBase):
    pass


class Player(Base):
    __tablename__ = "players"
    player_id: Mapped[str] = mapped_column(String(60), primary_key=True)
    name: Mapped[str] = mapped_column(String(120), nullable=False)
    age: Mapped[int] = mapped_column(Integer, nullable=False)
    position: Mapped[str] = mapped_column(String(30), nullable=False)
    height: Mapped[float | None] = mapped_column(Float)
    weight: Mapped[float | None] = mapped_column(Float)


class TrainingSession(Base):
    __tablename__ = "training"
    __table_args__ = (UniqueConstraint("player_id", "date"),)
    id: Mapped[int] = mapped_column(primary_key=True)
    player_id: Mapped[str] = mapped_column(ForeignKey("players.player_id"), index=True)
    date: Mapped[date] = mapped_column(Date, index=True)
    duration_min: Mapped[float] = mapped_column(Float)
    rpe: Mapped[float] = mapped_column(Float)
    distance: Mapped[float] = mapped_column(Float)
    sprint_distance: Mapped[float] = mapped_column(Float)
    high_speed_distance: Mapped[float] = mapped_column(Float)


class RecoveryRecord(Base):
    __tablename__ = "recovery"
    __table_args__ = (UniqueConstraint("player_id", "date"),)
    id: Mapped[int] = mapped_column(primary_key=True)
    player_id: Mapped[str] = mapped_column(ForeignKey("players.player_id"), index=True)
    date: Mapped[date] = mapped_column(Date, index=True)
    sleep_hours: Mapped[float] = mapped_column(Float)
    sleep_quality: Mapped[float] = mapped_column(Float)
    hrv: Mapped[float] = mapped_column(Float)
    resting_hr: Mapped[float] = mapped_column(Float)
    soreness: Mapped[float] = mapped_column(Float)
    stress: Mapped[float] = mapped_column(Float)


class InjuryHistory(Base):
    __tablename__ = "injuries"
    __table_args__ = (UniqueConstraint("player_id", "injury_date"),)
    id: Mapped[int] = mapped_column(primary_key=True)
    player_id: Mapped[str] = mapped_column(ForeignKey("players.player_id"), index=True)
    injury_date: Mapped[date] = mapped_column(Date, index=True)
    injury_occurred: Mapped[bool] = mapped_column(Boolean)
    injury_type: Mapped[str | None] = mapped_column(String(100))
    days_missed: Mapped[int | None] = mapped_column(Integer)


class MatchRecord(Base):
    __tablename__ = "matches"
    __table_args__ = (UniqueConstraint("player_id", "match_date"),)
    id: Mapped[int] = mapped_column(primary_key=True)
    player_id: Mapped[str] = mapped_column(ForeignKey("players.player_id"), index=True)
    match_date: Mapped[date] = mapped_column(Date, index=True)
    minutes_played: Mapped[int] = mapped_column(Integer)
    goals: Mapped[int] = mapped_column(Integer)
    assists: Mapped[int] = mapped_column(Integer)
    shots: Mapped[int] = mapped_column(Integer)
    passes_completed: Mapped[int] = mapped_column(Integer)
    key_passes: Mapped[int] = mapped_column(Integer)
    rating: Mapped[float] = mapped_column(Float)



class HealthRecord(Base):
    __tablename__ = "health_records"
    __table_args__ = (UniqueConstraint("player_id", "date"),)
    id: Mapped[int] = mapped_column(primary_key=True)
    player_id: Mapped[str] = mapped_column(ForeignKey("players.player_id"), index=True)
    date: Mapped[date] = mapped_column(Date, index=True)
    resting_hr: Mapped[float] = mapped_column(Float)
    hrv: Mapped[float] = mapped_column(Float)
    sleep_hours: Mapped[float] = mapped_column(Float)
    sleep_quality: Mapped[float] = mapped_column(Float)
    soreness: Mapped[float] = mapped_column(Float)
    fatigue: Mapped[float] = mapped_column(Float)
    stress: Mapped[float] = mapped_column(Float)
    energy_level: Mapped[float] = mapped_column(Float)
    hydration_status: Mapped[float] = mapped_column(Float)
    weight: Mapped[float | None] = mapped_column(Float)
    body_fat_pct: Mapped[float | None] = mapped_column(Float)
    blood_pressure_sys: Mapped[float | None] = mapped_column(Float)
    blood_pressure_dia: Mapped[float | None] = mapped_column(Float)
    oxygen_saturation: Mapped[float | None] = mapped_column(Float)
    body_temperature: Mapped[float | None] = mapped_column(Float)


class MedicalTest(Base):
    __tablename__ = "medical_tests"
    __table_args__ = (UniqueConstraint("player_id", "test_date"),)
    id: Mapped[int] = mapped_column(primary_key=True)
    player_id: Mapped[str] = mapped_column(ForeignKey("players.player_id"), index=True)
    test_date: Mapped[date] = mapped_column(Date, index=True)
    hemoglobin: Mapped[float | None] = mapped_column(Float)
    hematocrit: Mapped[float | None] = mapped_column(Float)
    wbc_count: Mapped[float | None] = mapped_column(Float)
    platelet_count: Mapped[float | None] = mapped_column(Float)
    ferritin: Mapped[float | None] = mapped_column(Float)
    serum_iron: Mapped[float | None] = mapped_column(Float)
    vitamin_d: Mapped[float | None] = mapped_column(Float)
    vitamin_b12: Mapped[float | None] = mapped_column(Float)
    glucose: Mapped[float | None] = mapped_column(Float)
    creatinine: Mapped[float | None] = mapped_column(Float)
    crp: Mapped[float | None] = mapped_column(Float)


class HealthEvent(Base):
    __tablename__ = "health_events"
    __table_args__ = (UniqueConstraint("player_id", "event_date"),)
    id: Mapped[int] = mapped_column(primary_key=True)
    player_id: Mapped[str] = mapped_column(ForeignKey("players.player_id"), index=True)
    event_date: Mapped[date] = mapped_column(Date, index=True)
    health_event: Mapped[bool] = mapped_column(Boolean)

DATASETS = {"players": Player, "training": TrainingSession, "recovery": RecoveryRecord,
            "injuries": InjuryHistory, "matches": MatchRecord, "health": HealthRecord,
            "medical_tests": MedicalTest, "health_events": HealthEvent}
