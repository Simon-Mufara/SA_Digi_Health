"""
AI-powered clinical summary endpoints for YARA.
Uses Google Gemini API for generating patient summaries.
Implements database caching with 24h TTL.
"""
import asyncio
from datetime import datetime, timedelta
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Path, Query
from pydantic import BaseModel
from sqlalchemy import desc
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.database import get_db
from app.core.dependencies import require_role
from app.models.staff import Staff
from app.models.patient import Patient
from app.models.visit_session import VisitSession
from app.schemas.common import UserRole
from app.services.ai_service import generate_clinical_summary, check_gemini_status

router = APIRouter(prefix="/ai", tags=["ai"])


# Response models
class AISummaryResponse(BaseModel):
    patient_uuid: str
    summary: str
    generated_at: datetime
    model_version: str
    is_cached: bool = False
    is_fallback: bool = False


class AIHealthResponse(BaseModel):
    service: str
    status: str
    gemini_configured: bool
    model: str
    cache_ttl_hours: int


# Database-backed cache table simulation (using in-memory for now, 
# but structured for easy migration to ai_summaries table)
_db_cache: dict = {}


def _get_cached_summary_from_db(
    db: Session, 
    patient_uuid: str,
    last_visit_time: Optional[datetime] = None,
) -> Optional[dict]:
    """
    Check for valid cached summary.
    
    Returns None if:
    - No cache exists
    - Cache is older than 24 hours
    - A new visit was added since the cache was generated
    """
    if patient_uuid not in _db_cache:
        return None
    
    cached = _db_cache[patient_uuid]
    cache_age = datetime.utcnow() - cached["generated_at"]
    
    # Check TTL
    if cache_age > timedelta(hours=settings.ai_summary_cache_hours):
        del _db_cache[patient_uuid]
        return None
    
    # Check if new visit was added since cache generation
    if last_visit_time and last_visit_time > cached["generated_at"]:
        del _db_cache[patient_uuid]
        return None
    
    return cached


def _save_summary_to_db(
    db: Session,
    patient_uuid: str,
    summary: str,
    model_version: str,
    is_fallback: bool,
) -> dict:
    """Save summary to cache (database in production)."""
    entry = {
        "summary": summary,
        "generated_at": datetime.utcnow(),
        "model_version": model_version,
        "is_fallback": is_fallback,
    }
    _db_cache[patient_uuid] = entry
    return entry


def _calculate_age_group(identifier: Optional[str]) -> str:
    """Calculate age group from SA ID."""
    if not identifier or len(identifier) < 6:
        return "Unknown age"
    try:
        year_part = int(identifier[0:2])
        birth_year = 2000 + year_part if year_part <= 30 else 1900 + year_part
        age = datetime.now().year - birth_year
        if age < 5:
            return "Infant/Toddler (0-4)"
        elif age < 15:
            return "Child (5-14)"
        elif age < 50:
            return "Adult (15-49)"
        elif age < 65:
            return "Middle-aged (50-64)"
        else:
            return "Elderly (65+)"
    except (ValueError, TypeError):
        return "Unknown age"


@router.get("/summarise/{patient_uuid}", response_model=AISummaryResponse)
async def get_patient_summary(
    patient_uuid: str = Path(..., description="Patient UUID"),
    force: bool = Query(False, description="Force regeneration ignoring cache"),
    db: Session = Depends(get_db),
    staff: Staff = Depends(require_role(UserRole.DOCTOR)),
):
    """
    Get AI-generated clinical summary for a patient.
    
    Caching behavior:
    - Returns cached summary if valid (< 24h old, no new visits)
    - Set force=true to regenerate regardless of cache
    - Always shows generated_at timestamp for recency awareness
    
    Requires: doctor role
    """
    # Verify patient exists
    patient = db.query(Patient).filter(Patient.patient_uuid == patient_uuid).first()
    if not patient:
        raise HTTPException(status_code=404, detail="Patient not found")
    
    # Get latest visit time
    latest_visit = db.query(VisitSession).filter(
        VisitSession.patient_uuid == patient_uuid
    ).order_by(desc(VisitSession.entry_time)).first()
    
    last_visit_time = latest_visit.entry_time if latest_visit else None
    
    # Check cache unless force refresh
    if not force:
        cached = _get_cached_summary_from_db(db, patient_uuid, last_visit_time)
        if cached:
            return AISummaryResponse(
                patient_uuid=patient_uuid,
                summary=cached["summary"],
                generated_at=cached["generated_at"],
                model_version=cached["model_version"],
                is_cached=True,
                is_fallback=cached.get("is_fallback", False),
            )
    
    # Fetch last 10 visits
    visits = db.query(VisitSession).filter(
        VisitSession.patient_uuid == patient_uuid
    ).order_by(desc(VisitSession.entry_time)).limit(10).all()
    
    # Build patient profile
    patient_profile = {
        "age_group": _calculate_age_group(patient.identifier),
        "gender": patient.gender or "Unknown gender",
    }
    
    # Format visits for AI
    visits_data = [
        {
            "date": v.entry_time.strftime("%Y-%m-%d"),
            "reason": v.reason,
            "status": v.status,
            "outcome": v.outcome,
        }
        for v in visits
    ]
    
    # No vitals in current schema, pass None
    latest_vitals = None
    
    # Generate summary (async)
    result = await generate_clinical_summary(
        patient_id=patient_uuid,
        patient_profile=patient_profile,
        visits=visits_data,
        latest_vitals=latest_vitals,
    )
    
    # Save to cache
    _save_summary_to_db(
        db=db,
        patient_uuid=patient_uuid,
        summary=result["summary"],
        model_version=result["model_version"],
        is_fallback=result["is_fallback"],
    )
    
    return AISummaryResponse(
        patient_uuid=patient_uuid,
        summary=result["summary"],
        generated_at=result["generated_at"],
        model_version=result["model_version"],
        is_cached=False,
        is_fallback=result["is_fallback"],
    )


@router.get("/health", response_model=AIHealthResponse)
def ai_health_check():
    """Check AI service health and configuration status."""
    status_info = check_gemini_status()
    
    return AIHealthResponse(
        service="ai-summary",
        status="ready" if status_info["configured"] else "fallback",
        gemini_configured=status_info["configured"],
        model=status_info["model"],
        cache_ttl_hours=status_info["cache_hours"],
    )


@router.delete("/cache/{patient_uuid}")
def clear_patient_cache(
    patient_uuid: str = Path(..., description="Patient UUID"),
    staff: Staff = Depends(require_role(UserRole.DOCTOR)),
):
    """Clear cached summary for a specific patient."""
    if patient_uuid in _db_cache:
        del _db_cache[patient_uuid]
        return {"message": "Cache cleared", "patient_uuid": patient_uuid}
    return {"message": "No cache found", "patient_uuid": patient_uuid}
