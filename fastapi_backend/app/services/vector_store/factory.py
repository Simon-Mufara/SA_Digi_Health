from sqlalchemy.orm import Session

from app.core.config import settings
from app.services.vector_store.base import VectorStore


def build_vector_store(db: Session) -> VectorStore:
    backend = settings.vector_store_backend.lower()

    if backend == "database":
        from app.services.vector_store.database_store import DatabaseVectorStore
        return DatabaseVectorStore(db)
    if backend == "faiss":
        from app.services.vector_store.faiss_store import FaissVectorStore
        return FaissVectorStore(db)
    if backend == "pinecone":
        from app.services.vector_store.pinecone_store import PineconeVectorStore
        return PineconeVectorStore()

    raise ValueError(f"Unsupported vector backend: {settings.vector_store_backend}")
