from sqlalchemy.orm import Session

from app.core.security import (
    create_access_token,
    create_refresh_token,
    hash_password,
    verify_password,
)
from app.models.staff import Staff
from app.schemas.auth import Token, UserCreate


class AuthService:
    @staticmethod
    def register(db: Session, payload: UserCreate) -> Staff:
        existing = db.query(Staff).filter(Staff.staff_id == payload.staff_id).first()
        if existing:
            raise ValueError("Staff ID already exists")

        user = Staff(
            staff_id=payload.staff_id,
            hashed_password=hash_password(payload.password),
            assigned_role=payload.role.value,
        )
        db.add(user)
        db.commit()
        db.refresh(user)
        return user

    @staticmethod
    def login(db: Session, staff_id: str, password: str, requested_role: str) -> Token:
        user = db.query(Staff).filter(Staff.staff_id == staff_id).first()
        if not user or not verify_password(password, user.hashed_password):
            raise ValueError("Invalid credentials")
        if requested_role != user.assigned_role:
            raise PermissionError("Role not assigned to this account")

        return Token(
            access_token=create_access_token(subject=user.staff_id, role=user.assigned_role),
            refresh_token=create_refresh_token(subject=user.staff_id, role=user.assigned_role),
        )
