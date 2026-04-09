from collections import Counter

from sqlalchemy.orm import Session

from app.services.clinical_record_service import ClinicalRecordService
from app.services.llm_clinical_summary_service import LLMClinicalSummaryService
from app.services.patient_service import PatientService
from app.services.visit_service import VisitService


class ClinicalIntelligenceService:
    @staticmethod
    def smart_profile(db: Session, patient_uuid: str) -> dict:
        patient = PatientService.get_by_uuid(db, patient_uuid)
        records = ClinicalRecordService.list_by_patient_uuid(db, patient_uuid)
        visits = PatientService.visit_timeline(db, patient_uuid)

        diagnoses = [record.diagnosis for record in records]
        medications = [record.medication for record in records]
        recent_visit_statuses = [visit.status for visit in visits[:5]]

        diagnosis_counter = Counter(diagnoses)
        top_conditions = [name for name, _ in diagnosis_counter.most_common(3)]

        missed_recent_visits = len([visit for visit in visits[:3] if visit.status == "missed"])
        risk_factors = []
        alerts = []

        if missed_recent_visits >= 2:
            risk_factors.append("Poor follow-up adherence")
            alerts.append("High risk: missed last appointments")
        if any("hypertension" in diag.lower() for diag in diagnoses):
            risk_factors.append("Hypertension history")
            alerts.append("Chronic hypertension risk")
        if any("diabetes" in diag.lower() for diag in diagnoses):
            risk_factors.append("Diabetes history")
            alerts.append("Diabetes follow-up needed")
        if any("chest pain" in diag.lower() for diag in diagnoses):
            risk_factors.append("Possible cardiovascular concern")
            alerts.append("Requires cardiovascular review")

        ai_summary = LLMClinicalSummaryService.generate_clinical_summary(
            diagnoses=top_conditions,
            medications=medications[:5],
            recent_visit_statuses=recent_visit_statuses,
            risk_factors=risk_factors,
        )

        return {
            "patient_uuid": patient.patient_uuid,
            "display_name": PatientService.display_name(patient),
            "masked_identifier": PatientService.masked_identifier(patient),
            "gender": patient.gender,
            "conditions": top_conditions,
            "medications": medications[:5],
            "visit_count": len(visits),
            "last_visit_at": visits[0].entry_time if visits else None,
            "ai_summary": ai_summary,
            "risk_factors": risk_factors,
            "alerts": alerts,
        }

    @staticmethod
    def attach_doctor_context(db: Session, visit_session_id: str) -> dict:
        visit = VisitService.get_by_session_id(db, visit_session_id)
        visit = VisitService.mark_doctor_interaction(db, visit)
        profile = ClinicalIntelligenceService.smart_profile(db, visit.patient_uuid)
        profile["visit_session_id"] = visit.visit_session_id
        return profile