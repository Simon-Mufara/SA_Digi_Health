from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel, ConfigDict, field_validator


class PatientCreate(BaseModel):
    name: str | None = None
    identifier: str | None = None
    gender: str | None = None

    @field_validator("identifier")
    @classmethod
    def validate_sa_identifier(cls, value: str | None) -> str | None:
        if value is None:
            return None
        cleaned = value.strip()
        if not cleaned:
            return None
        if not cleaned.isdigit() or len(cleaned) != 13:
            raise ValueError("South African ID must be exactly 13 digits.")
        return cleaned


class PatientRead(BaseModel):
    patient_uuid: str
    display_name: str | None
    masked_identifier: str | None
    gender: str | None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class PatientSearchResult(BaseModel):
    """Result item for patient search endpoint."""
    patient_uuid: str
    display_name: str | None
    masked_identifier: str | None
    gender: str | None
    last_visit: datetime | None = None

    model_config = ConfigDict(from_attributes=True)


class PatientTimelineVisit(BaseModel):
    visit_session_id: str
    reason: str | None
    status: str
    entry_time: datetime
    doctor_interaction_time: datetime | None
    outcome: str | None


class SmartPatientProfile(BaseModel):
    patient_uuid: str
    display_name: str | None
    masked_identifier: str | None
    gender: str | None
    conditions: list[str]
    medications: list[str]
    visit_count: int
    last_visit_at: datetime | None
    ai_summary: str
    risk_factors: list[str]
    alerts: list[str]
