from pydantic import BaseModel


class SessionCreateResponse(BaseModel):
    patient_uuid: str
    visit_session_id: str
    result: str
    image_received: bool
    warning: str | None = None
