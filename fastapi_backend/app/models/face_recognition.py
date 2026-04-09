from datetime import datetime

from sqlalchemy import DateTime, Float, ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


class BiometricProfile(Base):
    __tablename__ = "biometrics"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    patient_uuid: Mapped[str] = mapped_column(ForeignKey("patients.patient_uuid", ondelete="CASCADE"), index=True, nullable=False)
    face_biometric_hash: Mapped[str] = mapped_column(String(64), unique=True, index=True, nullable=False)
    embedding_vector: Mapped[str] = mapped_column(Text, nullable=False)
    vector_ref: Mapped[str | None] = mapped_column(String(128), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)

    patient = relationship("Patient", back_populates="biometrics")


class FaceRecognitionEvent(Base):
    __tablename__ = "face_recognition_events"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    patient_uuid: Mapped[str | None] = mapped_column(ForeignKey("patients.patient_uuid", ondelete="SET NULL"), nullable=True)
    visit_session_id: Mapped[str | None] = mapped_column(String(64), index=True, nullable=True)
    confidence: Mapped[float] = mapped_column(Float, nullable=False)
    result: Mapped[str] = mapped_column(String(32), nullable=False)
    capture_context: Mapped[str] = mapped_column(String(32), nullable=False)
    captured_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)