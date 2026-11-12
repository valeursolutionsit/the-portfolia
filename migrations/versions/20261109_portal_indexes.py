"""Index student learning history.

Revision ID: 20261109_portal_indexes
Revises: 20261109_portal_extensions
"""

import sqlalchemy as sa
from alembic import op

revision = "20261109_portal_indexes"
down_revision = "20261109_portal_extensions"
branch_labels = None
depends_on = None


def upgrade() -> None:
    indexes = {index["name"] for index in sa.inspect(op.get_bind()).get_indexes("learning_activities")}
    if "ix_learning_activities_user_id" not in indexes:
        op.create_index(
            "ix_learning_activities_user_id",
            "learning_activities",
            ["user_id"],
            unique=False,
        )


def downgrade() -> None:
    indexes = {index["name"] for index in sa.inspect(op.get_bind()).get_indexes("learning_activities")}
    if "ix_learning_activities_user_id" in indexes:
        op.drop_index("ix_learning_activities_user_id", table_name="learning_activities")
