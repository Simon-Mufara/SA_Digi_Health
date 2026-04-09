"""
Visit timeline and management endpoints for YARA.
"""
from datetime import datetime
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Path, Query, status, Body
from pydantic import BaseModel, ConfigDict
from sqlalchemy import desc, func
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.dependencies import require_role
from app.models.staff import Staff
from app.models.patient import Patient
from app.models.visit_session import VisitSession
from app.schemas.common import UserRole
from app.schemas.visit import VisitOutcomeUpdate, VisitSessionRead
from app.services.visit_service import VisitService

router = APIRouter(prefix="/visits", tags=["visits"])


# Response models for timeline
class VitalResponse(BaseModel):
    id: int
    bp_systolic: Optional[int] = None
    bp_diastolic: Optional[int] = None
    temperature_c: Optional[float] = None
    o2_sat: Optional[int] = None
    weight_kg: Optional[float] = None
    recorded_at: datetime

    model_config = ConfigDict(from_attributes=True)


class NoteResponse(BaseModel):
    id: int
    content: str
    created_at: datetime
    author_staff_id: Optional[int] = None

    model_config = ConfigDict(from_attributes=True)


class VisitWithDetails(BaseModel):
    visit_session_id: str
    reason: Optional[str] = None
    status: str
    entry_time: datetime
    doctor_interaction_time: Optional[datetime] = None
    outcome: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)


class VisitTimelineResponse(BaseModel):
    patient_uuid: str
    total_visits: int
    visits: List[VisitWithDetails]


@router.get("/{visit_session_id}", response_model=VisitSessionRead)
def get_visit(
    visit_session_id: str,
    db: Session = Depends(get_db),
    _: Staff = Depends(require_role(UserRole.SECURITY_OFFICER, UserRole.DOCTOR, UserRole.CLINICIAN)),
):
    """Get a single visit by session ID."""
    try:
        visit = VisitService.get_by_session_id(db, visit_session_id)
        return VisitSessionRead(
            visit_session_id=visit.visit_session_id,
            patient_uuid=visit.patient_uuid,
            reason=visit.reason,
            status=visit.status,
            entry_time=visit.entry_time,
            doctor_interaction_time=visit.doctor_interaction_time,
            outcome=visit.outcome,
        )
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc


@router.patch("/{visit_session_id}/outcome", response_model=VisitSessionRead)
def update_outcome(
    visit_session_id: str,
    payload: VisitOutcomeUpdate,
    db: Session = Depends(get_db),
    _: Staff = Depends(require_role(UserRole.DOCTOR, UserRole.CLINICIAN)),
):
    """Update visit outcome/status."""
    try:
        visit = VisitService.complete_visit(db, visit_session_id, payload.outcome, payload.status)
        return VisitSessionRead(
            visit_session_id=visit.visit_session_id,
            patient_uuid=visit.patient_uuid,
            reason=visit.reason,
            status=visit.status,
            entry_time=visit.entry_time,
            doctor_interaction_time=visit.doctor_interaction_time,
            outcome=visit.outcome,
        )
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc


@router.get("/patient/{patient_uuid}/timeline", response_model=VisitTimelineResponse)
def get_visit_timeline(
    patient_uuid: str = Path(..., description="Patient UUID"),
    limit: int = Query(20, ge=1, le=100, description="Max visits to return"),
    db: Session = Depends(get_db),
    staff: Staff = Depends(require_role(UserRole.DOCTOR)),
):
    """
    Get patient visit timeline newest-first.
    
    Returns visits with status and outcome. Suitable for showing
    patient history to doctors.
    
    Requires: doctor role
    """
    # Verify patient exists
    patient = db.query(Patient).filter(Patient.patient_uuid == patient_uuid).first()
    if not patient:
        raise HTTPException(status_code=404, detail="Patient not found")
    
    # Get total count
    total_visits = db.query(func.count(VisitSession.id)).filter(
        VisitSession.patient_uuid == patient_uuid
    ).scalar() or 0
    
    # Get visits ordered by entry_time descending
    visits = db.query(VisitSession).filter(
        VisitSession.patient_uuid == patient_uuid
    ).order_by(
        desc(VisitSession.entry_time)
    ).limit(limit).all()
    
    # Format response
    visit_details = [
        VisitWithDetails(
            visit_session_id=v.visit_session_id,
            reason=v.reason,
            status=v.status,
            entry_time=v.entry_time,
            doctor_interaction_time=v.doctor_interaction_time,
            outcome=v.outcome,
        )
        for v in visits
    ]
    
    return VisitTimelineResponse(
        patient_uuid=patient_uuid,
        total_visits=total_visits,
        visits=visit_details,
    )


@router.post("/{visit_session_id}/notes", response_model=dict)
def add_visit_note(
    visit_session_id: str,
    content: str = Body(..., embed=True, min_length=1, max_length=10000),
    db: Session = Depends(get_db),
    staff: Staff = Depends(require_role(UserRole.DOCTOR, UserRole.CLINICIAN)),
):
    """Add a clinical note to a visit."""
    visit = db.query(VisitSession).filter(
        VisitSession.visit_session_id == visit_session_id
    ).first()
    if not visit:
        raise HTTPException(status_code=404, detail="Visit not found")
    
    # Append to outcome as a simple note storage solution
    timestamp = datetime.utcnow().isoformat()
    staff_id = staff.staff_id
    note_entry = f"\n[{timestamp}] {staff_id}: {content}"
    
    current_outcome = visit.outcome or ""
    visit.outcome = current_outcome + note_entry
    db.commit()
    
    return {
        "message": "Note added successfully",
        "visit_session_id": visit_session_id,
        "timestamp": timestamp,
    }
