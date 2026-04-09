import json
import math

from sqlalchemy.orm import Session

from app.models.face_recognition import BiometricProfile
from app.services.vector_store.base import VectorMatchResult, VectorStore


class DatabaseVectorStore(VectorStore):
    def __init__(self, db: Session):
        self.db = db

    def upsert(self, patient_uuid: str, embedding_vector: list[float]) -> str:
        # SQL storage is handled by Biometrics table in FaceRecognitionService.
        return f"db://{patient_uuid}"

    def search_best(self, embedding_vector: list[float], threshold: float) -> VectorMatchResult:
        profiles = self.db.query(BiometricProfile).all()

        best_patient_uuid: str | None = None
        best_score = 0.0

        for profile in profiles:
            stored = json.loads(profile.embedding_vector)
            score = self._cosine_similarity(stored, embedding_vector)
            if score > best_score:
                best_score = score
                best_patient_uuid = profile.patient_uuid

        if best_score < threshold:
            return VectorMatchResult(patient_uuid=None, confidence=best_score)

        return VectorMatchResult(patient_uuid=best_patient_uuid, confidence=best_score)

    @staticmethod
    def _cosine_similarity(v1: list[float], v2: list[float]) -> float:
        if len(v1) != len(v2):
            raise ValueError("Embedding dimensions do not match")

        dot = sum(a * b for a, b in zip(v1, v2))
        norm_v1 = math.sqrt(sum(a * a for a in v1))
        norm_v2 = math.sqrt(sum(b * b for b in v2))
        if norm_v1 == 0.0 or norm_v2 == 0.0:
            raise ValueError("Embedding vector must not be zero")

        return dot / (norm_v1 * norm_v2)