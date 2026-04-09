import hashlib

from pinecone import Pinecone

from app.core.config import settings
from app.services.vector_store.base import VectorMatchResult, VectorStore


class PineconeVectorStore(VectorStore):
    def __init__(self):
        if not settings.pinecone_api_key:
            raise ValueError("PINECONE_API_KEY is required for pinecone backend")
        if not settings.pinecone_index_name:
            raise ValueError("PINECONE_INDEX_NAME is required for pinecone backend")

        self.client = Pinecone(api_key=settings.pinecone_api_key)
        self.index = self.client.Index(settings.pinecone_index_name)

    def upsert(self, patient_uuid: str, embedding_vector: list[float]) -> str:
        vector_id = self._vector_id(patient_uuid, embedding_vector)
        self.index.upsert(
            vectors=[
                {
                    "id": vector_id,
                    "values": embedding_vector,
                    "metadata": {"patient_uuid": patient_uuid},
                }
            ],
            namespace=settings.pinecone_namespace,
        )
        return f"pinecone://{settings.pinecone_index_name}/{vector_id}"

    def search_best(self, embedding_vector: list[float], threshold: float) -> VectorMatchResult:
        result = self.index.query(
            vector=embedding_vector,
            top_k=1,
            include_metadata=True,
            namespace=settings.pinecone_namespace,
        )

        matches = result.get("matches", [])
        if not matches:
            return VectorMatchResult(patient_uuid=None, confidence=0.0)

        top = matches[0]
        score = float(top.get("score", 0.0))
        if score < threshold:
            return VectorMatchResult(patient_uuid=None, confidence=score)

        metadata = top.get("metadata", {})
        return VectorMatchResult(patient_uuid=metadata.get("patient_uuid"), confidence=score)

    @staticmethod
    def _vector_id(patient_uuid: str, embedding_vector: list[float]) -> str:
        fingerprint = hashlib.sha256(str(embedding_vector).encode("utf-8")).hexdigest()
        return f"{patient_uuid}-{fingerprint[:16]}"