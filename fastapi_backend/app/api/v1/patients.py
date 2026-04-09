import os
import tempfile
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from fastapi import File, Form, UploadFile
from sqlalchemy import or_, func
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.dependencies import require_role
from app.core.security import create_gate_token
from app.models.face_recognition import FaceRecognitionEvent
from app.models.staff import Staff
from app.models.patient import Patient
from app.models.visit_session import VisitSession
from app.schemas.checkin import PatientCheckinResponse
from app.schemas.common import UserRole
from app.schemas.patient import PatientCreate
from app.schemas.patient import PatientRead, PatientTimelineVisit, SmartPatientProfile, PatientSearchResult
from app.services.clinical_intelligence_service import ClinicalIntelligenceService
from app.services.face_embedding_service import FaceEmbeddingService
from app.services.face_recognition_service import FaceRecognitionService
from app.services.patient_service import PatientService
from app.services.visit_service import VisitService

router = APIRouter(prefix="/patients", tags=["patients"])


def mask_name_to_initials(name: Optional[str]) -> Optional[str]:
    """Mask full name to initials only (e.g., 'John Smith' -> 'J.S.')"""
    if not name:
        return None
    parts = name.strip().split()
    if not parts:
        return None
    initials = '.'.join(p[0].upper() for p in parts if p) + '.'
    return initials


@router.post("/checkin", response_model=PatientCheckinResponse)
async def patient_checkin(
    face_image: UploadFile | None = File(default=None),
    name: str | None = Form(default=None),
    identifier: str | None = Form(default=None),
    gender: str | None = Form(default=None),
    visit_reason: str = Form(...),
    db: Session = Depends(get_db),
):
    """Public endpoint for patient self-service check-in. No authentication required."""
    temp_path = None
    biometric_warning: str | None = None
    try:
        if not visit_reason.strip():
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="visit_reason is required")

        cleaned_identifier = identifier.strip() if identifier else None
        if cleaned_identifier and (not cleaned_identifier.isdigit() or len(cleaned_identifier) != 13):
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="South African ID must be exactly 13 digits.")

        # Handle optional face image
        embedding = None
        if face_image and face_image.filename:
            suffix = os.path.splitext(face_image.filename)[1] or ".jpg"
            with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
                temp_path = tmp.name
                tmp.write(await face_image.read())
            try:
                embedding = FaceEmbeddingService.extract_embedding_from_image_path(temp_path)
            except ValueError as exc:
                biometric_warning = str(exc)
                embedding = None

        # Try to match patient if we have embedding
        matched_uuid = None
        confidence = 0.0
        if embedding:
            matched_uuid, confidence = FaceRecognitionService._match_patient(db, embedding)

        returning = matched_uuid is not None

        if returning:
            patient = PatientService.get_by_uuid(db, matched_uuid)
        else:
            try:
                patient = PatientService.get_or_create_anonymous(
                    db,
                    PatientCreate(
                        name=name.strip() if name else None,
                        identifier=cleaned_identifier,
                        gender=gender.strip() if gender else None,
                    ),
                )
            except Exception as exc:
                if "already exists" in str(exc).lower() or "unique" in str(exc).lower():
                    raise HTTPException(
                        status_code=status.HTTP_409_CONFLICT,
                        detail="Duplicate identifier conflict.",
                    ) from exc
                raise

            # Enroll face if we have embedding
            if embedding:
                FaceRecognitionService.enroll_biometric(db, patient.patient_uuid, embedding)
                confidence = 1.0

        visit = VisitService.create(db, patient.patient_uuid, visit_reason.strip())
        session_token = create_gate_token(patient.patient_uuid, visit.visit_session_id)

        event = FaceRecognitionEvent(
            patient_uuid=patient.patient_uuid,
            visit_session_id=visit.visit_session_id,
            confidence=confidence,
            result="matched_existing_patient" if returning else "new_patient_registered",
            capture_context="patient_checkin",
        )
        db.add(event)
        db.commit()

        return PatientCheckinResponse(
            returning_patient=returning,
            patient_uuid=patient.patient_uuid,
            patient_name=PatientService.display_name(patient),
            masked_identifier=PatientService.masked_identifier(patient),
            gender=patient.gender,
            confidence=confidence,
            visit_session_id=visit.visit_session_id,
            session_token=session_token,
            message=(
                "Returning patient"
                if returning
                else "New patient created"
            )
            if not biometric_warning
            else (
                "Session created without biometric match. "
                "Face capture is optional and can be completed later."
            ),
        )
    except HTTPException:
        raise
    except ValueError as exc:
        detail = str(exc)
        if "No face" in detail or "detect" in detail.lower():
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="No face detected in the image.") from exc
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=detail) from exc
    except Exception as exc:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Check-in failed: {exc}") from exc
    finally:
        if temp_path and os.path.exists(temp_path):
            os.remove(temp_path)


@router.get("", response_model=list[PatientRead])
def list_patients(
    db: Session = Depends(get_db),
    _: Staff = Depends(require_role(UserRole.SECURITY_OFFICER, UserRole.DOCTOR)),
):
    patients = PatientService.list_all(db)
    return [
        PatientRead(
            patient_uuid=patient.patient_uuid,
            display_name=PatientService.display_name(patient),
            masked_identifier=PatientService.masked_identifier(patient),
            gender=patient.gender,
            created_at=patient.created_at,
        )
        for patient in patients
    ]


@router.get("/{patient_uuid}", response_model=PatientRead)
def get_patient(
    patient_uuid: str,
    db: Session = Depends(get_db),
    _: Staff = Depends(require_role(UserRole.SECURITY_OFFICER, UserRole.DOCTOR)),
):
    try:
        patient = PatientService.get_by_uuid(db, patient_uuid)
        return PatientRead(
            patient_uuid=patient.patient_uuid,
            display_name=PatientService.display_name(patient),
            masked_identifier=PatientService.masked_identifier(patient),
            gender=patient.gender,
            created_at=patient.created_at,
        )
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc


@router.get("/{patient_uuid}/timeline", response_model=list[PatientTimelineVisit])
def get_patient_timeline(
    patient_uuid: str,
    db: Session = Depends(get_db),
    _: Staff = Depends(require_role(UserRole.SECURITY_OFFICER, UserRole.DOCTOR)),
):
    visits = PatientService.visit_timeline(db, patient_uuid)
    return [
        PatientTimelineVisit(
            visit_session_id=visit.visit_session_id,
            reason=visit.reason,
            status=visit.status,
            entry_time=visit.entry_time,
            doctor_interaction_time=visit.doctor_interaction_time,
            outcome=visit.outcome,
        )
        for visit in visits
    ]


@router.get("/{patient_uuid}/smart-profile", response_model=SmartPatientProfile)
def get_smart_profile(
    patient_uuid: str,
    db: Session = Depends(get_db),
    _: Staff = Depends(require_role(UserRole.DOCTOR, UserRole.CLINICIAN)),
):
    try:
        profile = ClinicalIntelligenceService.smart_profile(db, patient_uuid)
        return SmartPatientProfile(**profile)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc


@router.get("/search/query", response_model=List[PatientSearchResult])
def search_patients(
    q: str = Query(..., min_length=1, description="Search query for name or identifier"),
    limit: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
    staff: Staff = Depends(require_role(UserRole.DOCTOR, UserRole.CLINICIAN)),
):
    """
    Search patients by name or identifier.
    
    - Doctors see full names
    - Clinicians see names masked to initials only
    
    Returns: patient_uuid, name (potentially masked), identifier, last_visit date
    """
    search_term = f"%{q}%"
    
    # Query patients matching name or identifier
    patients = db.query(Patient).filter(
        or_(
            Patient.encrypted_name.ilike(search_term) if hasattr(Patient, 'encrypted_name') else Patient.name.ilike(search_term),
            Patient.identifier_hash.ilike(search_term) if hasattr(Patient, 'identifier_hash') else Patient.identifier.ilike(search_term),
        )
    ).limit(limit).all()
    
    results = []
    for patient in patients:
        # Get last visit date
        last_visit = db.query(func.max(VisitSession.entry_time)).filter(
            VisitSession.patient_uuid == patient.patient_uuid
        ).scalar()
        
        # Get display name
        display_name = PatientService.display_name(patient)
        
        # Mask name for clinicians
        if staff.assigned_role == "clinician":
            display_name = mask_name_to_initials(display_name)
        
        results.append(PatientSearchResult(
            patient_uuid=patient.patient_uuid,
            display_name=display_name,
            masked_identifier=PatientService.masked_identifier(patient),
            gender=patient.gender,
            last_visit=last_visit,
        ))
    
    return results
