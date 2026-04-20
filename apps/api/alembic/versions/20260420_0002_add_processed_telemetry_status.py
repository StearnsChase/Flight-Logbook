"""add processed telemetry parse status

Revision ID: 20260420_0002
Revises: 20260417_0001
Create Date: 2026-04-20 18:30:00
"""

from __future__ import annotations

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = "20260420_0002"
down_revision = "20260417_0001"
branch_labels = None
depends_on = None


parse_status = postgresql.ENUM(
    "queued",
    "processing",
    "parsed",
    "processed",
    "failed",
    name="parse_status",
    create_type=False,
)

previous_parse_status = postgresql.ENUM(
    "queued",
    "processing",
    "parsed",
    "failed",
    name="parse_status",
    create_type=False,
)


def upgrade() -> None:
    with op.get_context().autocommit_block():
        op.execute("ALTER TYPE parse_status ADD VALUE IF NOT EXISTS 'processed'")


def downgrade() -> None:
    bind = op.get_bind()

    op.execute("UPDATE telemetry_uploads SET parse_status = 'parsed' WHERE parse_status = 'processed'")

    with op.get_context().autocommit_block():
        op.execute("ALTER TYPE parse_status RENAME TO parse_status_old")

    previous_parse_status.create(bind, checkfirst=False)

    op.execute(
        """
        ALTER TABLE telemetry_uploads
        ALTER COLUMN parse_status TYPE parse_status
        USING parse_status::text::parse_status
        """
    )

    op.execute("DROP TYPE parse_status_old")
