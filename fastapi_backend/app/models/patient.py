from datetime import datetime
from uuid import uuid4

from sqlalchemy import DateTime, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


class Patient(Base):
    __tablename__ = "patients"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    patient_uuid: Mapped[str] = mapped_column(String(64), unique=True, index=True, default=lambda: str(uuid4()))
    encrypted_name: Mapped[str | None] = mapped_column(String(2000), nullable=True)
    name_hash: Mapped[str | None] = mapped_column(String(64), index=True, nullable=True)
    encrypted_identifier: Mapped[str | None] = mapped_column(String(2000), nullable=True)
    identifier_hash: Mapped[str | None] = mapped_column(String(64), index=True, nullable=True)
    gender: Mapped[str | None] = mapped_column(String(20), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)

    biometrics = relationship("BiometricProfile", back_populates="patient", cascade="all, delete-orphan")
    clinical_records = relationship("ClinicalRecord", back_populates="patient", cascade="all, delete-orphan")
    visits = relationship("VisitSession", back_populates="patient", cascade="all, delete-orphan")