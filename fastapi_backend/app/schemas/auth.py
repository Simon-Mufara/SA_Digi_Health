from pydantic import BaseModel, ConfigDict

from app.schemas.common import UserRole


class UserCreate(BaseModel):
    staff_id: str
    password: str
    role: UserRole


class UserRead(BaseModel):
    id: int
    staff_id: str
    role: UserRole

    model_config = ConfigDict(from_attributes=False)


class Token(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"


class TokenPayload(BaseModel):
    sub: str
    role: UserRole
    type: str
    exp: int
