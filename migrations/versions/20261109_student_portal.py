"""Add persisted student portal modules.

Revision ID: 20261109_student_portal
Revises: 20261109_learning_activity
"""

import sqlalchemy as sa
from alembic import op

from backend.app.database import Base
from backend.app.models import student_portal as _student_portal
from backend.app.models import user as _user

revision = "20261109_student_portal"
down_revision = "20261109_learning_activity"
branch_labels = None
depends_on = None


PROFILE_COLUMNS = {
    "profile_photo_url": sa.String(length=500),
    "date_of_birth": sa.Date(),
    "gender": sa.String(length=40),
    "address": sa.Text(),
    "university": sa.String(length=255),
    "degree": sa.String(length=255),
    "current_year": sa.String(length=80),
    "career_objective": sa.Text(),
    "interested_industries": sa.Text(),
    "preferred_job_roles": sa.Text(),
    "career_goals": sa.Text(),
    "linkedin_url": sa.String(length=500),
    "github_url": sa.String(length=500),
    "personal_website": sa.String(length=500),
    "profile_visibility": sa.String(length=20),
}

LEARNING_COLUMNS = {
    "topic": sa.String(length=255),
    "what_i_practised": sa.Text(),
    "resource_url": sa.String(length=500),
    "confidence": sa.Integer(),
    "status": sa.String(length=30),
}


def _add_missing_columns(table_name: str, columns: dict[str, sa.types.TypeEngine]) -> None:
    inspector = sa.inspect(op.get_bind())
    if table_name not in inspector.get_table_names():
        return
    existing = {column["name"] for column in inspector.get_columns(table_name)}
    for name, column_type in columns.items():
        if name not in existing:
            kwargs = {"nullable": name != "profile_visibility" and name != "status"}
            if name in {"profile_visibility", "status"}:
                kwargs["server_default"] = "private" if name == "profile_visibility" else "completed"
            op.add_column(table_name, sa.Column(name, column_type, **kwargs))


def upgrade() -> None:
    _add_missing_columns("user_profiles", PROFILE_COLUMNS)
    _add_missing_columns("learning_activities", LEARNING_COLUMNS)
    new_tables = [
        "student_skills",
        "learning_milestones",
        "learning_paths",
        "learning_resources",
        "portfolio_projects",
        "certifications",
        "achievements",
        "work_experiences",
        "skill_assessments",
        "assessment_questions",
        "assessment_attempts",
        "teams",
        "team_members",
        "team_invitations",
        "project_tasks",
        "project_contributions",
        "opportunities",
        "opportunity_applications",
        "saved_opportunities",
        "support_tickets",
        "support_messages",
        "notifications",
        "user_sessions",
        "student_settings",
    ]
    Base.metadata.create_all(
        bind=op.get_bind(),
        tables=[Base.metadata.tables[name] for name in new_tables],
        checkfirst=True,
    )


def downgrade() -> None:
    for table_name in (
        "student_settings",
        "support_messages",
        "notifications",
        "user_sessions",
        "support_tickets",
        "saved_opportunities",
        "opportunity_applications",
        "opportunities",
        "project_contributions",
        "project_tasks",
        "team_invitations",
        "team_members",
        "teams",
        "assessment_attempts",
        "assessment_questions",
        "skill_assessments",
        "achievements",
        "work_experiences",
        "certifications",
        "portfolio_projects",
        "learning_resources",
        "learning_paths",
        "learning_milestones",
        "student_skills",
    ):
        Base.metadata.tables[table_name].drop(bind=op.get_bind(), checkfirst=True)

    for table_name, columns in (
        ("learning_activities", LEARNING_COLUMNS),
        ("user_profiles", PROFILE_COLUMNS),
    ):
        if table_name in sa.inspect(op.get_bind()).get_table_names():
            existing = {column["name"] for column in sa.inspect(op.get_bind()).get_columns(table_name)}
            for name in reversed(tuple(columns)):
                if name in existing:
                    op.drop_column(table_name, name)
