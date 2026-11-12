"""Add session, notification, and experience records.

Revision ID: 20261109_portal_extensions
Revises: 20261109_student_portal
"""

import re
import secrets
from datetime import UTC, datetime

import sqlalchemy as sa
from alembic import op

from backend.app.database import Base
from backend.app.models import student_portal as _student_portal
from backend.app.models import user as _user

revision = "20261109_portal_extensions"
down_revision = "20261109_student_portal"
branch_labels = None
depends_on = None


def _update_existing_port_ids() -> None:
    connection = op.get_bind()
    rows = connection.execute(sa.text("SELECT id, port_id FROM users WHERE port_id IS NOT NULL")).all()
    valid_ids = {row.port_id for row in rows if re.fullmatch(r"TP\d{7}", row.port_id or "")}
    for row in rows:
        if re.fullmatch(r"TP\d{7}", row.port_id or ""):
            continue
        match = re.match(r"TP(\d{2})", row.port_id or "")
        year_suffix = match.group(1) if match else str(datetime.now(UTC).year)[-2:]
        while True:
            port_id = f"TP{year_suffix}{secrets.randbelow(90000) + 10000}"
            if port_id not in valid_ids:
                valid_ids.add(port_id)
                connection.execute(
                    sa.text("UPDATE users SET port_id = :port_id WHERE id = :user_id"),
                    {"port_id": port_id, "user_id": row.id},
                )
                break


def upgrade() -> None:
    new_tables = ["work_experiences", "notifications", "user_sessions"]
    Base.metadata.create_all(
        bind=op.get_bind(),
        tables=[Base.metadata.tables[name] for name in new_tables],
        checkfirst=True,
    )
    index_map = {
        "team_members": ("uq_team_member_user", ["team_id", "user_id"]),
        "opportunity_applications": ("uq_opportunity_application_user", ["opportunity_id", "user_id"]),
        "saved_opportunities": ("uq_saved_opportunity_user", ["opportunity_id", "user_id"]),
    }
    inspector = sa.inspect(op.get_bind())
    for table_name, (index_name, columns) in index_map.items():
        existing = {index["name"] for index in inspector.get_indexes(table_name)}
        existing.update(
            constraint["name"]
            for constraint in inspector.get_unique_constraints(table_name)
            if constraint["name"]
        )
        if index_name not in existing:
            op.create_index(index_name, table_name, columns, unique=True)
    if "ix_learning_activities_user_id" not in {
        index["name"] for index in inspector.get_indexes("learning_activities")
    }:
        op.create_index(
            "ix_learning_activities_user_id",
            "learning_activities",
            ["user_id"],
            unique=False,
        )
    _update_existing_port_ids()


def downgrade() -> None:
    for table_name, index_name in (
        ("team_members", "uq_team_member_user"),
        ("opportunity_applications", "uq_opportunity_application_user"),
        ("saved_opportunities", "uq_saved_opportunity_user"),
    ):
        existing = {index["name"] for index in sa.inspect(op.get_bind()).get_indexes(table_name)}
        if index_name in existing:
            op.drop_index(index_name, table_name=table_name)
    if "ix_learning_activities_user_id" in {
        index["name"] for index in sa.inspect(op.get_bind()).get_indexes("learning_activities")
    }:
        op.drop_index("ix_learning_activities_user_id", table_name="learning_activities")
    for table_name in ("user_sessions", "notifications", "work_experiences"):
        Base.metadata.tables[table_name].drop(bind=op.get_bind(), checkfirst=True)
