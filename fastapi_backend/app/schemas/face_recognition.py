from datetime import datetime

from pydantic import BaseModel, ConfigDict


class BiometricEnrollRequest(BaseModel):
    patient_uuid: str
    embedding_vector: list[float]


class BiometricEnrollResponse(BaseModel):
    patient_uuid: str
    face_biometric_hash: str
    vector_ref: str | None
    created_at: datetime


class GateScanRequest(BaseModel):
    embedding_vector: list[float]
    optional_name: str | None = None
    optional_identifier: str | None = None
    gender: str | None = None
    reason: str | None = None


class GateScanResponse(BaseModel):
    patient_uuid: str
    visit_session_id: str
    gate_token: str
    confidence: float
    result: str


class DoctorResolveRequest(BaseModel):
    embedding_vector: list[float]


class DoctorResolveResponse(BaseModel):
    patient_uuid: str | None
    confidence: float
    matched: bool
    result: str
    visit_session_id: str | None


class FaceRecognitionEventRead(BaseModel):
    id: int
    patient_uuid: str | None
    visit_session_id: str | None
    confidence: float
    result: str
    capture_context: str
    captured_at: datetime

    model_config = ConfigDict(from_attributes=True)


class ImageMatchResponse(BaseModel):
    matched: bool
    patient_uuid: str | None
    confidence: float
    result: str


class ImageEnrollResponse(BaseModel):
    patient_uuid: str
    face_biometric_hash: str
    vector_ref: str | None
    embedding_dimension: int
    created_at: datetime