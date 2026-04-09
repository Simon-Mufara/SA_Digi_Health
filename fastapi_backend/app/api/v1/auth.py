from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session

from app.core.dependencies import get_current_user
from app.core.database import get_db
from app.core.security import create_access_token, create_refresh_token, decode_token
from app.models.staff import Staff
from app.schemas.auth import Token, UserCreate, UserRead
from app.services.auth_service import AuthService
from app.schemas.common import UserRole
from app.core.security import hash_password

router = APIRouter(prefix="/auth", tags=["auth"])


def ensure_default_accounts(db: Session) -> None:
    defaults = [
        ("DR-001", "doctor"),
        ("CLIN-001", "clinician"),
        ("ADM-001", "admin"),
        ("SEC-001", "security_officer"),
        ("RES-001", "researcher"),
    ]
    for staff_id, role in defaults:
        existing = db.query(Staff).filter(Staff.staff_id == staff_id).first()
        if existing:
            existing.assigned_role = role
            existing.hashed_password = hash_password("1234567")
            continue
        db.add(
            Staff(
                staff_id=staff_id,
                hashed_password=hash_password("1234567"),
                assigned_role=role,
            )
        )
    db.commit()


@router.post("/register", response_model=UserRead, status_code=status.HTTP_201_CREATED)
def register(payload: UserCreate, db: Session = Depends(get_db)):
    try:
        staff = AuthService.register(db, payload)
        return UserRead(id=staff.id, staff_id=staff.staff_id, role=staff.assigned_role)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc


@router.post("/login", response_model=Token)
def login(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    try:
        ensure_default_accounts(db)
        requested_role = form_data.scopes[0] if form_data.scopes else ""
        if not requested_role:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Requested role is required in OAuth2 scope.",
            )
        return AuthService.login(db, form_data.username, form_data.password, requested_role)
    except PermissionError as exc:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=str(exc)) from exc


@router.post("/refresh", response_model=Token)
def refresh_token(refresh_token: str):
    payload = decode_token(refresh_token)
    if payload.get("type") != "refresh":
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid refresh token")

    username = payload.get("sub")
    role = payload.get("role")
    if not username or not role:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Malformed token")

    return Token(
        access_token=create_access_token(subject=username, role=role),
        refresh_token=create_refresh_token(subject=username, role=role),
    )


@router.get("/verify")
def verify_token(current_staff: Staff = Depends(get_current_user)):
    return {"staff_id": current_staff.staff_id, "role": current_staff.assigned_role}
