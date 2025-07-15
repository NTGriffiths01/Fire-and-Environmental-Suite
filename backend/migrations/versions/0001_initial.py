"""Initial schema (fire & hygiene suite)"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID

revision = "0001_initial"
down_revision = None
branch_labels = None
depends_on = None

def upgrade():
    # Users / Roles
    op.create_table(
        "users",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column("username", sa.String(120), nullable=False, unique=True),
        sa.Column("role", sa.Enum("admin", "inspector", "deputy_ops", name="role_enum"), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )

    # JSON‑schema templates
    op.create_table(
        "templates",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("schema", sa.JSON(), nullable=False),
        sa.Column("created_by", UUID(as_uuid=True), sa.ForeignKey("users.id")),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )

    # Inspections
    op.create_table(
        "inspections",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column("template_id", UUID(as_uuid=True), sa.ForeignKey("templates.id")),
        sa.Column("facility", sa.String(120), nullable=False),
        sa.Column("payload", sa.JSON(), nullable=False),
        sa.Column("status", sa.Enum("draft", "submitted", "completed", name="status_enum")),
        sa.Column("inspector_id", UUID(as_uuid=True), sa.ForeignKey("users.id")),
        sa.Column("deputy_id", UUID(as_uuid=True), sa.ForeignKey("users.id"), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), onupdate=sa.func.now()),
    )

    # Corrective‑action tracker
    op.create_table(
        "corrective_actions",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column("inspection_id", UUID(as_uuid=True), sa.ForeignKey("inspections.id", ondelete="CASCADE")),
        sa.Column("violation_ref", sa.String(255)),
        sa.Column("action_plan", sa.Text()),
        sa.Column("due_date", sa.Date()),
        sa.Column("completed", sa.Boolean(), default=False),
        sa.Column("completed_at", sa.DateTime(timezone=True)),
    )

    # Audit log
    op.create_table(
        "audit_logs",
        sa.Column("id", sa.BigInteger, primary_key=True),
        sa.Column("username", sa.String(120)),
        sa.Column("action", sa.String(255)),
        sa.Column("ip_addr", sa.String(45)),
        sa.Column("timestamp", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )

def downgrade():
    op.drop_table("audit_logs")
    op.drop_table("corrective_actions")
    op.drop_table("inspections")
    op.drop_table("templates")
    op.drop_table("users")
    op.execute("DROP TYPE IF EXISTS role_enum")
    op.execute("DROP TYPE IF EXISTS status_enum")