import os
import tempfile
import re

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.dependencies import require_role
from app.models.staff import Staff
from app.schemas.common import UserRole
from app.schemas.face_recognition import (
    BiometricEnrollRequest,
    BiometricEnrollResponse,
    DoctorResolveRequest,
    DoctorResolveResponse,
    FaceRecognitionEventRead,
    GateScanRequest,
    GateScanResponse,
    ImageEnrollResponse,
    ImageMatchResponse,
)
from app.schemas.patient import SmartPatientProfile
from app.services.clinical_intelligence_service import ClinicalIntelligenceService
from app.services.face_embedding_service import FaceEmbeddingService
from app.services.face_recognition_service import FaceRecognitionService

router = APIRouter(prefix="/face-recognition", tags=["face-recognition"])
SA_ID_REGEX = re.compile(r"^\d{13}$")


@router.post("/enroll", response_model=BiometricEnrollResponse, status_code=status.HTTP_201_CREATED)
def enroll(
    payload: BiometricEnrollRequest,
    db: Session = Depends(get_db),
    _: Staff = Depends(require_role(UserRole.SECURITY_OFFICER, UserRole.CLINICIAN)),
):
    try:
        profile = FaceRecognitionService.enroll_biometric(db, payload.patient_uuid, payload.embedding_vector)
        return BiometricEnrollResponse(
            patient_uuid=profile.patient_uuid,
            face_biometric_hash=profile.face_biometric_hash,
            vector_ref=profile.vector_ref,
            created_at=profile.created_at,
        )
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc


@router.post("/enroll-image", response_model=ImageEnrollResponse, status_code=status.HTTP_201_CREATED)
async def enroll_image(
    patient_uuid: str,
    image: UploadFile = File(...),
    db: Session = Depends(get_db),
    _: Staff = Depends(require_role(UserRole.SECURITY_OFFICER, UserRole.CLINICIAN)),
):
    suffix = os.path.splitext(image.filename or "face.jpg")[1] or ".jpg"
    temp_path = None
    try:
        with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
            temp_path = tmp.name
            tmp.write(await image.read())

        profile, embedding_dimension = FaceRecognitionService.enroll_biometric_from_image(db, patient_uuid, temp_path)
        return ImageEnrollResponse(
            patient_uuid=profile.patient_uuid,
            face_biometric_hash=profile.face_biometric_hash,
            vector_ref=profile.vector_ref,
            embedding_dimension=embedding_dimension,
            created_at=profile.created_at,
        )
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc
    finally:
        if temp_path and os.path.exists(temp_path):
            os.remove(temp_path)


@router.post("/match-image", response_model=ImageMatchResponse)
async def match_image(
    image: UploadFile = File(...),
    db: Session = Depends(get_db),
    _: Staff = Depends(require_role(UserRole.SECURITY_OFFICER, UserRole.DOCTOR, UserRole.CLINICIAN)),
):
    suffix = os.path.splitext(image.filename or "face.jpg")[1] or ".jpg"
    temp_path = None
    try:
        with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
            temp_path = tmp.name
            tmp.write(await image.read())

        return FaceRecognitionService.match_image(db, temp_path)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc
    finally:
        if temp_path and os.path.exists(temp_path):
            os.remove(temp_path)


@router.post("/gate-scan", response_model=GateScanResponse)
def gate_scan(
    payload: GateScanRequest,
    db: Session = Depends(get_db),
    _: Staff = Depends(require_role(UserRole.SECURITY_OFFICER, UserRole.CLINICIAN)),
):
    try:
        return FaceRecognitionService.gate_scan(
            db,
            payload.embedding_vector,
            payload.optional_name,
            payload.optional_identifier,
            payload.gender,
            payload.reason,
        )
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc


@router.post("/gate-scan-image", response_model=GateScanResponse)
async def gate_scan_image(
    image: UploadFile = File(...),
    optional_name: str | None = Form(default=None),
    optional_identifier: str | None = Form(default=None),
    gender: str | None = Form(default=None),
    reason: str | None = Form(default=None),
    db: Session = Depends(get_db),
    _: Staff = Depends(require_role(UserRole.SECURITY_OFFICER, UserRole.CLINICIAN)),
):
    if optional_identifier:
        cleaned_identifier = optional_identifier.strip()
        if not SA_ID_REGEX.fullmatch(cleaned_identifier):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="South African ID must be exactly 13 digits.",
            )
        optional_identifier = cleaned_identifier

    suffix = os.path.splitext(image.filename or "face.jpg")[1] or ".jpg"
    temp_path = None
    try:
        with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
            temp_path = tmp.name
            tmp.write(await image.read())

        embedding = FaceEmbeddingService.extract_embedding_from_image_path(temp_path)
        return FaceRecognitionService.gate_scan(
            db,
            embedding,
            optional_name,
            optional_identifier,
            gender,
            reason,
        )
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc
    finally:
        if temp_path and os.path.exists(temp_path):
            os.remove(temp_path)


@router.post("/doctor-resolve", response_model=DoctorResolveResponse)
def doctor_resolve(
    payload: DoctorResolveRequest,
    db: Session = Depends(get_db),
    _: Staff = Depends(require_role(UserRole.DOCTOR, UserRole.CLINICIAN)),
):
    try:
        return FaceRecognitionService.doctor_resolve(db, payload.embedding_vector)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc


@router.post("/doctor-profile-from-scan", response_model=SmartPatientProfile)
def doctor_profile_from_scan(
    payload: DoctorResolveRequest,
    db: Session = Depends(get_db),
    _: Staff = Depends(require_role(UserRole.DOCTOR, UserRole.CLINICIAN)),
):
    resolved = FaceRecognitionService.doctor_resolve(db, payload.embedding_vector)
    if not resolved.matched or not resolved.visit_session_id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Patient identity not resolved")

    profile = ClinicalIntelligenceService.attach_doctor_context(db, resolved.visit_session_id)
    return SmartPatientProfile(**{k: v for k, v in profile.items() if k in SmartPatientProfile.model_fields})


@router.post("/doctor-profile-from-image", response_model=SmartPatientProfile)
async def doctor_profile_from_image(
    image: UploadFile = File(...),
    db: Session = Depends(get_db),
    _: Staff = Depends(require_role(UserRole.DOCTOR, UserRole.CLINICIAN)),
):
    suffix = os.path.splitext(image.filename or "face.jpg")[1] or ".jpg"
    temp_path = None
    try:
        with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
            temp_path = tmp.name
            tmp.write(await image.read())

        embedding = FaceEmbeddingService.extract_embedding_from_image_path(temp_path)
        resolved = FaceRecognitionService.doctor_resolve(db, embedding)
        if not resolved.matched or not resolved.visit_session_id:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Patient identity not resolved")

        profile = ClinicalIntelligenceService.attach_doctor_context(db, resolved.visit_session_id)
        return SmartPatientProfile(**{k: v for k, v in profile.items() if k in SmartPatientProfile.model_fields})
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc
    finally:
        if temp_path and os.path.exists(temp_path):
            os.remove(temp_path)


@router.get("/events", response_model=list[FaceRecognitionEventRead])
def list_events(
    db: Session = Depends(get_db),
    _: Staff = Depends(require_role(UserRole.SECURITY_OFFICER, UserRole.DOCTOR, UserRole.ADMIN, UserRole.RESEARCHER)),
):
    return FaceRecognitionService.events(db)
