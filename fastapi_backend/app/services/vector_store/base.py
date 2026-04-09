from dataclasses import dataclass
from typing import Protocol


@dataclass
class VectorMatchResult:
    patient_uuid: str | None
    confidence: float


class VectorStore(Protocol):
    def upsert(self, patient_uuid: str, embedding_vector: list[float]) -> str:
        ...

    def search_best(self, embedding_vector: list[float], threshold: float) -> VectorMatchResult:
        ...