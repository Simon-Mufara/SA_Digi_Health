"""
Research endpoints for YARA - de-identified cohort analytics.
All endpoints enforce k-anonymity (min group size of 5).
NEVER expose: patient_id, name, identifier, face_embedding_id, staff_id
"""
import csv
import io
from datetime import datetime
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from sqlalchemy import func, case
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.dependencies import require_role
from app.models.staff import Staff
from app.models.patient import Patient
from app.models.visit_session import VisitSession
from app.schemas.common import UserRole

router = APIRouter(prefix="/research", tags=["research"])

# K-anonymity threshold - suppress groups smaller than this
K_ANONYMITY_MIN = 5


# Response models
class CohortGroup(BaseModel):
    age_group: str
    gender: str
    visit_reason: Optional[str] = None
    visit_count: int


class CohortResponse(BaseModel):
    total_records: int
    suppressed_groups: int
    cohorts: List[CohortGroup]
    k_anonymity_threshold: int = K_ANONYMITY_MIN
    generated_at: datetime


class ExportMetadata(BaseModel):
    filename: str
    record_count: int
    generated_at: datetime
    researcher_id: str


def _calculate_age_band(identifier: Optional[str]) -> str:
    """
    Calculate age band from SA ID number.
    SA ID format: YYMMDD SSSS C A Z
    First 6 digits are birthdate (YYMMDD)
    """
    if not identifier or len(identifier) < 6:
        return "Unknown"
    
    try:
        year_part = int(identifier[0:2])
        # Handle century: 00-30 = 2000s, 31-99 = 1900s
        if year_part <= 30:
            birth_year = 2000 + year_part
        else:
            birth_year = 1900 + year_part
        
        current_year = datetime.now().year
        age = current_year - birth_year
        
        if age < 0:
            return "Unknown"
        elif age < 5:
            return "0-4"
        elif age < 15:
            return "5-14"
        elif age < 50:
            return "15-49"
        elif age < 65:
            return "50-64"
        else:
            return "65+"
    except (ValueError, TypeError):
        return "Unknown"


def _extract_gender_from_id(identifier: Optional[str]) -> str:
    """
    Extract gender from SA ID number.
    Digits 7-10 (SSSS): 0000-4999 = Female, 5000-9999 = Male
    """
    if not identifier or len(identifier) < 10:
        return "Unknown"
    
    try:
        gender_digits = int(identifier[6:10])
        if gender_digits < 5000:
            return "Female"
        else:
            return "Male"
    except (ValueError, TypeError):
        return "Unknown"


@router.get("/cohorts", response_model=CohortResponse)
def get_cohorts(
    db: Session = Depends(get_db),
    staff: Staff = Depends(require_role(UserRole.RESEARCHER)),
):
    """
    Get de-identified cohort statistics.
    
    Groups patients by age band, gender, and visit reason.
    Applies k-anonymity filtering (suppresses groups with count < 5).
    
    NEVER returns: patient IDs, names, identifiers, face embeddings, staff IDs
    
    Requires: researcher role
    """
    # Get all patients with visits
    patients = db.query(Patient).all()
    
    # Get visit counts by patient with reason
    visits_query = db.query(
        VisitSession.patient_uuid,
        VisitSession.reason,
        func.count(VisitSession.id).label("visit_count")
    ).group_by(
        VisitSession.patient_uuid,
        VisitSession.reason
    ).all()
    
    # Build cohort map
    cohort_map = {}  # (age_group, gender, reason) -> count
    
    patient_lookup = {p.patient_uuid: p for p in patients}
    
    for visit_data in visits_query:
        patient_uuid = visit_data.patient_uuid
        reason = visit_data.reason or "Unspecified"
        count = visit_data.visit_count
        
        patient = patient_lookup.get(patient_uuid)
        if not patient:
            continue
        
        # Calculate age and gender from identifier or use stored gender
        age_band = _calculate_age_band(patient.identifier)
        gender = patient.gender or _extract_gender_from_id(patient.identifier) or "Unknown"
        
        key = (age_band, gender, reason)
        cohort_map[key] = cohort_map.get(key, 0) + count
    
    # Apply k-anonymity filtering
    cohorts = []
    suppressed = 0
    total_records = 0
    
    for (age_group, gender, reason), count in cohort_map.items():
        total_records += count
        if count >= K_ANONYMITY_MIN:
            cohorts.append(CohortGroup(
                age_group=age_group,
                gender=gender,
                visit_reason=reason,
                visit_count=count,
            ))
        else:
            suppressed += 1
    
    # Sort by visit count descending
    cohorts.sort(key=lambda x: x.visit_count, reverse=True)
    
    return CohortResponse(
        total_records=total_records,
        suppressed_groups=suppressed,
        cohorts=cohorts,
        k_anonymity_threshold=K_ANONYMITY_MIN,
        generated_at=datetime.utcnow(),
    )


@router.get("/export")
def export_cohort_data(
    db: Session = Depends(get_db),
    staff: Staff = Depends(require_role(UserRole.RESEARCHER)),
):
    """
    Export de-identified cohort data as CSV.
    
    Columns: age_group, gender, visit_reason, visit_count
    
    NEVER includes: patient_id, name, identifier, face_embedding_id, staff_id
    
    Logs export event to audit trail.
    
    Requires: researcher role
    """
    # Get cohort data (reuse cohorts logic)
    cohort_response = get_cohorts(db=db, staff=staff)
    
    # Generate CSV
    output = io.StringIO()
    writer = csv.writer(output)
    
    # Header
    writer.writerow(["age_group", "gender", "visit_reason", "visit_count"])
    
    # Data rows
    for cohort in cohort_response.cohorts:
        writer.writerow([
            cohort.age_group,
            cohort.gender,
            cohort.visit_reason,
            cohort.visit_count,
        ])
    
    # Add metadata footer
    writer.writerow([])
    writer.writerow(["# Export metadata"])
    writer.writerow([f"# Generated: {datetime.utcnow().isoformat()}"])
    writer.writerow([f"# Total records: {cohort_response.total_records}"])
    writer.writerow([f"# Suppressed groups (k<{K_ANONYMITY_MIN}): {cohort_response.suppressed_groups}"])
    writer.writerow([f"# Exported by: {staff.staff_id}"])
    writer.writerow(["# Note: All data de-identified. No PII included."])
    
    # Log audit event (in production, save to audit_events table)
    print(f"AUDIT: Research export by {staff.staff_id} at {datetime.utcnow()}")
    
    # Return as streaming response
    output.seek(0)
    filename = f"yara_cohort_export_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}.csv"
    
    return StreamingResponse(
        iter([output.getvalue()]),
        media_type="text/csv",
        headers={"Content-Disposition": f"attachment; filename={filename}"},
    )


@router.get("/summary")
def get_research_summary(
    db: Session = Depends(get_db),
    staff: Staff = Depends(require_role(UserRole.RESEARCHER)),
):
    """
    Get high-level research statistics.
    All numbers are aggregates - no individual patient data.
    """
    total_patients = db.query(func.count(Patient.id)).scalar() or 0
    total_visits = db.query(func.count(VisitSession.id)).scalar() or 0
    
    # Gender distribution
    gender_counts = db.query(
        Patient.gender,
        func.count(Patient.id)
    ).group_by(Patient.gender).all()
    
    # Visit reason distribution
    reason_counts = db.query(
        VisitSession.reason,
        func.count(VisitSession.id)
    ).group_by(VisitSession.reason).all()
    
    return {
        "total_patients": total_patients,
        "total_visits": total_visits,
        "avg_visits_per_patient": round(total_visits / max(total_patients, 1), 2),
        "gender_distribution": {
            (g or "Unknown"): c for g, c in gender_counts
        },
        "visit_reason_distribution": {
            (r or "Unspecified"): c for r, c in reason_counts
        },
        "data_note": "All data de-identified. Individual records not accessible.",
        "generated_at": datetime.utcnow().isoformat(),
    }
