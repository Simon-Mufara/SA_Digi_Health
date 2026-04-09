from pathlib import Path

from app.core.config import settings


class FaceEmbeddingService:
    @staticmethod
    def extract_embedding_from_image_path(image_path: str) -> list[float]:
        if not Path(image_path).exists():
            raise ValueError("Image file not found")

        try:
            from deepface import DeepFace
        except ModuleNotFoundError as exc:
            raise ValueError(
                "DeepFace is not installed. Install deepface and opencv-python-headless to use image embedding endpoints."
            ) from exc
        except Exception as exc:
            raise ValueError(f"DeepFace runtime initialization failed: {exc}") from exc

        try:
            representations = DeepFace.represent(
                img_path=image_path,
                model_name=settings.face_embedding_model,
                detector_backend=settings.face_detector_backend,
                enforce_detection=settings.face_enforce_detection,
            )
        except Exception as exc:
            raise ValueError(f"Embedding extraction failed: {exc}") from exc

        if not representations:
            raise ValueError("No face embedding extracted")

        embedding = representations[0].get("embedding")
        if not embedding:
            raise ValueError("Embedding data missing from model response")

        return [float(value) for value in embedding]
