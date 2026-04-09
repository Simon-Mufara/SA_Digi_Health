from __future__ import annotations

import sqlite3
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path

import cv2
import numpy as np


@dataclass
class FaceMatchResult:
    matched: bool
    patient_id: str | None
    confidence: float
    message: str


class FaceCaptureService:
    """
    Robust face capture/match service that supports:
    - webcam frame (OpenCV ndarray)
    - fallback uploaded image path
    - fallback uploaded image bytes
    """

    def __init__(
        self,
        sqlite_db_path: str | Path = Path(__file__).resolve().parents[2] / "clinic_local.db",
        match_threshold: float = 0.80,
    ) -> None:
        self.sqlite_db_path = str(sqlite_db_path)
        self.match_threshold = match_threshold
        self._ensure_table()

    def _ensure_table(self) -> None:
        with sqlite3.connect(self.sqlite_db_path) as conn:
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS face_embeddings (
                    patient_id TEXT NOT NULL,
                    embedding_blob BLOB NOT NULL,
                    captured_at TEXT NOT NULL
                )
                """
            )
            conn.commit()

    @staticmethod
    def _is_black_frame(image: np.ndarray) -> bool:
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        return float(gray.mean()) < 5.0 and float(gray.std()) < 2.0

    @staticmethod
    def _load_image(
        webcam_frame: np.ndarray | None,
        uploaded_image_path: str | Path | None,
        uploaded_image_bytes: bytes | None,
    ) -> np.ndarray:
        if webcam_frame is not None:
            if not isinstance(webcam_frame, np.ndarray) or webcam_frame.size == 0:
                raise ValueError("Invalid webcam frame received.")
            return webcam_frame

        if uploaded_image_bytes is not None:
            arr = np.frombuffer(uploaded_image_bytes, dtype=np.uint8)
            image = cv2.imdecode(arr, cv2.IMREAD_COLOR)
            if image is None:
                raise ValueError("Uploaded image bytes could not be decoded.")
            return image

        if uploaded_image_path is not None:
            image = cv2.imread(str(uploaded_image_path))
            if image is None:
                raise ValueError("Uploaded image file could not be read.")
            return image

        raise ValueError("No input image provided. Pass a webcam frame or uploaded image.")

    @staticmethod
    def _extract_embedding(image_bgr: np.ndarray) -> np.ndarray:
        # Try face_recognition first, fallback to deepface.
        try:
            import face_recognition  # type: ignore

            rgb = cv2.cvtColor(image_bgr, cv2.COLOR_BGR2RGB)
            locations = face_recognition.face_locations(rgb, model="hog")
            if not locations:
                raise ValueError("No face detected in the image.")
            encodings = face_recognition.face_encodings(rgb, known_face_locations=locations)
            if not encodings:
                raise ValueError("Face detected but embedding extraction failed.")
            return np.asarray(encodings[0], dtype=np.float32)
        except ImportError:
            pass

        try:
            from deepface import DeepFace  # type: ignore
        except Exception as exc:
            raise ValueError(
                "No face backend available. Install deepface or face_recognition."
            ) from exc

        try:
            # DeepFace accepts numpy image arrays directly.
            representations = DeepFace.represent(img_path=image_bgr, enforce_detection=True)
        except Exception as exc:
            raise ValueError(f"No face detected or embedding failed: {exc}") from exc

        if not representations:
            raise ValueError("No face detected in the image.")
        embedding = representations[0].get("embedding")
        if embedding is None:
            raise ValueError("Embedding extraction returned empty data.")
        return np.asarray(embedding, dtype=np.float32)

    def capture_and_store_embedding(
        self,
        patient_id: str,
        webcam_frame: np.ndarray | None = None,
        uploaded_image_path: str | Path | None = None,
        uploaded_image_bytes: bytes | None = None,
    ) -> dict:
        image = self._load_image(webcam_frame, uploaded_image_path, uploaded_image_bytes)

        if self._is_black_frame(image):
            raise ValueError(
                "Webcam frame is all black. Camera stream may have failed or is unavailable."
            )

        embedding = self._extract_embedding(image)
        captured_at = datetime.now(timezone.utc).isoformat()

        with sqlite3.connect(self.sqlite_db_path) as conn:
            conn.execute(
                """
                INSERT INTO face_embeddings (patient_id, embedding_blob, captured_at)
                VALUES (?, ?, ?)
                """,
                (patient_id, embedding.astype(np.float32).tobytes(), captured_at),
            )
            conn.commit()

        return {
            "patient_id": patient_id,
            "captured_at": captured_at,
            "embedding_dimension": int(embedding.shape[0]),
        }

    def search_existing_embeddings(
        self,
        webcam_frame: np.ndarray | None = None,
        uploaded_image_path: str | Path | None = None,
        uploaded_image_bytes: bytes | None = None,
    ) -> FaceMatchResult:
        image = self._load_image(webcam_frame, uploaded_image_path, uploaded_image_bytes)

        if self._is_black_frame(image):
            raise ValueError(
                "Webcam frame is all black. Camera stream may have failed or is unavailable."
            )

        query = self._extract_embedding(image)
        query_norm = np.linalg.norm(query)
        if query_norm == 0:
            raise ValueError("Invalid query embedding (zero norm).")

        with sqlite3.connect(self.sqlite_db_path) as conn:
            rows = conn.execute(
                "SELECT patient_id, embedding_blob, captured_at FROM face_embeddings"
            ).fetchall()

        if not rows:
            return FaceMatchResult(
                matched=False,
                patient_id=None,
                confidence=0.0,
                message="No stored embeddings found.",
            )

        best_patient: str | None = None
        best_score = -1.0
        for patient_id, blob, _captured_at in rows:
            emb = np.frombuffer(blob, dtype=np.float32)
            if emb.size == 0:
                continue
            denom = float(np.linalg.norm(emb) * query_norm)
            if denom == 0:
                continue
            cosine = float(np.dot(query, emb) / denom)
            confidence = max(0.0, min(1.0, (cosine + 1.0) / 2.0))
            if confidence > best_score:
                best_score = confidence
                best_patient = patient_id

        if best_patient is None:
            return FaceMatchResult(
                matched=False,
                patient_id=None,
                confidence=0.0,
                message="No valid embeddings available for matching.",
            )

        matched = best_score >= self.match_threshold
        return FaceMatchResult(
            matched=matched,
            patient_id=best_patient if matched else None,
            confidence=round(best_score, 4),
            message="Match found." if matched else "No match above threshold.",
        )
