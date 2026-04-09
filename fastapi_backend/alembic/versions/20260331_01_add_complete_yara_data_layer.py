"""Add complete YARA data layer schema

Revision ID: 20260331_01
Revises: 20260330_02_add_patient_identifier_encryption_fields
Create Date: 2026-03-31 04:45:00

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '20260331_01'
down_revision: Union[str, None] = '20260330_02_add_patient_identifier_encryption_fields'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Add missing columns to staff table
    op.add_column('staff', sa.Column('is_active', sa.Boolean(), nullable=True, server_default='true'))
    op.add_column('staff', sa.Column('created_at', sa.DateTime(), nullable=True, server_default=sa.func.now()))
    op.add_column('staff', sa.Column('last_login', sa.DateTime(), nullable=True))
    
    # Add columns to patients table if not exist
    try:
        op.add_column('patients', sa.Column('name', sa.String(500), nullable=True))
    except:
        pass  # Column may already exist
    
    try:
        op.add_column('patients', sa.Column('identifier', sa.String(50), nullable=True))
        op.create_index('ix_patients_identifier', 'patients', ['identifier'])
    except:
        pass
    
    try:
        op.add_column('patients', sa.Column('face_embedding_id', sa.Integer(), nullable=True))
        op.add_column('patients', sa.Column('date_of_birth', sa.DateTime(), nullable=True))
        op.add_column('patients', sa.Column('updated_at', sa.DateTime(), nullable=True, server_default=sa.func.now()))
    except:
        pass
    
    # Create face_embeddings table
    op.create_table(
        'face_embeddings',
        sa.Column('id', sa.Integer(), primary_key=True, index=True),
        sa.Column('patient_id', sa.Integer(), sa.ForeignKey('patients.id', ondelete='CASCADE'), nullable=False, index=True),
        sa.Column('embedding', sa.JSON(), nullable=False),
        sa.Column('model', sa.String(100), nullable=False, server_default='Facenet512'),
        sa.Column('captured_at', sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.Column('image_hash', sa.String(64), nullable=True, unique=True),
    )
    op.create_index('ix_face_embeddings_patient_id', 'face_embeddings', ['patient_id'])
    
    # Add FK to patients for face_embedding_id
    try:
        op.create_foreign_key(
            'fk_patients_face_embedding_id',
            'patients', 'face_embeddings',
            ['face_embedding_id'], ['id'],
            ondelete='SET NULL'
        )
    except:
        pass
    
    # Add missing columns to visits table
    try:
        op.add_column('visits', sa.Column('patient_id', sa.Integer(), nullable=True))
        op.add_column('visits', sa.Column('session_token', sa.String(128), nullable=True))
        op.add_column('visits', sa.Column('visit_reason', sa.String(255), nullable=True))
        op.add_column('visits', sa.Column('created_by_staff_id', sa.Integer(), nullable=True))
        op.add_column('visits', sa.Column('created_at', sa.DateTime(), nullable=True, server_default=sa.func.now()))
        
        # Create indexes
        op.create_index('ix_visits_patient_id', 'visits', ['patient_id'])
        op.create_index('ix_visits_created_at', 'visits', ['created_at'])
        op.create_index('ix_visits_status', 'visits', ['status'])
        
        # Create FKs
        op.create_foreign_key('fk_visits_patient_id', 'visits', 'patients', ['patient_id'], ['id'], ondelete='CASCADE')
        op.create_foreign_key('fk_visits_staff_id', 'visits', 'staff', ['created_by_staff_id'], ['id'], ondelete='SET NULL')
    except:
        pass
    
    # Create vitals table
    op.create_table(
        'vitals',
        sa.Column('id', sa.Integer(), primary_key=True, index=True),
        sa.Column('visit_id', sa.Integer(), sa.ForeignKey('visits.id', ondelete='CASCADE'), nullable=False, index=True),
        sa.Column('bp_systolic', sa.Integer(), nullable=True),
        sa.Column('bp_diastolic', sa.Integer(), nullable=True),
        sa.Column('temperature_c', sa.Float(), nullable=True),
        sa.Column('o2_sat', sa.Integer(), nullable=True),
        sa.Column('weight_kg', sa.Float(), nullable=True),
        sa.Column('recorded_at', sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.Column('recorded_by', sa.Integer(), sa.ForeignKey('staff.id', ondelete='SET NULL'), nullable=True),
    )
    
    # Create notes table
    op.create_table(
        'notes',
        sa.Column('id', sa.Integer(), primary_key=True, index=True),
        sa.Column('visit_id', sa.Integer(), sa.ForeignKey('visits.id', ondelete='CASCADE'), nullable=False, index=True),
        sa.Column('content', sa.Text(), nullable=False),
        sa.Column('author_staff_id', sa.Integer(), sa.ForeignKey('staff.id', ondelete='SET NULL'), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.func.now()),
    )
    
    # Create audit_events table
    op.create_table(
        'audit_events',
        sa.Column('id', sa.Integer(), primary_key=True, index=True),
        sa.Column('staff_id', sa.String(100), nullable=True, index=True),
        sa.Column('action', sa.String(100), nullable=False),
        sa.Column('outcome', sa.String(32), nullable=False),
        sa.Column('ip_address', sa.String(45), nullable=True),
        sa.Column('role', sa.String(32), nullable=True),
        sa.Column('details', sa.JSON(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.func.now(), index=True),
    )
    op.create_index('ix_audit_events_created_at', 'audit_events', ['created_at'])
    op.create_index('ix_audit_events_staff_id', 'audit_events', ['staff_id'])
    op.create_index('ix_audit_events_action', 'audit_events', ['action'])
    
    # Create ai_summaries table
    op.create_table(
        'ai_summaries',
        sa.Column('id', sa.Integer(), primary_key=True, index=True),
        sa.Column('patient_id', sa.Integer(), sa.ForeignKey('patients.id', ondelete='CASCADE'), nullable=False, index=True),
        sa.Column('summary_text', sa.Text(), nullable=False),
        sa.Column('generated_at', sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.Column('model_version', sa.String(100), nullable=False, server_default='gemini-1.5-flash'),
    )
    op.create_index('ix_ai_summaries_patient_generated', 'ai_summaries', ['patient_id', 'generated_at'])


def downgrade() -> None:
    # Drop new tables
    op.drop_table('ai_summaries')
    op.drop_table('audit_events')
    op.drop_table('notes')
    op.drop_table('vitals')
    
    # Drop foreign keys
    try:
        op.drop_constraint('fk_patients_face_embedding_id', 'patients', type_='foreignkey')
    except:
        pass
    
    op.drop_table('face_embeddings')
    
    # Drop added columns
    op.drop_column('staff', 'last_login')
    op.drop_column('staff', 'created_at')
    op.drop_column('staff', 'is_active')
