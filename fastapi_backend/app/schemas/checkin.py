from pydantic import BaseModel


class PatientCheckinResponse(BaseModel):
    returning_patient: bool
    patient_uuid: str
    patient_name: str | None
    masked_identifier: str | None
    gender: str | None
    confidence: float
    visit_session_id: str
    session_token: str
    message: str
