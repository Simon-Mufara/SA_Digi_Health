import base64
import hashlib
import json
import os
from datetime import datetime, timedelta, timezone

from cryptography.exceptions import InvalidTag
from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from jose import JWTError, jwt
from passlib.context import CryptContext

from app.core.config import settings

pwd_context = CryptContext(schemes=["pbkdf2_sha256"], deprecated="auto")


class FieldKeyManager:
    def __init__(self) -> None:
        try:
            raw_keys = json.loads(settings.field_encryption_keys_json)
        except json.JSONDecodeError as exc:
            raise ValueError("FIELD_ENCRYPTION_KEYS_JSON must be valid JSON") from exc

        if not isinstance(raw_keys, dict) or not raw_keys:
            raise ValueError("FIELD_ENCRYPTION_KEYS_JSON must contain at least one key")

        self.keys: dict[str, bytes] = {}
        for key_id, key_value in raw_keys.items():
            self.keys[str(key_id)] = self._decode_key(str(key_value))

        self.active_key_id = settings.field_encryption_active_key_id
        if self.active_key_id not in self.keys:
            raise ValueError("FIELD_ENCRYPTION_ACTIVE_KEY_ID must exist in FIELD_ENCRYPTION_KEYS_JSON")

    @staticmethod
    def _decode_key(value: str) -> bytes:
        padded = value + "=" * (-len(value) % 4)
        try:
            raw = base64.urlsafe_b64decode(padded.encode("utf-8"))
        except Exception as exc:
            raise ValueError("Invalid base64 key in FIELD_ENCRYPTION_KEYS_JSON") from exc

        if len(raw) not in (16, 24, 32):
            raise ValueError("AES key length must be 16, 24, or 32 bytes")

        return raw

    def active_key(self) -> tuple[str, bytes]:
        return self.active_key_id, self.keys[self.active_key_id]

    def get(self, key_id: str) -> bytes | None:
        return self.keys.get(key_id)

    def all_keys(self) -> list[tuple[str, bytes]]:
        return list(self.keys.items())


field_key_manager = FieldKeyManager()


def hash_password(password: str) -> str:
    return pwd_context.hash(password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)


def create_access_token(subject: str, role: str) -> str:
    expires = datetime.now(timezone.utc) + timedelta(minutes=settings.jwt_access_token_expire_minutes)
    payload = {"sub": subject, "role": role, "type": "access", "exp": expires}
    return jwt.encode(payload, settings.jwt_secret_key, algorithm=settings.jwt_algorithm)


def create_refresh_token(subject: str, role: str) -> str:
    expires = datetime.now(timezone.utc) + timedelta(minutes=settings.jwt_refresh_token_expire_minutes)
    payload = {"sub": subject, "role": role, "type": "refresh", "exp": expires}
    return jwt.encode(payload, settings.jwt_secret_key, algorithm=settings.jwt_algorithm)


def create_gate_token(patient_uuid: str, visit_session_id: str) -> str:
    expires = datetime.now(timezone.utc) + timedelta(minutes=settings.gate_token_expire_minutes)
    payload = {
        "sub": patient_uuid,
        "visit_session_id": visit_session_id,
        "type": "gate_session",
        "exp": expires,
    }
    return jwt.encode(payload, settings.jwt_secret_key, algorithm=settings.jwt_algorithm)


def decode_token(token: str) -> dict:
    try:
        payload = jwt.decode(token, settings.jwt_secret_key, algorithms=[settings.jwt_algorithm])
        return payload
    except JWTError as exc:
        raise ValueError("Invalid token") from exc


def stable_hash(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def _b64_encode(raw: bytes) -> str:
    return base64.urlsafe_b64encode(raw).decode("utf-8")


def _b64_decode(value: str) -> bytes:
    padded = value + "=" * (-len(value) % 4)
    return base64.urlsafe_b64decode(padded.encode("utf-8"))


def encrypt_text(value: str) -> str:
    key_id, key = field_key_manager.active_key()
    nonce = os.urandom(12)
    cipher = AESGCM(key)
    ciphertext = cipher.encrypt(nonce, value.encode("utf-8"), None)
    return f"v1:{key_id}:{_b64_encode(nonce)}:{_b64_encode(ciphertext)}"


def decrypt_text(value: str) -> str:
    parts = value.split(":", 3)
    if len(parts) != 4:
        raise ValueError("Encrypted field payload is malformed")

    version, key_id, nonce_b64, ciphertext_b64 = parts
    if version != "v1":
        raise ValueError("Unsupported encrypted field payload version")

    nonce = _b64_decode(nonce_b64)
    ciphertext = _b64_decode(ciphertext_b64)

    key = field_key_manager.get(key_id)
    attempted_keys: list[tuple[str, bytes]] = []
    if key is not None:
        attempted_keys.append((key_id, key))

    for candidate_id, candidate_key in field_key_manager.all_keys():
        if candidate_id != key_id:
            attempted_keys.append((candidate_id, candidate_key))

    for _, candidate_key in attempted_keys:
        try:
            plain = AESGCM(candidate_key).decrypt(nonce, ciphertext, None)
            return plain.decode("utf-8")
        except InvalidTag:
            continue

    raise ValueError("Unable to decrypt field with configured keys")
