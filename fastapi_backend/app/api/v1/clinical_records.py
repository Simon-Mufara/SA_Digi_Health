from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.dependencies import require_role
from app.models.staff import Staff
from app.schemas.clinical_record import ClinicalRecordCreate, ClinicalRecordRead
from app.schemas.common import UserRole
from app.services.clinical_record_service import ClinicalRecordService

router = APIRouter(prefix="/clinical-records", tags=["clinical-records"])


@router.post("", response_model=ClinicalRecordRead, status_code=status.HTTP_201_CREATED)
def create_record(
    payload: ClinicalRecordCreate,
    db: Session = Depends(get_db),
    _: Staff = Depends(require_role(UserRole.DOCTOR, UserRole.CLINICIAN)),
):
    try:
        return ClinicalRecordService.create(db, payload)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc


@router.get("/patient/{patient_uuid}", response_model=list[ClinicalRecordRead])
def list_patient_records(
    patient_uuid: str,
    db: Session = Depends(get_db),
    _: Staff = Depends(require_role(UserRole.DOCTOR, UserRole.CLINICIAN, UserRole.SECURITY_OFFICER, UserRole.RESEARCHER)),
):
    return ClinicalRecordService.list_by_patient_uuid(db, patient_uuid)
