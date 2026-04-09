from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from .api.router import api_router
from .core.config import settings
from .core.database import Base, engine
from .models import (  # noqa: F401
    BiometricProfile,
    ClinicalRecord,
    FaceRecognitionEvent,
    Patient,
    Staff,
    User,
    VisitSession,
)


def create_app() -> FastAPI:
    app = FastAPI(title=settings.app_name, version=settings.app_version)
    
    # CORS middleware - allow credentials for cookie-based auth
    app.add_middleware(
        CORSMiddleware,
        allow_origins=[
            "http://localhost:5173",
            "http://127.0.0.1:5173",
            "http://localhost:5174",
            "http://127.0.0.1:5174",
            "http://localhost:5180",
            "http://127.0.0.1:5180",
            "http://localhost:3000",
            "http://127.0.0.1:3000",
            "http://localhost:3001",
            "http://127.0.0.1:3001",
            "http://localhost:3100",
            "http://127.0.0.1:3100",
        ],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    
    app.include_router(api_router, prefix="/api/v1")

    @app.on_event("startup")
    def create_tables_on_startup() -> None:
        Base.metadata.create_all(bind=engine)

    @app.get("/health", tags=["health"])
    def health_check() -> dict[str, str]:
        return {"status": "ok"}

    # Global exception handler - always return JSON, never HTML
    @app.exception_handler(Exception)
    async def global_exception_handler(request: Request, exc: Exception) -> JSONResponse:
        error_type = type(exc).__name__
        error_msg = str(exc) if str(exc) else "An unexpected error occurred"
        return JSONResponse(
            status_code=500,
            content={
                "error": "internal_server_error",
                "message": error_msg,
                "type": error_type,
            },
        )

    return app


app = create_app()
