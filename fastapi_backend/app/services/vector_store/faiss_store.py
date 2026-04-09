import hashlib
from pathlib import Path

import faiss
import numpy as np
from sqlalchemy.orm import Session

from app.core.config import settings
from app.models.face_recognition import BiometricProfile
from app.services.vector_store.base import VectorMatchResult, VectorStore


class FaissVectorStore(VectorStore):
    def __init__(self, db: Session):
        self.db = db
        self.index_path = Path(settings.faiss_index_path)
        self.index_path.parent.mkdir(parents=True, exist_ok=True)

    def upsert(self, patient_uuid: str, embedding_vector: list[float]) -> str:
        matrix = np.array([embedding_vector], dtype="float32")
        dim = matrix.shape[1]

        index = self._load_or_create_index(dim)
        if index.d != dim:
            raise ValueError(
                f"Embedding dimension mismatch for FAISS index. expected={index.d}, provided={dim}"
            )
        faiss.normalize_L2(matrix)
        index.add(matrix)
        faiss.write_index(index, str(self.index_path))

        return f"faiss://{patient_uuid}/{self._vector_hash(embedding_vector)}"

    def search_best(self, embedding_vector: list[float], threshold: float) -> VectorMatchResult:
        profiles = self.db.query(BiometricProfile).all()
        if not profiles:
            return VectorMatchResult(patient_uuid=None, confidence=0.0)

        dim = len(embedding_vector)
        index = self._load_or_create_index(dim)

        if index.ntotal == 0:
            vectors = [np.array([self._deserialize(profile.embedding_vector)], dtype="float32") for profile in profiles]
            for vector in vectors:
                faiss.normalize_L2(vector)
                index.add(vector)
            faiss.write_index(index, str(self.index_path))

        query = np.array([embedding_vector], dtype="float32")
        faiss.normalize_L2(query)

        distances, indices = index.search(query, 1)
        confidence = float(distances[0][0]) if indices[0][0] != -1 else 0.0

        if indices[0][0] == -1 or confidence < threshold:
            return VectorMatchResult(patient_uuid=None, confidence=confidence)

        if indices[0][0] >= len(profiles):
            return VectorMatchResult(patient_uuid=None, confidence=confidence)

        return VectorMatchResult(patient_uuid=profiles[indices[0][0]].patient_uuid, confidence=confidence)

    def _load_or_create_index(self, dim: int):
        if self.index_path.exists():
            return faiss.read_index(str(self.index_path))

        return faiss.IndexFlatIP(dim)

    @staticmethod
    def _deserialize(raw: str) -> list[float]:
        import json

        return json.loads(raw)

    @staticmethod
    def _vector_hash(vector: list[float]) -> str:
        return hashlib.sha256(str(vector).encode("utf-8")).hexdigest()
