import os
import re
import tempfile

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.schemas.patient import PatientCreate
from app.schemas.session import SessionCreateResponse
from app.services.face_embedding_service import FaceEmbeddingService
from app.services.face_recognition_service import FaceRecognitionService
from app.services.patient_service import PatientService
from app.services.visit_service import VisitService

router = APIRouter(prefix="/sessions", tags=["sessions"])
SA_ID_REGEX = re.compile(r"^\d{13}$")


@router.post("/create", response_model=SessionCreateResponse)
async def create_session(
    name: str = Form(...),
    identifier: str = Form(...),
    gender: str = Form(...),
    visit_reason: str = Form(...),
    face_image: UploadFile | None = File(default=None),
    db: Session = Depends(get_db),
):
    try:
        cleaned_name = name.strip()
        cleaned_identifier = identifier.strip()
        cleaned_gender = gender.strip()
        cleaned_reason = visit_reason.strip()

        if not cleaned_name:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="name is required")
        if not cleaned_reason:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="visit_reason is required")
        if cleaned_gender not in {"F", "M", "Other", "Unknown"}:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="gender must be F, M, Other, or Unknown")
        if not SA_ID_REGEX.fullmatch(cleaned_identifier):
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="South African ID must be exactly 13 digits.")

        patient = PatientService.get_or_create_anonymous(
            db,
            PatientCreate(name=cleaned_name, identifier=cleaned_identifier, gender=cleaned_gender),
        )

        image_received = False
        warning = None
        if face_image is not None:
            image_received = True
            suffix = os.path.splitext(face_image.filename or "face.jpg")[1] or ".jpg"
            temp_path = None
            try:
                with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
                    temp_path = tmp.name
                    tmp.write(await face_image.read())
                try:
                    embedding = FaceEmbeddingService.extract_embedding_from_image_path(temp_path)
                    FaceRecognitionService.enroll_biometric(db, patient.patient_uuid, embedding)
                except ValueError as exc:
                    warning = str(exc)
            finally:
                if temp_path and os.path.exists(temp_path):
                    os.remove(temp_path)

        visit = VisitService.create(db, patient.patient_uuid, cleaned_reason)
        return SessionCreateResponse(
            patient_uuid=patient.patient_uuid,
            visit_session_id=visit.visit_session_id,
            result="session_created",
            image_received=image_received,
            warning=warning,
        )
    except HTTPException:
        raise
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc
    except Exception as exc:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"session creation failed: {exc}") from exc
