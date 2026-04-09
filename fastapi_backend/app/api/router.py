from fastapi import APIRouter

from .v1 import ai, analytics, auth, biometric, clinical_records, face_recognition, patients, research, sessions, visits

api_router = APIRouter()
api_router.include_router(auth.router)
api_router.include_router(patients.router)
api_router.include_router(clinical_records.router)
api_router.include_router(face_recognition.router)
api_router.include_router(biometric.router)
api_router.include_router(sessions.router)
api_router.include_router(visits.router)
api_router.include_router(analytics.router)
api_router.include_router(ai.router)
api_router.include_router(research.router)
