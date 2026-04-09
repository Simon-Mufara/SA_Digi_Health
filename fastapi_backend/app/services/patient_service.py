from sqlalchemy.orm import Session

from app.core.security import decrypt_text, encrypt_text, stable_hash
from app.models.patient import Patient
from app.models.visit_session import VisitSession
from app.schemas.patient import PatientCreate


class PatientService:
    @staticmethod
    def get_or_create_anonymous(db: Session, payload: PatientCreate) -> Patient:
        if payload.identifier:
            identifier_hash = stable_hash(payload.identifier.strip().lower())
            existing_by_identifier = db.query(Patient).filter(Patient.identifier_hash == identifier_hash).first()
            if existing_by_identifier:
                return existing_by_identifier
        else:
            identifier_hash = None

        if payload.name:
            name_hash = stable_hash(payload.name.strip().lower())
            existing_by_name = db.query(Patient).filter(Patient.name_hash == name_hash).first()
            if existing_by_name:
                return existing_by_name
        else:
            name_hash = None

        patient = Patient(
            encrypted_name=encrypt_text(payload.name.strip()) if payload.name else None,
            name_hash=name_hash,
            encrypted_identifier=encrypt_text(payload.identifier.strip()) if payload.identifier else None,
            identifier_hash=identifier_hash,
            gender=payload.gender,
        )
        db.add(patient)
        db.commit()
        db.refresh(patient)
        return patient

    @staticmethod
    def get_by_uuid(db: Session, patient_uuid: str) -> Patient:
        patient = db.query(Patient).filter(Patient.patient_uuid == patient_uuid).first()
        if not patient:
            raise ValueError("Patient not found")
        return patient

    @staticmethod
    def list_all(db: Session) -> list[Patient]:
        return db.query(Patient).order_by(Patient.created_at.desc()).all()

    @staticmethod
    def display_name(patient: Patient) -> str | None:
        if not patient.encrypted_name:
            return None
        return decrypt_text(patient.encrypted_name)

    @staticmethod
    def masked_identifier(patient: Patient) -> str | None:
        if not patient.encrypted_identifier:
            return None
        identifier = decrypt_text(patient.encrypted_identifier)
        if len(identifier) <= 4:
            return "*" * len(identifier)
        return "*" * (len(identifier) - 4) + identifier[-4:]

    @staticmethod
    def visit_timeline(db: Session, patient_uuid: str) -> list[VisitSession]:
        return (
            db.query(VisitSession)
            .filter(VisitSession.patient_uuid == patient_uuid)
            .order_by(VisitSession.entry_time.desc())
            .all()
        )