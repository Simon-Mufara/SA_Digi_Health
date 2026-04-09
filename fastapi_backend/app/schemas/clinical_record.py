from datetime import datetime

from pydantic import BaseModel, ConfigDict


class ClinicalRecordCreate(BaseModel):
    patient_uuid: str
    diagnosis: str
    medication: str
    notes: str
    attending_doctor: str


class ClinicalRecordRead(BaseModel):
    record_uuid: str
    patient_uuid: str
    diagnosis: str
    medication: str
    notes: str
    attending_doctor: str
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)