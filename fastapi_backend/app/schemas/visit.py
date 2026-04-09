from datetime import datetime

from pydantic import BaseModel


class VisitSessionRead(BaseModel):
    visit_session_id: str
    patient_uuid: str
    reason: str | None
    status: str
    entry_time: datetime
    doctor_interaction_time: datetime | None
    outcome: str | None


class VisitOutcomeUpdate(BaseModel):
    outcome: str
    status: str = "completed"