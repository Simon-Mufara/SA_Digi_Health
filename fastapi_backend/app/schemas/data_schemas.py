"""
Pydantic schemas for YARA API endpoints.
"""
from datetime import datetime
from typing import List, Optional, Any
from pydantic import BaseModel, Field


# ============ Staff Schemas ============
class StaffBase(BaseModel):
    staff_id: str
    assigned_role: str


class StaffCreate(StaffBase):
    password: str


class StaffResponse(StaffBase):
    id: int
    is_active: bool
    created_at: datetime
    last_login: Optional[datetime] = None

    class Config:
        from_attributes = True


# ============ Patient Schemas ============
class PatientBase(BaseModel):
    name: Optional[str] = None
    identifier: Optional[str] = None
    gender: Optional[str] = None


class PatientCreate(PatientBase):
    date_of_birth: Optional[datetime] = None


class PatientSearchResult(BaseModel):
    id: int
    patient_uuid: str
    name: Optional[str] = None  # May be masked to initials for clinicians
    identifier: Optional[str] = None
    gender: Optional[str] = None
    last_visit: Optional[datetime] = None

    class Config:
        from_attributes = True


class PatientResponse(PatientBase):
    id: int
    patient_uuid: str
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


# ============ Vital Schemas ============
class VitalBase(BaseModel):
    bp_systolic: Optional[int] = None
    bp_diastolic: Optional[int] = None
    temperature_c: Optional[float] = None
    o2_sat: Optional[int] = None
    weight_kg: Optional[float] = None


class VitalCreate(VitalBase):
    visit_id: int


class VitalResponse(VitalBase):
    id: int
    visit_id: int
    recorded_at: datetime
    recorded_by: Optional[int] = None

    class Config:
        from_attributes = True


# ============ Note Schemas ============
class NoteBase(BaseModel):
    content: str


class NoteCreate(NoteBase):
    visit_id: int


class NoteResponse(NoteBase):
    id: int
    visit_id: int
    author_staff_id: Optional[int] = None
    created_at: datetime

    class Config:
        from_attributes = True


# ============ Visit Schemas ============
class VisitBase(BaseModel):
    visit_reason: Optional[str] = None
    status: str = "waiting"


class VisitCreate(VisitBase):
    patient_id: int


class VisitResponse(VisitBase):
    id: int
    patient_id: int
    session_token: str
    created_at: datetime
    created_by_staff_id: Optional[int] = None

    class Config:
        from_attributes = True


class VisitWithDetails(VisitResponse):
    """Visit with nested vitals and notes for timeline endpoint."""
    vitals: List[VitalResponse] = []
    notes: List[NoteResponse] = []


class VisitTimeline(BaseModel):
    """Patient visit timeline response."""
    patient_id: int
    patient_uuid: str
    total_visits: int
    visits: List[VisitWithDetails]


# ============ AI Summary Schemas ============
class AISummaryResponse(BaseModel):
    patient_id: int
    summary: str
    generated_at: datetime
    model_version: str
    cached: bool = False

    class Config:
        from_attributes = True


# ============ Research/Cohort Schemas ============
class CohortGroup(BaseModel):
    """Single cohort group with de-identified stats."""
    age_group: str
    gender: Optional[str] = None
    visit_reason: Optional[str] = None
    count: int
    
    # Only included in export
    avg_bp_systolic: Optional[float] = None
    avg_bp_diastolic: Optional[float] = None
    avg_o2_sat: Optional[float] = None


class CohortResponse(BaseModel):
    """Response for /research/cohorts endpoint."""
    total_patients: int
    total_visits: int
    cohorts: List[CohortGroup]
    k_anonymity_threshold: int = 5
    suppressed_groups: int = 0


class ResearchExportRow(BaseModel):
    """Row in research export CSV."""
    age_group: str
    gender: str
    visit_reason: str
    visit_count: int
    avg_bp_systolic: Optional[float] = None
    avg_bp_diastolic: Optional[float] = None
    avg_o2_sat: Optional[float] = None


# ============ Audit Event Schemas ============
class AuditEventCreate(BaseModel):
    staff_id: Optional[str] = None
    action: str
    outcome: str
    ip_address: Optional[str] = None
    role: Optional[str] = None
    details: Optional[dict] = None


class AuditEventResponse(AuditEventCreate):
    id: int
    created_at: datetime

    class Config:
        from_attributes = True


# ============ Face Embedding Schemas ============
class FaceEmbeddingResponse(BaseModel):
    id: int
    patient_id: int
    model: str
    captured_at: datetime
    image_hash: Optional[str] = None
    # Note: embedding not included for security

    class Config:
        from_attributes = True
