"""Monthly Inspections System

Revision ID: 0003_monthly_inspections
Revises: 0002_compliance_tracking
Create Date: 2025-01-15 18:45:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers
revision = '0003_monthly_inspections'
down_revision = '0002_compliance_tracking'
branch_labels = None
depends_on = None

def upgrade():
    # Create monthly_inspections table
    op.create_table('monthly_inspections',
        sa.Column('id', sa.String(36), primary_key=True),
        sa.Column('facility_id', sa.String(36), sa.ForeignKey('facilities.id'), nullable=False),
        sa.Column('year', sa.Integer, nullable=False),
        sa.Column('month', sa.Integer, nullable=False),
        sa.Column('inspection_date', sa.Date),
        sa.Column('status', sa.String(20), default='draft'),  # draft, inspector_signed, deputy_signed, completed
        sa.Column('created_by', sa.String(100)),
        sa.Column('created_at', sa.DateTime, default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime, default=sa.func.now(), onupdate=sa.func.now()),
        sa.Column('form_data', sa.JSON),  # Store the complete form data
        sa.Column('notes', sa.Text),
        sa.Column('carryover_deficiencies', sa.JSON),  # Previous month's deficiencies
        # Add composite unique constraint for facility/year/month
        sa.UniqueConstraint('facility_id', 'year', 'month', name='uq_monthly_inspection_facility_year_month')
    )
    
    # Create inspection_signatures table
    op.create_table('inspection_signatures',
        sa.Column('id', sa.String(36), primary_key=True),
        sa.Column('inspection_id', sa.String(36), sa.ForeignKey('monthly_inspections.id'), nullable=False),
        sa.Column('signature_type', sa.String(20), nullable=False),  # inspector, deputy
        sa.Column('signed_by', sa.String(100), nullable=False),
        sa.Column('signed_at', sa.DateTime, nullable=False),
        sa.Column('signature_data', sa.Text),  # Base64 encoded signature image
        sa.Column('ip_address', sa.String(45)),
        sa.Column('user_agent', sa.String(500)),
        sa.Column('verification_hash', sa.String(256)),  # For signature verification
    )
    
    # Create inspection_deficiencies table
    op.create_table('inspection_deficiencies',
        sa.Column('id', sa.String(36), primary_key=True),
        sa.Column('inspection_id', sa.String(36), sa.ForeignKey('monthly_inspections.id'), nullable=False),
        sa.Column('violation_code_id', sa.String(36), sa.ForeignKey('violation_codes.id')),
        sa.Column('area_type', sa.String(50), nullable=False),  # fire_safety, environmental_health, etc.
        sa.Column('location', sa.String(200)),
        sa.Column('description', sa.Text, nullable=False),
        sa.Column('citation_code', sa.String(50)),
        sa.Column('citation_section', sa.String(100)),
        sa.Column('severity', sa.String(20), default='medium'),  # low, medium, high, critical
        sa.Column('status', sa.String(20), default='open'),  # open, in_progress, resolved, carried_over
        sa.Column('corrective_action', sa.Text),
        sa.Column('target_completion_date', sa.Date),
        sa.Column('actual_completion_date', sa.Date),
        sa.Column('completed_by', sa.String(100)),
        sa.Column('carryover_from_month', sa.Integer),  # If carried over from previous month
        sa.Column('created_at', sa.DateTime, default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime, default=sa.func.now(), onupdate=sa.func.now()),
    )
    
    # Create violation_codes table
    op.create_table('violation_codes',
        sa.Column('id', sa.String(36), primary_key=True),
        sa.Column('code_type', sa.String(50), nullable=False),  # ICC, 780_CMR, 527_CMR, 105_CMR_451
        sa.Column('code_number', sa.String(50), nullable=False),
        sa.Column('section', sa.String(100)),
        sa.Column('title', sa.String(200), nullable=False),
        sa.Column('description', sa.Text),
        sa.Column('severity_level', sa.String(20), default='medium'),
        sa.Column('area_category', sa.String(50)),  # fire_safety, environmental_health, etc.
        sa.Column('pdf_document_id', sa.String(36)),  # Reference to uploaded PDF
        sa.Column('is_active', sa.Boolean, default=True),
        sa.Column('created_at', sa.DateTime, default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime, default=sa.func.now(), onupdate=sa.func.now()),
        # Add composite unique constraint for code_type/code_number/section
        sa.UniqueConstraint('code_type', 'code_number', 'section', name='uq_violation_code')
    )
    
    # Create form_configurations table
    op.create_table('form_configurations',
        sa.Column('id', sa.String(36), primary_key=True),
        sa.Column('form_type', sa.String(50), nullable=False),  # monthly_inspection
        sa.Column('section_name', sa.String(100), nullable=False),
        sa.Column('field_name', sa.String(100), nullable=False),
        sa.Column('field_type', sa.String(50), nullable=False),  # checkbox, text, textarea, select
        sa.Column('field_label', sa.String(200), nullable=False),
        sa.Column('is_enabled', sa.Boolean, default=True),
        sa.Column('is_required', sa.Boolean, default=False),
        sa.Column('display_order', sa.Integer, default=0),
        sa.Column('field_options', sa.JSON),  # For select fields, etc.
        sa.Column('validation_rules', sa.JSON),
        sa.Column('role_visibility', sa.JSON),  # Which roles can see this field
        sa.Column('created_at', sa.DateTime, default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime, default=sa.func.now(), onupdate=sa.func.now()),
        # Add composite unique constraint for form_type/section_name/field_name
        sa.UniqueConstraint('form_type', 'section_name', 'field_name', name='uq_form_field')
    )
    
    # Create violation_pdfs table for storing uploaded code documents
    op.create_table('violation_pdfs',
        sa.Column('id', sa.String(36), primary_key=True),
        sa.Column('filename', sa.String(255), nullable=False),
        sa.Column('file_type', sa.String(50), nullable=False),
        sa.Column('file_size', sa.Integer, nullable=False),
        sa.Column('base64_content', sa.Text, nullable=False),
        sa.Column('code_type', sa.String(50), nullable=False),
        sa.Column('uploaded_by', sa.String(100), nullable=False),
        sa.Column('uploaded_at', sa.DateTime, default=sa.func.now()),
        sa.Column('description', sa.Text),
        sa.Column('is_active', sa.Boolean, default=True),
    )
    
    # Create indexes for better performance
    op.create_index('idx_monthly_inspections_facility_date', 'monthly_inspections', ['facility_id', 'year', 'month'])
    op.create_index('idx_monthly_inspections_status', 'monthly_inspections', ['status'])
    op.create_index('idx_inspection_signatures_inspection', 'inspection_signatures', ['inspection_id'])
    op.create_index('idx_inspection_deficiencies_inspection', 'inspection_deficiencies', ['inspection_id'])
    op.create_index('idx_inspection_deficiencies_status', 'inspection_deficiencies', ['status'])
    op.create_index('idx_violation_codes_type', 'violation_codes', ['code_type'])
    op.create_index('idx_violation_codes_active', 'violation_codes', ['is_active'])
    op.create_index('idx_form_configurations_form_type', 'form_configurations', ['form_type'])


def downgrade():
    # Drop indexes
    op.drop_index('idx_form_configurations_form_type', table_name='form_configurations')
    op.drop_index('idx_violation_codes_active', table_name='violation_codes')
    op.drop_index('idx_violation_codes_type', table_name='violation_codes')
    op.drop_index('idx_inspection_deficiencies_status', table_name='inspection_deficiencies')
    op.drop_index('idx_inspection_deficiencies_inspection', table_name='inspection_deficiencies')
    op.drop_index('idx_inspection_signatures_inspection', table_name='inspection_signatures')
    op.drop_index('idx_monthly_inspections_status', table_name='monthly_inspections')
    op.drop_index('idx_monthly_inspections_facility_date', table_name='monthly_inspections')
    
    # Drop tables
    op.drop_table('violation_pdfs')
    op.drop_table('form_configurations')
    op.drop_table('violation_codes')
    op.drop_table('inspection_deficiencies')
    op.drop_table('inspection_signatures')
    op.drop_table('monthly_inspections')