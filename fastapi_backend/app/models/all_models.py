"""
Complete SQLAlchemy models for YARA Hospital System.
Includes all tables with proper relationships, indexes, and constraints.
"""
from datetime import datetime
from typing import List, Optional
from uuid import uuid4

from sqlalchemy import (
    Boolean, DateTime, Float, ForeignKey, Index, Integer, 
    String, Text, JSON, Enum as SQLEnum
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship
import enum

from app.core.database_async import Base


# Enums
class StaffRole(str, enum.Enum):
    DOCTOR = "doctor"
    CLINICIAN = "clinician"
    ADMIN = "admin"
    SECURITY_OFFICER = "security_officer"
    RESEARCHER = "researcher"


class VisitStatus(str, enum.Enum):
    WAITING = "waiting"
    ACTIVE = "active"
    COMPLETE = "complete"
    DISCHARGED = "discharged"


class AuditOutcome(str, enum.Enum):
    SUCCESS = "success"
    FAIL = "fail"
    ROLE_MISMATCH = "role_mismatch"


# Staff table
class Staff(Base):
    __tablename__ = "staff"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    staff_id: Mapped[str] = mapped_column(String(100), unique=True, index=True, nullable=False)
    hashed_password: Mapped[str] = mapped_column(String(255), nullable=False)
    assigned_role: Mapped[str] = mapped_column(String(32), nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)
    last_login: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)

    # Relationships
    created_visits: Mapped[List["Visit"]] = relationship(
        "Visit", 
        back_populates="created_by_staff",
        foreign_keys="Visit.created_by_staff_id"
    )
    recorded_vitals: Mapped[List["Vital"]] = relationship(
        "Vital",
        back_populates="recorded_by_staff",
        foreign_keys="Vital.recorded_by"
    )
    authored_notes: Mapped[List["Note"]] = relationship(
        "Note",
        back_populates="author_staff",
        foreign_keys="Note.author_staff_id"
    )


# Patient table
class Patient(Base):
    __tablename__ = "patients"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    patient_uuid: Mapped[str] = mapped_column(
        String(64), unique=True, index=True, 
        default=lambda: str(uuid4())
    )
    face_embedding_id: Mapped[Optional[int]] = mapped_column(
        Integer, ForeignKey("face_embeddings.id", ondelete="SET NULL"), 
        nullable=True
    )
    name: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    identifier: Mapped[Optional[str]] = mapped_column(String(50), nullable=True, index=True)
    gender: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)
    date_of_birth: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False
    )

    # Relationships
    face_embedding: Mapped[Optional["FaceEmbedding"]] = relationship(
        "FaceEmbedding",
        back_populates="patient",
        foreign_keys=[face_embedding_id],
        uselist=False
    )
    all_embeddings: Mapped[List["FaceEmbedding"]] = relationship(
        "FaceEmbedding",
        back_populates="patient_owner",
        foreign_keys="FaceEmbedding.patient_id",
        cascade="all, delete-orphan"
    )
    visits: Mapped[List["Visit"]] = relationship(
        "Visit", back_populates="patient", cascade="all, delete-orphan"
    )
    ai_summaries: Mapped[List["AISummary"]] = relationship(
        "AISummary", back_populates="patient", cascade="all, delete-orphan"
    )

    __table_args__ = (
        Index("ix_patients_identifier", "identifier"),
        Index("ix_patients_name_search", "name"),
    )


# Face Embeddings table
class FaceEmbedding(Base):
    __tablename__ = "face_embeddings"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    patient_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("patients.id", ondelete="CASCADE"), 
        nullable=False, index=True
    )
    embedding: Mapped[dict] = mapped_column(JSON, nullable=False)  # JSONB for PostgreSQL
    model: Mapped[str] = mapped_column(String(100), default="Facenet512", nullable=False)
    captured_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)
    image_hash: Mapped[Optional[str]] = mapped_column(String(64), nullable=True, unique=True)

    # Relationships
    patient: Mapped[Optional["Patient"]] = relationship(
        "Patient",
        back_populates="face_embedding",
        foreign_keys="Patient.face_embedding_id"
    )
    patient_owner: Mapped["Patient"] = relationship(
        "Patient",
        back_populates="all_embeddings",
        foreign_keys=[patient_id]
    )

    __table_args__ = (
        Index("ix_face_embeddings_patient_id", "patient_id"),
    )


# Visit table
class Visit(Base):
    __tablename__ = "visits"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    patient_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("patients.id", ondelete="CASCADE"), 
        nullable=False, index=True
    )
    session_token: Mapped[str] = mapped_column(
        String(128), unique=True, index=True, 
        default=lambda: f"VST-{uuid4().hex[:16].upper()}"
    )
    visit_reason: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    created_by_staff_id: Mapped[Optional[int]] = mapped_column(
        Integer, ForeignKey("staff.id", ondelete="SET NULL"), 
        nullable=True
    )
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)
    status: Mapped[str] = mapped_column(
        String(32), default=VisitStatus.WAITING.value, nullable=False
    )

    # Relationships
    patient: Mapped["Patient"] = relationship("Patient", back_populates="visits")
    created_by_staff: Mapped[Optional["Staff"]] = relationship(
        "Staff", back_populates="created_visits", foreign_keys=[created_by_staff_id]
    )
    vitals: Mapped[List["Vital"]] = relationship(
        "Vital", back_populates="visit", cascade="all, delete-orphan"
    )
    notes: Mapped[List["Note"]] = relationship(
        "Note", back_populates="visit", cascade="all, delete-orphan"
    )

    __table_args__ = (
        Index("ix_visits_patient_id", "patient_id"),
        Index("ix_visits_created_at", "created_at"),
        Index("ix_visits_status", "status"),
    )


# Vitals table
class Vital(Base):
    __tablename__ = "vitals"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    visit_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("visits.id", ondelete="CASCADE"), 
        nullable=False, index=True
    )
    bp_systolic: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    bp_diastolic: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    temperature_c: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    o2_sat: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    weight_kg: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    recorded_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)
    recorded_by: Mapped[Optional[int]] = mapped_column(
        Integer, ForeignKey("staff.id", ondelete="SET NULL"), 
        nullable=True
    )

    # Relationships
    visit: Mapped["Visit"] = relationship("Visit", back_populates="vitals")
    recorded_by_staff: Mapped[Optional["Staff"]] = relationship(
        "Staff", back_populates="recorded_vitals", foreign_keys=[recorded_by]
    )


# Notes table
class Note(Base):
    __tablename__ = "notes"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    visit_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("visits.id", ondelete="CASCADE"), 
        nullable=False, index=True
    )
    content: Mapped[str] = mapped_column(Text, nullable=False)
    author_staff_id: Mapped[Optional[int]] = mapped_column(
        Integer, ForeignKey("staff.id", ondelete="SET NULL"), 
        nullable=True
    )
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)

    # Relationships
    visit: Mapped["Visit"] = relationship("Visit", back_populates="notes")
    author_staff: Mapped[Optional["Staff"]] = relationship(
        "Staff", back_populates="authored_notes", foreign_keys=[author_staff_id]
    )


# Audit Events table
class AuditEvent(Base):
    __tablename__ = "audit_events"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    staff_id: Mapped[Optional[str]] = mapped_column(String(100), nullable=True, index=True)
    action: Mapped[str] = mapped_column(String(100), nullable=False)
    outcome: Mapped[str] = mapped_column(String(32), nullable=False)
    ip_address: Mapped[Optional[str]] = mapped_column(String(45), nullable=True)
    role: Mapped[Optional[str]] = mapped_column(String(32), nullable=True)
    details: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False, index=True)

    __table_args__ = (
        Index("ix_audit_events_created_at", "created_at"),
        Index("ix_audit_events_staff_id", "staff_id"),
        Index("ix_audit_events_action", "action"),
    )


# AI Summaries table
class AISummary(Base):
    __tablename__ = "ai_summaries"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    patient_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("patients.id", ondelete="CASCADE"), 
        nullable=False, index=True
    )
    summary_text: Mapped[str] = mapped_column(Text, nullable=False)
    generated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)
    model_version: Mapped[str] = mapped_column(String(100), default="gemini-1.5-flash", nullable=False)

    # Relationships
    patient: Mapped["Patient"] = relationship("Patient", back_populates="ai_summaries")

    __table_args__ = (
        Index("ix_ai_summaries_patient_generated", "patient_id", "generated_at"),
    )
