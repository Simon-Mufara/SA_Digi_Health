from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.security import decode_token
from app.models.staff import Staff
from app.schemas.common import UserRole

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/login")


def get_current_user(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)) -> Staff:
    payload = decode_token(token)
    if payload.get("type") != "access":
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token type")

    staff_id = payload.get("sub")
    if not staff_id:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Missing subject claim")

    user = db.query(Staff).filter(Staff.staff_id == staff_id).first()
    if not user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="User not found")

    return user


def require_role(*allowed_roles: UserRole):
    def role_checker(current_user: Staff = Depends(get_current_user)) -> Staff:
        if current_user.assigned_role not in {role.value for role in allowed_roles}:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Insufficient permissions")
        return current_user

    return role_checker
