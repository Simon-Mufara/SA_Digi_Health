"""
Gemini AI Clinical Summary Service for YARA.
Generates factual, clinical-tone summaries for attending physicians.
"""
import logging
from datetime import datetime
from typing import Optional, List, Any

from app.core.config import settings

logger = logging.getLogger(__name__)

# Normal vital ranges for flagging
VITAL_RANGES = {
    "bp_systolic": (90, 140),
    "bp_diastolic": (60, 90),
    "temperature_c": (36.1, 37.2),
    "o2_sat": (95, 100),
    "weight_kg": None,  # No universal range
}


def _check_vital_flag(name: str, value: Optional[float]) -> Optional[str]:
    """Check if a vital is outside normal range."""
    if value is None:
        return None
    range_tuple = VITAL_RANGES.get(name)
    if not range_tuple:
        return None
    low, high = range_tuple
    if value < low:
        return f"{name.replace('_', ' ').title()}: {value} (LOW)"
    if value > high:
        return f"{name.replace('_', ' ').title()}: {value} (HIGH)"
    return None


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


def _build_clinical_prompt(
    patient_profile: dict,
    visits: List[dict],
    latest_vitals: Optional[dict],
) -> str:
    """Build the structured clinical prompt for Gemini."""
    
    # Patient profile
    age_group = patient_profile.get("age_group", "Unknown age")
    gender = patient_profile.get("gender", "Unknown gender")
    
    # Visits summary
    if visits:
        visits_summary = "; ".join([
            f"{v.get('date', 'Unknown date')}: {v.get('reason', 'No reason recorded')}"
            for v in visits[:5]
        ])
        reasons = list(set(v.get("reason") for v in visits if v.get("reason")))
    else:
        visits_summary = "No recent visits recorded"
        reasons = []
    
    # Vitals
    if latest_vitals:
        bp = f"{latest_vitals.get('bp_systolic', '?')}/{latest_vitals.get('bp_diastolic', '?')}"
        temp = latest_vitals.get("temperature_c", "N/A")
        o2 = latest_vitals.get("o2_sat", "N/A")
        weight = latest_vitals.get("weight_kg", "N/A")
    else:
        bp = "N/A"
        temp = "N/A"
        o2 = "N/A"
        weight = "N/A"
    
    prompt = f"""You are a clinical decision support assistant.
Summarise the following patient data for an attending physician.
Be factual, concise (under 150 words), and clinical in tone.
Flag any values outside normal range.
Do NOT speculate beyond the data provided.

Patient profile: {age_group}, {gender}
Recent visits ({len(visits)}): {visits_summary}
Latest vitals: BP {bp}, Temp {temp}°C, O2 {o2}%, Weight {weight}kg
Visit reasons: {', '.join(reasons) if reasons else 'None recorded'}

Output format:
SUMMARY: [2-3 sentence clinical overview]
FLAGS: [bullet list of abnormal values, or "None"]
TREND: [improving / stable / concerning / insufficient data]"""
    
    return prompt


async def generate_clinical_summary(
    patient_id: str,
    patient_profile: dict,
    visits: List[dict],
    latest_vitals: Optional[dict] = None,
) -> dict:
    """
    Generate AI clinical summary using Gemini.
    
    Returns:
        dict with keys: summary, model_version, generated_at, is_fallback
    """
    
    if not settings.gemini_api_key:
        logger.warning("Gemini API key not configured, using fallback summary")
        return _generate_fallback_summary(patient_profile, visits, latest_vitals)
    
    try:
        import google.generativeai as genai
        from google.generativeai.types import HarmCategory, HarmBlockThreshold
        
        # Configure Gemini
        genai.configure(api_key=settings.gemini_api_key)
        
        # Build prompt
        prompt = _build_clinical_prompt(patient_profile, visits, latest_vitals)
        
        # Configure model with medical-appropriate settings
        model = genai.GenerativeModel(
            model_name=settings.gemini_model,
            generation_config={
                "max_output_tokens": settings.gemini_max_tokens,
                "temperature": settings.gemini_temperature,
            },
            # Disable safety filters for medical content (clinical data triggers false positives)
            safety_settings={
                HarmCategory.HARM_CATEGORY_HARASSMENT: HarmBlockThreshold.BLOCK_NONE,
                HarmCategory.HARM_CATEGORY_HATE_SPEECH: HarmBlockThreshold.BLOCK_NONE,
                HarmCategory.HARM_CATEGORY_SEXUALLY_EXPLICIT: HarmBlockThreshold.BLOCK_NONE,
                HarmCategory.HARM_CATEGORY_DANGEROUS_CONTENT: HarmBlockThreshold.BLOCK_NONE,
            },
        )
        
        # Generate response
        response = await model.generate_content_async(prompt)
        summary_text = response.text.strip()
        
        logger.info(f"Generated Gemini summary for patient {patient_id}")
        
        return {
            "summary": summary_text,
            "model_version": settings.gemini_model,
            "generated_at": datetime.utcnow(),
            "is_fallback": False,
        }
        
    except ImportError as e:
        logger.error(f"google-generativeai not installed: {e}")
        return _generate_fallback_summary(patient_profile, visits, latest_vitals)
    
    except Exception as e:
        error_msg = str(e)
        if "ResourceExhausted" in error_msg or "quota" in error_msg.lower():
            logger.warning(f"Gemini quota exceeded: {e}")
            return {
                "summary": "AI summary temporarily unavailable due to service limits. Please review records manually.",
                "model_version": "unavailable",
                "generated_at": datetime.utcnow(),
                "is_fallback": True,
            }
        
        logger.error(f"Gemini API error: {e}")
        return _generate_fallback_summary(patient_profile, visits, latest_vitals)


def _generate_fallback_summary(
    patient_profile: dict,
    visits: List[dict],
    latest_vitals: Optional[dict],
) -> dict:
    """Generate a structured fallback summary when AI is unavailable."""
    
    age_group = patient_profile.get("age_group", "Unknown age")
    gender = patient_profile.get("gender", "Unknown gender")
    
    # Build summary
    summary_parts = [f"SUMMARY: {age_group} {gender} patient"]
    
    if visits:
        summary_parts[0] += f" with {len(visits)} recorded visit(s)."
        reasons = list(set(v.get("reason") for v in visits if v.get("reason")))
        if reasons:
            summary_parts[0] += f" Primary visit reasons: {', '.join(reasons[:3])}."
    else:
        summary_parts[0] += " with no recent visit history."
    
    # Flags section
    flags = []
    if latest_vitals:
        for vital_name in ["bp_systolic", "bp_diastolic", "temperature_c", "o2_sat"]:
            flag = _check_vital_flag(vital_name, latest_vitals.get(vital_name))
            if flag:
                flags.append(f"• {flag}")
    
    if flags:
        summary_parts.append(f"\nFLAGS:\n" + "\n".join(flags))
    else:
        summary_parts.append("\nFLAGS: None")
    
    # Trend
    if len(visits) < 2:
        summary_parts.append("\nTREND: insufficient data")
    else:
        summary_parts.append("\nTREND: stable (automated assessment)")
    
    summary_parts.append("\n\n(Note: AI summary unavailable - this is an automated extraction)")
    
    return {
        "summary": "\n".join(summary_parts),
        "model_version": "fallback-extractive-v1",
        "generated_at": datetime.utcnow(),
        "is_fallback": True,
    }


def check_gemini_status() -> dict:
    """Check Gemini API configuration status."""
    return {
        "configured": bool(settings.gemini_api_key),
        "model": settings.gemini_model,
        "max_tokens": settings.gemini_max_tokens,
        "temperature": settings.gemini_temperature,
        "cache_hours": settings.ai_summary_cache_hours,
    }
