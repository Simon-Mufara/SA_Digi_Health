from sqlalchemy import Integer, String
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base


class Staff(Base):
    __tablename__ = "staff"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    staff_id: Mapped[str] = mapped_column(String(100), unique=True, index=True, nullable=False)
    hashed_password: Mapped[str] = mapped_column(String(255), nullable=False)
    assigned_role: Mapped[str] = mapped_column(String(32), nullable=False)
