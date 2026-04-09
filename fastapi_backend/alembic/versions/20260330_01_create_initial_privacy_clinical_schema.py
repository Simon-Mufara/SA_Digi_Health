"""create_initial_privacy_clinical_schema

Revision ID: 20260330_01
Revises:
Create Date: 2026-03-30
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "20260330_01"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "users",
        sa.Column("id", sa.Integer(), primary_key=True, nullable=False),
        sa.Column("username", sa.String(length=100), nullable=False),
        sa.Column("hashed_password", sa.String(length=255), nullable=False),
        sa.Column("role", sa.String(length=32), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
    )
    op.create_index("ix_users_id", "users", ["id"], unique=False)
    op.create_index("ix_users_username", "users", ["username"], unique=True)

    op.create_table(
        "patients",
        sa.Column("id", sa.Integer(), primary_key=True, nullable=False),
        sa.Column("patient_uuid", sa.String(length=64), nullable=False),
        sa.Column("encrypted_name", sa.String(length=400), nullable=True),
        sa.Column("name_hash", sa.String(length=64), nullable=True),
        sa.Column("gender", sa.String(length=20), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
    )
    op.create_index("ix_patients_id", "patients", ["id"], unique=False)
    op.create_index("ix_patients_patient_uuid", "patients", ["patient_uuid"], unique=True)
    op.create_index("ix_patients_name_hash", "patients", ["name_hash"], unique=False)

    op.create_table(
        "biometrics",
        sa.Column("id", sa.Integer(), primary_key=True, nullable=False),
        sa.Column("patient_uuid", sa.String(length=64), nullable=False),
        sa.Column("face_biometric_hash", sa.String(length=64), nullable=False),
        sa.Column("embedding_vector", sa.Text(), nullable=False),
        sa.Column("vector_ref", sa.String(length=128), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(["patient_uuid"], ["patients.patient_uuid"], ondelete="CASCADE"),
    )
    op.create_index("ix_biometrics_id", "biometrics", ["id"], unique=False)
    op.create_index("ix_biometrics_patient_uuid", "biometrics", ["patient_uuid"], unique=False)
    op.create_index("ix_biometrics_face_biometric_hash", "biometrics", ["face_biometric_hash"], unique=True)

    op.create_table(
        "visits",
        sa.Column("id", sa.Integer(), primary_key=True, nullable=False),
        sa.Column("visit_session_id", sa.String(length=64), nullable=False),
        sa.Column("patient_uuid", sa.String(length=64), nullable=False),
        sa.Column("reason", sa.String(length=255), nullable=True),
        sa.Column("status", sa.String(length=32), nullable=False),
        sa.Column("entry_time", sa.DateTime(), nullable=False),
        sa.Column("doctor_interaction_time", sa.DateTime(), nullable=True),
        sa.Column("outcome", sa.Text(), nullable=True),
        sa.ForeignKeyConstraint(["patient_uuid"], ["patients.patient_uuid"], ondelete="CASCADE"),
    )
    op.create_index("ix_visits_id", "visits", ["id"], unique=False)
    op.create_index("ix_visits_visit_session_id", "visits", ["visit_session_id"], unique=True)
    op.create_index("ix_visits_patient_uuid", "visits", ["patient_uuid"], unique=False)

    op.create_table(
        "clinical_records",
        sa.Column("id", sa.Integer(), primary_key=True, nullable=False),
        sa.Column("record_uuid", sa.String(length=64), nullable=False),
        sa.Column("patient_uuid", sa.String(length=64), nullable=False),
        sa.Column("diagnosis", sa.String(length=500), nullable=False),
        sa.Column("medication", sa.String(length=500), nullable=False),
        sa.Column("notes", sa.Text(), nullable=False),
        sa.Column("attending_doctor", sa.String(length=120), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(["patient_uuid"], ["patients.patient_uuid"], ondelete="CASCADE"),
    )
    op.create_index("ix_clinical_records_id", "clinical_records", ["id"], unique=False)
    op.create_index("ix_clinical_records_record_uuid", "clinical_records", ["record_uuid"], unique=True)
    op.create_index("ix_clinical_records_patient_uuid", "clinical_records", ["patient_uuid"], unique=False)

    op.create_table(
        "face_recognition_events",
        sa.Column("id", sa.Integer(), primary_key=True, nullable=False),
        sa.Column("patient_uuid", sa.String(length=64), nullable=True),
        sa.Column("visit_session_id", sa.String(length=64), nullable=True),
        sa.Column("confidence", sa.Float(), nullable=False),
        sa.Column("result", sa.String(length=32), nullable=False),
        sa.Column("capture_context", sa.String(length=32), nullable=False),
        sa.Column("captured_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(["patient_uuid"], ["patients.patient_uuid"], ondelete="SET NULL"),
    )
    op.create_index("ix_face_recognition_events_id", "face_recognition_events", ["id"], unique=False)
    op.create_index("ix_face_recognition_events_visit_session_id", "face_recognition_events", ["visit_session_id"], unique=False)


def downgrade() -> None:
    op.drop_index("ix_face_recognition_events_visit_session_id", table_name="face_recognition_events")
    op.drop_index("ix_face_recognition_events_id", table_name="face_recognition_events")
    op.drop_table("face_recognition_events")

    op.drop_index("ix_clinical_records_patient_uuid", table_name="clinical_records")
    op.drop_index("ix_clinical_records_record_uuid", table_name="clinical_records")
    op.drop_index("ix_clinical_records_id", table_name="clinical_records")
    op.drop_table("clinical_records")

    op.drop_index("ix_visits_patient_uuid", table_name="visits")
    op.drop_index("ix_visits_visit_session_id", table_name="visits")
    op.drop_index("ix_visits_id", table_name="visits")
    op.drop_table("visits")

    op.drop_index("ix_biometrics_face_biometric_hash", table_name="biometrics")
    op.drop_index("ix_biometrics_patient_uuid", table_name="biometrics")
    op.drop_index("ix_biometrics_id", table_name="biometrics")
    op.drop_table("biometrics")

    op.drop_index("ix_patients_name_hash", table_name="patients")
    op.drop_index("ix_patients_patient_uuid", table_name="patients")
    op.drop_index("ix_patients_id", table_name="patients")
    op.drop_table("patients")

    op.drop_index("ix_users_username", table_name="users")
    op.drop_index("ix_users_id", table_name="users")
    op.drop_table("users")