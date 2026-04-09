from datetime import datetime
from uuid import uuid4

from sqlalchemy import DateTime, ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


class ClinicalRecord(Base):
    __tablename__ = "clinical_records"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    record_uuid: Mapped[str] = mapped_column(String(64), unique=True, index=True, default=lambda: str(uuid4()))
    patient_uuid: Mapped[str] = mapped_column(ForeignKey("patients.patient_uuid", ondelete="CASCADE"), index=True, nullable=False)
    diagnosis: Mapped[str] = mapped_column(String(500), nullable=False)
    medication: Mapped[str] = mapped_column(String(500), nullable=False)
    notes: Mapped[str] = mapped_column(Text, nullable=False)
    attending_doctor: Mapped[str] = mapped_column(String(120), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)

    patient = relationship("Patient", back_populates="clinical_records")