"""Initial schema (fire & hygiene suite)"""
from alembic import op
import sqlalchemy as sa

revision = "0001_initial"
down_revision = None
branch_labels = None
depends_on = None

def upgrade():
    # Users / Roles
    op.create_table(
        "users",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("username", sa.String(120), nullable=False, unique=True),
        sa.Column("role", sa.String(50), nullable=False),
        sa.Column("created_at", sa.DateTime(), server_default=sa.func.now()),
    )

    # JSON‑schema templates
    op.create_table(
        "templates",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("schema", sa.JSON(), nullable=False),
        sa.Column("created_by", sa.String(36), sa.ForeignKey("users.id")),
        sa.Column("created_at", sa.DateTime(), server_default=sa.func.now()),
    )

    # Inspections
    op.create_table(
        "inspections",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("template_id", sa.String(36), sa.ForeignKey("templates.id")),
        sa.Column("facility", sa.String(120), nullable=False),
        sa.Column("payload", sa.JSON(), nullable=False),
        sa.Column("status", sa.String(50), default="draft"),
        sa.Column("inspector_id", sa.String(36), sa.ForeignKey("users.id")),
        sa.Column("deputy_id", sa.String(36), sa.ForeignKey("users.id"), nullable=True),
        sa.Column("created_at", sa.DateTime(), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(), server_default=sa.func.now()),
    )

    # Corrective‑action tracker
    op.create_table(
        "corrective_actions",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("inspection_id", sa.String(36), sa.ForeignKey("inspections.id")),
        sa.Column("violation_ref", sa.String(255)),
        sa.Column("action_plan", sa.Text()),
        sa.Column("due_date", sa.Date()),
        sa.Column("completed", sa.Boolean(), default=False),
        sa.Column("completed_at", sa.DateTime()),
    )

    # Audit log
    op.create_table(
        "audit_logs",
        sa.Column("id", sa.Integer, primary_key=True, autoincrement=True),
        sa.Column("username", sa.String(120)),
        sa.Column("action", sa.String(255)),
        sa.Column("ip_addr", sa.String(45)),
        sa.Column("timestamp", sa.DateTime(), server_default=sa.func.now()),
    )

def downgrade():
    op.drop_table("audit_logs")
    op.drop_table("corrective_actions")
    op.drop_table("inspections")
    op.drop_table("templates")
    op.drop_table("users")