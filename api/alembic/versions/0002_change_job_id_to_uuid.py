"""change job id column type to uuid

Revision ID: 0002
Revises: 0001
Create Date: 2026-05-08

"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

revision: str = "0002"
down_revision: str | None = "0001"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    # Existing rows contain ULID strings which cannot be cast to uuid, so the
    # table is truncated before altering the column type. This is safe for a
    # demo project where in-flight jobs are not preserved across schema changes.
    op.execute("TRUNCATE TABLE jobs")
    op.alter_column(
        "jobs",
        "id",
        type_=sa.Uuid(),
        postgresql_using="id::uuid",
    )


def downgrade() -> None:
    op.execute("TRUNCATE TABLE jobs")
    op.alter_column(
        "jobs",
        "id",
        type_=sa.String(26),
        postgresql_using="id::text",
    )
