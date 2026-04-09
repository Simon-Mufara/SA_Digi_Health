"""add_patient_identifier_encryption_fields

Revision ID: 20260330_02
Revises: 20260330_01
Create Date: 2026-03-30
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "20260330_02"
down_revision: Union[str, None] = "20260330_01"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("patients", sa.Column("encrypted_identifier", sa.String(length=2000), nullable=True))
    op.add_column("patients", sa.Column("identifier_hash", sa.String(length=64), nullable=True))
    op.create_index("ix_patients_identifier_hash", "patients", ["identifier_hash"], unique=False)

    op.alter_column(
        "patients",
        "encrypted_name",
        existing_type=sa.String(length=400),
        type_=sa.String(length=2000),
        existing_nullable=True,
    )


def downgrade() -> None:
    op.alter_column(
        "patients",
        "encrypted_name",
        existing_type=sa.String(length=2000),
        type_=sa.String(length=400),
        existing_nullable=True,
    )
    op.drop_index("ix_patients_identifier_hash", table_name="patients")
    op.drop_column("patients", "identifier_hash")
    op.drop_column("patients", "encrypted_identifier")