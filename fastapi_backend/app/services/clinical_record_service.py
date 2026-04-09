from sqlalchemy.orm import Session

from app.models.clinical_record import ClinicalRecord
from app.models.patient import Patient
from app.schemas.clinical_record import ClinicalRecordCreate


class ClinicalRecordService:
    @staticmethod
    def create(db: Session, payload: ClinicalRecordCreate) -> ClinicalRecord:
        patient = db.query(Patient).filter(Patient.patient_uuid == payload.patient_uuid).first()
        if not patient:
            raise ValueError("Patient not found")

        record = ClinicalRecord(**payload.model_dump())
        db.add(record)
        db.commit()
        db.refresh(record)
        return record

    @staticmethod
    def list_by_patient_uuid(db: Session, patient_uuid: str) -> list[ClinicalRecord]:
        return (
            db.query(ClinicalRecord)
            .filter(ClinicalRecord.patient_uuid == patient_uuid)
            .order_by(ClinicalRecord.created_at.desc())
            .all()
        )