"""Add compliance tracking tables"""
from alembic import op
import sqlalchemy as sa

revision = "0002_compliance_tracking"
down_revision = "0001_initial"
branch_labels = None
depends_on = None

def upgrade():
    # Facilities table
    op.create_table(
        "facilities",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("address", sa.String(500)),
        sa.Column("facility_type", sa.String(100)),
        sa.Column("capacity", sa.Integer),
        sa.Column("is_active", sa.Boolean(), default=True),
        sa.Column("created_at", sa.DateTime(), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(), server_default=sa.func.now()),
    )

    # Compliance functions table
    op.create_table(
        "compliance_functions",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("description", sa.Text()),
        sa.Column("category", sa.String(100)),  # EHSO, Fire Safety, etc.
        sa.Column("default_frequency", sa.String(10)),  # W, M, Q, SA, A, 2y, 3y, 5y
        sa.Column("citation_references", sa.JSON()),  # ICC, NFPA, 105 CMR 451, etc.
        sa.Column("is_active", sa.Boolean(), default=True),
        sa.Column("created_at", sa.DateTime(), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(), server_default=sa.func.now()),
    )

    # Compliance schedules table (links facilities to functions)
    op.create_table(
        "compliance_schedules",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("facility_id", sa.String(36), sa.ForeignKey("facilities.id")),
        sa.Column("function_id", sa.String(36), sa.ForeignKey("compliance_functions.id")),
        sa.Column("frequency", sa.String(10), nullable=False),  # W, M, Q, SA, A, 2y, 3y, 5y
        sa.Column("start_date", sa.Date()),
        sa.Column("next_due_date", sa.Date()),
        sa.Column("assigned_to", sa.String(36), sa.ForeignKey("users.id")),
        sa.Column("is_active", sa.Boolean(), default=True),
        sa.Column("created_at", sa.DateTime(), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(), server_default=sa.func.now()),
    )

    # Compliance records table (tracks completion status)
    op.create_table(
        "compliance_records",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("schedule_id", sa.String(36), sa.ForeignKey("compliance_schedules.id")),
        sa.Column("due_date", sa.Date(), nullable=False),
        sa.Column("completed_date", sa.Date()),
        sa.Column("status", sa.String(20), default="pending"),  # pending, completed, missed, overdue
        sa.Column("completed_by", sa.String(36), sa.ForeignKey("users.id")),
        sa.Column("notes", sa.Text()),
        sa.Column("created_at", sa.DateTime(), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(), server_default=sa.func.now()),
    )

    # Document attachments table
    op.create_table(
        "compliance_documents",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("record_id", sa.String(36), sa.ForeignKey("compliance_records.id")),
        sa.Column("filename", sa.String(255), nullable=False),
        sa.Column("file_type", sa.String(50)),
        sa.Column("file_size", sa.Integer),
        sa.Column("file_path", sa.String(500)),
        sa.Column("base64_content", sa.Text()),
        sa.Column("uploaded_by", sa.String(36), sa.ForeignKey("users.id")),
        sa.Column("uploaded_at", sa.DateTime(), server_default=sa.func.now()),
    )

    # Create indexes for better performance
    op.create_index("idx_compliance_schedules_facility", "compliance_schedules", ["facility_id"])
    op.create_index("idx_compliance_records_schedule", "compliance_records", ["schedule_id"])
    op.create_index("idx_compliance_records_due_date", "compliance_records", ["due_date"])
    op.create_index("idx_compliance_documents_record", "compliance_documents", ["record_id"])

def downgrade():
    op.drop_index("idx_compliance_documents_record")
    op.drop_index("idx_compliance_records_due_date")
    op.drop_index("idx_compliance_records_schedule")
    op.drop_index("idx_compliance_schedules_facility")
    op.drop_table("compliance_documents")
    op.drop_table("compliance_records")
    op.drop_table("compliance_schedules")
    op.drop_table("compliance_functions")
    op.drop_table("facilities")