import json

from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.security import create_gate_token, stable_hash
from app.models.face_recognition import BiometricProfile, FaceRecognitionEvent
from app.schemas.face_recognition import DoctorResolveResponse, GateScanResponse, ImageMatchResponse
from app.schemas.patient import PatientCreate
from app.services.face_embedding_service import FaceEmbeddingService
from app.services.patient_service import PatientService
from app.services.vector_store import build_vector_store
from app.services.visit_service import VisitService


class FaceRecognitionService:
    @staticmethod
    def enroll_biometric(db: Session, patient_uuid: str, embedding_vector: list[float]) -> BiometricProfile:
        patient = PatientService.get_by_uuid(db, patient_uuid)
        biometric_hash = stable_hash(json.dumps(embedding_vector))

        existing = db.query(BiometricProfile).filter(BiometricProfile.face_biometric_hash == biometric_hash).first()
        if existing and existing.patient_uuid != patient.patient_uuid:
            raise ValueError("Biometric profile already linked to another patient")

        vector_store = build_vector_store(db)
        vector_ref = vector_store.upsert(patient.patient_uuid, embedding_vector)

        if existing:
            existing.vector_ref = vector_ref
            db.commit()
            db.refresh(existing)
            return existing

        profile = BiometricProfile(
            patient_uuid=patient.patient_uuid,
            face_biometric_hash=biometric_hash,
            embedding_vector=json.dumps(embedding_vector),
            vector_ref=vector_ref,
        )
        db.add(profile)
        db.commit()
        db.refresh(profile)
        return profile

    @staticmethod
    def enroll_biometric_from_image(db: Session, patient_uuid: str, image_path: str) -> tuple[BiometricProfile, int]:
        embedding_vector = FaceEmbeddingService.extract_embedding_from_image_path(image_path)
        profile = FaceRecognitionService.enroll_biometric(db, patient_uuid, embedding_vector)
        return profile, len(embedding_vector)

    @staticmethod
    def match_image(db: Session, image_path: str) -> ImageMatchResponse:
        embedding_vector = FaceEmbeddingService.extract_embedding_from_image_path(image_path)
        patient_uuid, confidence = FaceRecognitionService._match_patient(db, embedding_vector)
        matched = patient_uuid is not None
        result = "match" if matched else "no_match"
        return ImageMatchResponse(matched=matched, patient_uuid=patient_uuid, confidence=confidence, result=result)

    @staticmethod
    def gate_scan(
        db: Session,
        embedding_vector: list[float],
        optional_name: str | None,
        optional_identifier: str | None,
        gender: str | None,
        reason: str | None,
    ) -> GateScanResponse:
        matched_patient_uuid, confidence = FaceRecognitionService._match_patient(db, embedding_vector)

        if matched_patient_uuid is None:
            patient = PatientService.get_or_create_anonymous(
                db,
                PatientCreate(name=optional_name, identifier=optional_identifier, gender=gender),
            )
            matched_patient_uuid = patient.patient_uuid
            profile = FaceRecognitionService.enroll_biometric(db, matched_patient_uuid, embedding_vector)
            confidence = 1.0 if profile else confidence
            result = "new_patient_registered"
        else:
            result = "matched_existing_patient"

        visit = VisitService.create(db, matched_patient_uuid, reason)
        gate_token = create_gate_token(matched_patient_uuid, visit.visit_session_id)

        event = FaceRecognitionEvent(
            patient_uuid=matched_patient_uuid,
            visit_session_id=visit.visit_session_id,
            confidence=confidence,
            result=result,
            capture_context="security_gate",
        )
        db.add(event)
        db.commit()

        return GateScanResponse(
            patient_uuid=matched_patient_uuid,
            visit_session_id=visit.visit_session_id,
            gate_token=gate_token,
            confidence=confidence,
            result=result,
        )

    @staticmethod
    def doctor_resolve(db: Session, embedding_vector: list[float]) -> DoctorResolveResponse:
        patient_uuid, confidence = FaceRecognitionService._match_patient(db, embedding_vector)
        matched = patient_uuid is not None
        result = "resolved" if matched else "unresolved"

        visit_session_id = None
        if matched:
            visit = VisitService.create(db, patient_uuid, reason="doctor-scan")
            visit_session_id = visit.visit_session_id

        event = FaceRecognitionEvent(
            patient_uuid=patient_uuid,
            visit_session_id=visit_session_id,
            confidence=confidence,
            result=result,
            capture_context="doctor_consultation",
        )
        db.add(event)
        db.commit()

        return DoctorResolveResponse(
            patient_uuid=patient_uuid,
            confidence=confidence,
            matched=matched,
            result=result,
            visit_session_id=visit_session_id,
        )

    @staticmethod
    def events(db: Session) -> list[FaceRecognitionEvent]:
        return db.query(FaceRecognitionEvent).order_by(FaceRecognitionEvent.id.desc()).all()

    @staticmethod
    def _match_patient(db: Session, embedding_vector: list[float]) -> tuple[str | None, float]:
        vector_store = build_vector_store(db)
        match = vector_store.search_best(embedding_vector, settings.face_match_threshold)
        return match.patient_uuid, match.confidence