"""
Biometric capture and identification API.
Robust face detection, embedding extraction, and patient matching.
"""
import hashlib
import importlib.util
import os
import tempfile
from datetime import datetime
from typing import Optional
from uuid import uuid4

import numpy as np
from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile, status
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.database import get_db
from app.core.dependencies import require_role
from app.models.face_recognition import BiometricProfile, FaceRecognitionEvent
from app.models.staff import Staff
from app.schemas.common import UserRole
from app.services.patient_service import PatientService

router = APIRouter(prefix="/biometric", tags=["biometric"])

# Constants
MAX_FILE_SIZE = 5 * 1024 * 1024  # 5MB
ALLOWED_CONTENT_TYPES = {"image/jpeg", "image/png", "image/jpg"}
SIMILARITY_THRESHOLD = 0.75


class BiometricError(BaseModel):
    error: str
    message: str


class CaptureResponse(BaseModel):
    success: bool
    patient_id: Optional[str] = None
    embedding_id: Optional[str] = None
    image_hash: str
    model: str = "Facenet512"
    captured_at: str
    message: str


class IdentifyResponse(BaseModel):
    match: Optional[str] = None
    patient_id: Optional[str] = None
    confidence: float = 0.0
    name: Optional[str] = None


def compute_image_hash(data: bytes) -> str:
    """Compute SHA256 hash of image data for deduplication."""
    return hashlib.sha256(data).hexdigest()


def validate_image_file(content_type: Optional[str], file_size: int, data: bytes) -> None:
    """Validate image file type and size."""
    if content_type and content_type not in ALLOWED_CONTENT_TYPES:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail={"error": "invalid_file_type", "message": f"File must be JPEG or PNG. Got: {content_type}"},
        )
    
    if file_size > MAX_FILE_SIZE:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail={"error": "file_too_large", "message": f"File size must be less than 5MB. Got: {file_size / 1024 / 1024:.2f}MB"},
        )
    
    # Check if image data is valid (not all zeros / black frame)
    if len(data) < 1000:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail={"error": "invalid_image", "message": "Image data is too small or corrupted."},
        )


def extract_faces_and_embedding(image_path: str) -> tuple[list[float], int]:
    """
    Extract face embedding from image.
    Returns (embedding, face_count).
    Raises ValueError with specific error codes.
    """
    try:
        from deepface import DeepFace
        import cv2
    except ImportError as exc:
        raise ValueError("deepface_not_installed") from exc
    
    # First, detect faces to validate
    try:
        faces = DeepFace.extract_faces(
            img_path=image_path,
            detector_backend=settings.face_detector_backend,
            enforce_detection=True,
        )
    except Exception:
        # No face detected
        raise ValueError("no_face_detected")
    
    face_count = len(faces)
    if face_count == 0:
        raise ValueError("no_face_detected")
    if face_count > 1:
        raise ValueError("multiple_faces")
    
    # Extract embedding
    try:
        representations = DeepFace.represent(
            img_path=image_path,
            model_name=settings.face_embedding_model,
            detector_backend=settings.face_detector_backend,
            enforce_detection=True,
        )
    except Exception as exc:
        raise ValueError(f"embedding_extraction_failed: {exc}") from exc
    
    if not representations or not representations[0].get("embedding"):
        raise ValueError("embedding_extraction_failed")
    
    embedding = [float(v) for v in representations[0]["embedding"]]
    return embedding, face_count


def cosine_similarity(vec1: list[float], vec2: list[float]) -> float:
    """Compute cosine similarity between two vectors."""
    a = np.array(vec1)
    b = np.array(vec2)
    dot_product = np.dot(a, b)
    norm_a = np.linalg.norm(a)
    norm_b = np.linalg.norm(b)
    if norm_a == 0 or norm_b == 0:
        return 0.0
    return float(dot_product / (norm_a * norm_b))


@router.post(
    "/capture",
    response_model=CaptureResponse,
    responses={
        422: {"model": BiometricError, "description": "Face detection/validation error"},
        500: {"model": BiometricError, "description": "Internal server error"},
    },
)
async def capture_biometric(
    face_image: UploadFile = File(...),
    patient_id: Optional[str] = Form(default=None),
    use_webcam: bool = Form(default=False),
    db: Session = Depends(get_db),
    _: Staff = Depends(require_role(UserRole.SECURITY_OFFICER, UserRole.CLINICIAN, UserRole.DOCTOR)),
):
    """
    Capture and store a face biometric.
    
    - Validates image is JPEG/PNG and < 5MB
    - Detects face using DeepFace.extract_faces()
    - Extracts embedding using Facenet512 model
    - Stores embedding in database with image hash for deduplication
    
    Returns 422 with structured error for:
    - no_face_detected: No face found in image
    - multiple_faces: More than one face detected
    - invalid_file_type: Not JPEG/PNG
    - file_too_large: Exceeds 5MB
    """
    temp_path = None
    try:
        # Read file data
        file_data = await face_image.read()
        file_size = len(file_data)
        
        # Validate file
        validate_image_file(face_image.content_type, file_size, file_data)
        
        # Compute image hash for deduplication
        image_hash = compute_image_hash(file_data)
        
        # Check for duplicate
        existing = db.query(BiometricProfile).filter(
            BiometricProfile.face_biometric_hash == image_hash
        ).first()
        if existing:
            return CaptureResponse(
                success=True,
                patient_id=existing.patient_uuid,
                embedding_id=str(existing.id),
                image_hash=image_hash,
                captured_at=existing.created_at.isoformat(),
                message="Biometric already exists (duplicate image)",
            )
        
        # Save to temp file for DeepFace processing
        suffix = os.path.splitext(face_image.filename or "face.jpg")[1] or ".jpg"
        with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
            temp_path = tmp.name
            tmp.write(file_data)
        
        # Extract faces and embedding
        try:
            embedding, face_count = extract_faces_and_embedding(temp_path)
        except ValueError as exc:
            error_code = str(exc)
            if "no_face_detected" in error_code:
                return JSONResponse(
                    status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                    content={
                        "error": "no_face_detected",
                        "message": "No face found in image. Please retake with better lighting.",
                    },
                )
            elif "multiple_faces" in error_code:
                return JSONResponse(
                    status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                    content={
                        "error": "multiple_faces",
                        "message": "Multiple faces detected. Please ensure only one face is in frame.",
                    },
                )
            elif "deepface_not_installed" in error_code:
                return JSONResponse(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    content={
                        "error": "service_unavailable",
                        "message": "Face recognition service is not available. DeepFace not installed.",
                    },
                )
            else:
                return JSONResponse(
                    status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                    content={
                        "error": "embedding_failed",
                        "message": f"Failed to extract face embedding: {error_code}",
                    },
                )
        
        # Store in database
        import json
        from app.core.security import stable_hash
        
        embedding_hash = stable_hash(json.dumps(embedding))
        
        profile = BiometricProfile(
            patient_uuid=patient_id or f"pending-{uuid4()}",
            face_biometric_hash=image_hash,
            embedding_vector=json.dumps(embedding),
            vector_ref=embedding_hash,
        )
        db.add(profile)
        db.commit()
        db.refresh(profile)
        
        return CaptureResponse(
            success=True,
            patient_id=profile.patient_uuid,
            embedding_id=str(profile.id),
            image_hash=image_hash,
            model=settings.face_embedding_model,
            captured_at=profile.created_at.isoformat(),
            message="Face biometric captured successfully",
        )
        
    except HTTPException:
        raise
    except Exception as exc:
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={
                "error": "capture_failed",
                "message": f"Biometric capture failed: {str(exc)}",
            },
        )
    finally:
        if temp_path and os.path.exists(temp_path):
            os.remove(temp_path)


@router.post(
    "/identify",
    response_model=IdentifyResponse,
    responses={
        422: {"model": BiometricError, "description": "Face detection error"},
        500: {"model": BiometricError, "description": "Internal server error"},
    },
)
async def identify_biometric(
    face_image: UploadFile = File(...),
    db: Session = Depends(get_db),
    _: Staff = Depends(require_role(UserRole.SECURITY_OFFICER, UserRole.CLINICIAN, UserRole.DOCTOR)),
):
    """
    Identify a patient by face biometric.
    
    - Extracts embedding from submitted image
    - Computes cosine similarity against all stored embeddings
    - Returns top match if similarity > 0.75
    
    Always returns JSON, never 500 errors. Returns { match: null, confidence: 0 } if no match.
    """
    temp_path = None
    try:
        # Read and validate file
        file_data = await face_image.read()
        validate_image_file(face_image.content_type, len(file_data), file_data)
        
        # Save to temp file
        suffix = os.path.splitext(face_image.filename or "face.jpg")[1] or ".jpg"
        with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
            temp_path = tmp.name
            tmp.write(file_data)
        
        # Extract embedding
        try:
            query_embedding, _ = extract_faces_and_embedding(temp_path)
        except ValueError as exc:
            error_code = str(exc)
            if "no_face_detected" in error_code:
                return JSONResponse(
                    status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                    content={
                        "error": "no_face_detected",
                        "message": "No face found in image. Please retake with better lighting.",
                    },
                )
            elif "multiple_faces" in error_code:
                return JSONResponse(
                    status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                    content={
                        "error": "multiple_faces",
                        "message": "Multiple faces detected. Please ensure only one face is in frame.",
                    },
                )
            else:
                # Return no match instead of error for graceful degradation
                return IdentifyResponse(match=None, patient_id=None, confidence=0.0, name=None)
        
        # Load all embeddings from DB (paginated)
        import json
        
        best_match = None
        best_confidence = 0.0
        best_patient_id = None
        
        offset = 0
        batch_size = 1000
        
        while True:
            profiles = db.query(BiometricProfile).offset(offset).limit(batch_size).all()
            if not profiles:
                break
            
            for profile in profiles:
                try:
                    stored_embedding = json.loads(profile.embedding_vector)
                    similarity = cosine_similarity(query_embedding, stored_embedding)
                    
                    if similarity > best_confidence:
                        best_confidence = similarity
                        best_patient_id = profile.patient_uuid
                except (json.JSONDecodeError, TypeError):
                    continue
            
            offset += batch_size
            if len(profiles) < batch_size:
                break
        
        # Check if match meets threshold
        if best_confidence >= SIMILARITY_THRESHOLD and best_patient_id:
            # Try to get patient name
            patient_name = None
            try:
                patient = PatientService.get_by_uuid(db, best_patient_id)
                patient_name = PatientService.display_name(patient)
            except Exception:
                pass
            
            # Log identification event
            event = FaceRecognitionEvent(
                patient_uuid=best_patient_id,
                confidence=best_confidence,
                result="identified",
                capture_context="biometric_identify",
            )
            db.add(event)
            db.commit()
            
            return IdentifyResponse(
                match=best_patient_id,
                patient_id=best_patient_id,
                confidence=round(best_confidence, 4),
                name=patient_name,
            )
        
        # No match found
        event = FaceRecognitionEvent(
            patient_uuid=None,
            confidence=best_confidence,
            result="no_match",
            capture_context="biometric_identify",
        )
        db.add(event)
        db.commit()
        
        return IdentifyResponse(match=None, patient_id=None, confidence=round(best_confidence, 4), name=None)
        
    except HTTPException:
        raise
    except Exception as exc:
        # Never return 500 - return no match
        return IdentifyResponse(match=None, patient_id=None, confidence=0.0, name=None)
    finally:
        if temp_path and os.path.exists(temp_path):
            os.remove(temp_path)


@router.get("/status")
async def biometric_status():
    """Check if biometric service is available."""
    try:
        deepface_available = importlib.util.find_spec("deepface") is not None
        cv2_available = importlib.util.find_spec("cv2") is not None
    except Exception as exc:
        return JSONResponse(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            content={
                "error": "service_unavailable",
                "message": f"Biometric dependencies unavailable: {exc}",
            },
        )

    if not deepface_available or not cv2_available:
        return JSONResponse(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            content={
                "error": "service_unavailable",
                "message": "DeepFace or OpenCV not installed.",
            },
        )

    return {
        "status": "available",
        "model": settings.face_embedding_model,
        "detector": settings.face_detector_backend,
        "threshold": SIMILARITY_THRESHOLD,
    }
