"""Create learning activities table

Revision ID: 20261109_learning_activity
Revises: None
Create Date: 2026-11-09 22:00:00.000000
"""

from alembic import op

from backend.app.database import Base
from backend.app.models import student_portal as _student_portal
from backend.app.models import user as _user
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = "20261109_learning_activity"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    core_tables = [
        "roles",
        "permissions",
        "users",
        "role_permissions",
        "user_roles",
        "user_profiles",
        "institution_profiles",
        "company_profiles",
        "investor_profiles",
        "audit_logs",
    ]
    Base.metadata.create_all(
        bind=op.get_bind(),
        tables=[Base.metadata.tables[name] for name in core_tables],
        checkfirst=True,
    )
    if "learning_activities" in sa.inspect(op.get_bind()).get_table_names():
        return
    op.create_table(
        "learning_activities",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("user_id", sa.String(length=36), nullable=False),
        sa.Column("title", sa.String(length=255), nullable=False),
        sa.Column("category", sa.String(length=100), nullable=False, server_default="general"),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("evidence_url", sa.String(length=500), nullable=True),
        sa.Column("duration_hours", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("completed_at", sa.DateTime(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"]),
    )
    op.create_index(op.f("ix_learning_activities_id"), "learning_activities", ["id"], unique=False)
    op.create_index("ix_learning_activities_user_id", "learning_activities", ["user_id"], unique=False)


def downgrade() -> None:
    op.drop_index(op.f("ix_learning_activities_id"), table_name="learning_activities")
    op.drop_table("learning_activities")
