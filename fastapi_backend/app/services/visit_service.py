from datetime import datetime

from sqlalchemy.orm import Session

from app.models.visit_session import VisitSession


class VisitService:
    @staticmethod
    def create(db: Session, patient_uuid: str, reason: str | None) -> VisitSession:
        visit = VisitSession(patient_uuid=patient_uuid, reason=reason)
        db.add(visit)
        db.commit()
        db.refresh(visit)
        return visit

    @staticmethod
    def get_by_session_id(db: Session, visit_session_id: str) -> VisitSession:
        visit = db.query(VisitSession).filter(VisitSession.visit_session_id == visit_session_id).first()
        if not visit:
            raise ValueError("Visit session not found")
        return visit

    @staticmethod
    def mark_doctor_interaction(db: Session, visit: VisitSession) -> VisitSession:
        visit.status = "in_consultation"
        visit.doctor_interaction_time = datetime.utcnow()
        db.commit()
        db.refresh(visit)
        return visit

    @staticmethod
    def complete_visit(db: Session, visit_session_id: str, outcome: str, status: str) -> VisitSession:
        visit = VisitService.get_by_session_id(db, visit_session_id)
        visit.outcome = outcome
        visit.status = status
        db.commit()
        db.refresh(visit)
        return visit