from datetime import datetime
from uuid import uuid4

from sqlalchemy import DateTime, ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


class VisitSession(Base):
    __tablename__ = "visits"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    visit_session_id: Mapped[str] = mapped_column(String(64), unique=True, index=True, default=lambda: str(uuid4()))
    patient_uuid: Mapped[str] = mapped_column(ForeignKey("patients.patient_uuid", ondelete="CASCADE"), index=True, nullable=False)
    reason: Mapped[str | None] = mapped_column(String(255), nullable=True)
    status: Mapped[str] = mapped_column(String(32), default="initiated", nullable=False)
    entry_time: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)
    doctor_interaction_time: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    outcome: Mapped[str | None] = mapped_column(Text, nullable=True)

    patient = relationship("Patient", back_populates="visits")