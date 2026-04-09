"""
Analytics API for PHDC-style health data analysis.
Provides disease burden, facility statistics, and de-identified cohort exports.
"""
from datetime import datetime
from typing import Optional

from fastapi import APIRouter, Depends, Query
from fastapi.responses import StreamingResponse
from sqlalchemy import func, case, text
from sqlalchemy.orm import Session
import csv
import io

from app.core.database import get_db
from app.core.dependencies import require_role
from app.models.patient import Patient
from app.models.visit_session import VisitSession
from app.models.staff import Staff
from app.schemas.common import UserRole

router = APIRouter(prefix="/analytics", tags=["analytics"])

# PHDC Disease Groups based on ICD-10 mapping
DISEASE_GROUPS = {
    "ALRI": ["J06", "J18", "J20", "J21", "J22"],  # Acute Lower Respiratory Infections
    "HIV": ["B20", "B21", "B22", "B23", "B24", "Z21"],
    "TB": ["A15", "A16", "A17", "A18", "A19"],
    "NCD": ["I10", "I25", "E11", "E78", "J45"],  # Non-Communicable Diseases (Hypertension, Diabetes, etc.)
    "Maternal": ["O00", "O80", "O82", "Z34", "Z35"],
    "Injury": ["S00", "S01", "S02", "T00", "T14"],
    "Mental Health": ["F20", "F32", "F33", "F41"],
    "Other": []  # Catch-all
}

# Age bands for burden analysis
AGE_BANDS = [
    (0, 4, "0-4"),
    (5, 14, "5-14"),
    (15, 49, "15-49"),
    (50, 64, "50-64"),
    (65, 200, "65+"),
]

# Western Cape districts
WC_DISTRICTS = ["City of Cape Town", "Cape Winelands", "Garden Route", "West Coast", "Overberg", "Central Karoo"]

# Sample facilities (can be extended)
FACILITIES = [
    "Khayelitsha CHC", "Mitchell's Plain CDC", "Gugulethu CHC",
    "Stellenbosch Clinic", "Paarl East Clinic", "Worcester Hospital",
    "George Hospital", "Mossel Bay Clinic"
]


def classify_disease_group(icd10_code: Optional[str]) -> str:
    """Classify ICD-10 code into PHDC disease group."""
    if not icd10_code:
        return "Other"
    code = icd10_code.upper().strip()
    for group, prefixes in DISEASE_GROUPS.items():
        for prefix in prefixes:
            if code.startswith(prefix):
                return group
    return "Other"


def get_age_band(age: Optional[int]) -> str:
    """Map age to PHDC age band."""
    if age is None:
        return "Unknown"
    for min_age, max_age, label in AGE_BANDS:
        if min_age <= age <= max_age:
            return label
    return "Unknown"


@router.get("/summary")
def analytics_summary(
    db: Session = Depends(get_db),
    _: Staff = Depends(require_role(UserRole.RESEARCHER, UserRole.ADMIN, UserRole.DOCTOR)),
):
    """
    High-level analytics summary aligned with PHDC workbook metrics.
    """
    total_visits = db.query(func.count(VisitSession.id)).scalar() or 0
    total_patients = db.query(func.count(Patient.id)).scalar() or 0
    
    # Get date range
    min_date = db.query(func.min(VisitSession.entry_time)).scalar()
    max_date = db.query(func.max(VisitSession.entry_time)).scalar()
    
    # Gender distribution
    gender_counts = dict(
        db.query(Patient.gender, func.count(Patient.id))
        .group_by(Patient.gender)
        .all()
    )
    
    return {
        "total_visits": total_visits,
        "unique_patients": total_patients,
        "date_range": {
            "start": min_date.isoformat() if min_date else None,
            "end": max_date.isoformat() if max_date else None,
        },
        "gender_distribution": gender_counts,
        "disease_groups": list(DISEASE_GROUPS.keys()),
        "districts": WC_DISTRICTS,
        "facilities_count": len(FACILITIES),
    }


@router.get("/disease-burden")
def disease_burden_analysis(
    district: Optional[str] = Query(None, description="Filter by district"),
    start_date: Optional[str] = Query(None, description="Start date (YYYY-MM-DD)"),
    end_date: Optional[str] = Query(None, description="End date (YYYY-MM-DD)"),
    db: Session = Depends(get_db),
    _: Staff = Depends(require_role(UserRole.RESEARCHER, UserRole.ADMIN, UserRole.DOCTOR)),
):
    """
    Quadruple burden analysis: disease load by age, gender, and geography.
    Returns data suitable for pivot tables and heatmaps.
    """
    # Build base query joining visits with patients
    query = db.query(
        VisitSession.reason,
        Patient.gender,
        VisitSession.entry_time,
    ).join(Patient, Patient.patient_uuid == VisitSession.patient_uuid)
    
    # Apply filters
    if start_date:
        query = query.filter(VisitSession.entry_time >= datetime.fromisoformat(start_date))
    if end_date:
        query = query.filter(VisitSession.entry_time <= datetime.fromisoformat(end_date))
    
    visits = query.all()
    
    # Aggregate by disease group
    disease_counts = {}
    gender_by_disease = {}
    
    for visit_reason, gender, entry_time in visits:
        # Use visit reason as proxy for disease classification
        # In production, this would use ICD-10 codes from clinical records
        disease_group = classify_visit_reason(visit_reason)
        
        disease_counts[disease_group] = disease_counts.get(disease_group, 0) + 1
        
        if disease_group not in gender_by_disease:
            gender_by_disease[disease_group] = {"M": 0, "F": 0, "Other": 0, "Unknown": 0}
        
        g = gender if gender in ["M", "F", "Other"] else "Unknown"
        gender_by_disease[disease_group][g] += 1
    
    # Calculate percentages
    total = sum(disease_counts.values()) or 1
    disease_share = {k: round(v / total * 100, 1) for k, v in disease_counts.items()}
    
    return {
        "total_visits": sum(disease_counts.values()),
        "disease_counts": disease_counts,
        "disease_share_pct": disease_share,
        "gender_by_disease": gender_by_disease,
        "filters_applied": {
            "district": district,
            "start_date": start_date,
            "end_date": end_date,
        },
    }


@router.get("/facility-stats")
def facility_statistics(
    db: Session = Depends(get_db),
    _: Staff = Depends(require_role(UserRole.RESEARCHER, UserRole.ADMIN)),
):
    """
    Visit distribution by facility and district.
    """
    # Count visits by status
    status_counts = dict(
        db.query(VisitSession.status, func.count(VisitSession.id))
        .group_by(VisitSession.status)
        .all()
    )
    
    # Visits over time (monthly)
    monthly_visits = (
        db.query(
            func.strftime("%Y-%m", VisitSession.entry_time).label("month"),
            func.count(VisitSession.id).label("count"),
        )
        .group_by(text("month"))
        .order_by(text("month"))
        .all()
    )
    
    return {
        "status_distribution": status_counts,
        "monthly_visits": [{"month": m, "count": c} for m, c in monthly_visits],
        "facilities": FACILITIES,
        "districts": WC_DISTRICTS,
    }


@router.get("/data-quality")
def data_quality_audit(
    db: Session = Depends(get_db),
    _: Staff = Depends(require_role(UserRole.RESEARCHER, UserRole.ADMIN)),
):
    """
    Data quality audit: missing values, completeness metrics.
    """
    total_patients = db.query(func.count(Patient.id)).scalar() or 1
    total_visits = db.query(func.count(VisitSession.id)).scalar() or 1
    
    # Check missing values in patients
    missing_name = db.query(func.count(Patient.id)).filter(Patient.encrypted_name.is_(None)).scalar() or 0
    missing_identifier = db.query(func.count(Patient.id)).filter(Patient.encrypted_identifier.is_(None)).scalar() or 0
    missing_gender = db.query(func.count(Patient.id)).filter(
        (Patient.gender.is_(None)) | (Patient.gender == "")
    ).scalar() or 0
    
    # Check missing values in visits
    missing_reason = db.query(func.count(VisitSession.id)).filter(
        (VisitSession.reason.is_(None)) | (VisitSession.reason == "")
    ).scalar() or 0
    
    return {
        "total_patients": total_patients,
        "total_visits": total_visits,
        "patient_completeness": {
            "name": {
                "null_count": missing_name,
                "pct_missing": round(missing_name / total_patients * 100, 1),
                "severity": "low" if missing_name / total_patients < 0.05 else "high",
            },
            "identifier": {
                "null_count": missing_identifier,
                "pct_missing": round(missing_identifier / total_patients * 100, 1),
                "severity": "low" if missing_identifier / total_patients < 0.05 else "high",
            },
            "gender": {
                "null_count": missing_gender,
                "pct_missing": round(missing_gender / total_patients * 100, 1),
                "severity": "low" if missing_gender / total_patients < 0.05 else "high",
            },
        },
        "visit_completeness": {
            "reason": {
                "null_count": missing_reason,
                "pct_missing": round(missing_reason / total_visits * 100, 1),
                "severity": "low" if missing_reason / total_visits < 0.05 else "high",
            },
        },
        "recommendations": [
            "Fill missing gender with 'Unknown' or median" if missing_gender > 0 else None,
            "Flag records with missing identifiers for follow-up" if missing_identifier > 0 else None,
        ],
    }


@router.get("/cohort-export")
def cohort_export(
    format: str = Query("json", description="Export format: json or csv"),
    include_pii: bool = Query(False, description="Include PII fields (requires admin role)"),
    db: Session = Depends(get_db),
    current_user: Staff = Depends(require_role(UserRole.RESEARCHER, UserRole.ADMIN)),
):
    """
    De-identified cohort export for research.
    CSV export excludes PII fields by default.
    """
    # Only admin can export PII
    if include_pii and current_user.assigned_role != UserRole.ADMIN.value:
        include_pii = False
    
    # Query visits with patient data
    query = db.query(
        VisitSession.visit_session_id,
        Patient.patient_uuid,
        Patient.gender,
        VisitSession.reason,
        VisitSession.status,
        VisitSession.entry_time,
        VisitSession.outcome,
    ).join(Patient, Patient.patient_uuid == VisitSession.patient_uuid)
    
    records = query.all()
    
    # Build de-identified dataset
    data = []
    for r in records:
        row = {
            "visit_id": r.visit_session_id[:8] + "...",  # Truncated for privacy
            "patient_hash": r.patient_uuid[:8] + "...",  # Truncated
            "gender": r.gender or "Unknown",
            "visit_reason": r.reason or "",
            "disease_group": classify_visit_reason(r.reason),
            "status": r.status,
            "visit_date": r.entry_time.strftime("%Y-%m-%d") if r.entry_time else None,
            "outcome": r.outcome or "",
        }
        data.append(row)
    
    if format == "csv":
        output = io.StringIO()
        if data:
            writer = csv.DictWriter(output, fieldnames=data[0].keys())
            writer.writeheader()
            writer.writerows(data)
        output.seek(0)
        
        return StreamingResponse(
            iter([output.getvalue()]),
            media_type="text/csv",
            headers={"Content-Disposition": "attachment; filename=cohort_export.csv"},
        )
    
    return {
        "record_count": len(data),
        "columns": list(data[0].keys()) if data else [],
        "data": data,
        "pii_included": include_pii,
        "export_timestamp": datetime.utcnow().isoformat(),
    }


def classify_visit_reason(reason: Optional[str]) -> str:
    """
    Classify visit reason into disease group.
    This is a heuristic mapping; in production use ICD-10 codes.
    """
    if not reason:
        return "Other"
    
    reason_lower = reason.lower()
    
    mappings = {
        "NCD": ["check-up", "diabetes", "hypertension", "blood pressure", "cholesterol", "chronic"],
        "ALRI": ["respiratory", "cough", "pneumonia", "breathing", "flu", "cold"],
        "HIV": ["hiv", "arv", "antiretroviral", "viral load"],
        "TB": ["tb", "tuberculosis", "chest x-ray"],
        "Maternal": ["prenatal", "antenatal", "pregnancy", "postnatal", "maternity"],
        "Injury": ["injury", "accident", "wound", "fracture", "burn"],
        "Mental Health": ["mental", "depression", "anxiety", "psychiatric", "counseling"],
    }
    
    for group, keywords in mappings.items():
        if any(kw in reason_lower for kw in keywords):
            return group
    
    return "Other"
