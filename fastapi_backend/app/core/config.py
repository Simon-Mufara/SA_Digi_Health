from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "Clinical Platform API"
    app_version: str = "2.0.0"
    environment: str = "development"

    database_url: str = "sqlite+pysqlite:///./clinic_local.db"

    jwt_secret_key: str = "replace-with-strong-secret"
    jwt_algorithm: str = "HS256"
    jwt_access_token_expire_minutes: int = 15
    jwt_refresh_token_expire_minutes: int = 8 * 60
    gate_token_expire_minutes: int = 20

    field_encryption_active_key_id: str = "key-2026-01"
    field_encryption_keys_json: str = '{"key-2026-01":"MDEyMzQ1Njc4OWFiY2RlZjAxMjM0NTY3ODlhYmNkZWY="}'

    llm_provider: str = "mock"
    llm_model: str = "gpt-4.1-mini"
    llm_api_key: str | None = None

    # Gemini AI settings
    gemini_api_key: str | None = None
    gemini_model: str = "gemini-1.5-flash"
    gemini_max_tokens: int = 300
    gemini_temperature: float = 0.2
    ai_summary_cache_hours: int = 24

    face_match_threshold: float = 0.82
    face_embedding_model: str = "Facenet512"
    face_detector_backend: str = "opencv"
    face_enforce_detection: bool = True

    vector_store_backend: str = "database"
    faiss_index_path: str = "./data/faiss.index"
    pinecone_api_key: str | None = None
    pinecone_index_name: str | None = None
    pinecone_namespace: str = "patients"

    model_config = SettingsConfigDict(env_file=".env", case_sensitive=False)


settings = Settings()
