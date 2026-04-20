"""initial canonical schema

Revision ID: 20260417_0001
Revises:
Create Date: 2026-04-17 10:00:00
"""

from __future__ import annotations

from alembic import op
import sqlalchemy as sa
from geoalchemy2 import Geometry
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = "20260417_0001"
down_revision = None
branch_labels = None
depends_on = None


identity_provider = postgresql.ENUM("google", "apple", name="identity_provider", create_type=False)
telemetry_format = postgresql.ENUM(
    "airbly",
    "baju",
    "csv",
    "gpx",
    "igc",
    "kml",
    "nmea",
    "unknown",
    name="telemetry_format",
    create_type=False
)
parse_status = postgresql.ENUM("queued", "processing", "parsed", "failed", name="parse_status", create_type=False)
media_type = postgresql.ENUM("image", "pdf", "video", name="media_type", create_type=False)


def upgrade() -> None:
    op.execute("CREATE EXTENSION IF NOT EXISTS postgis")
    identity_provider.create(op.get_bind(), checkfirst=True)
    telemetry_format.create(op.get_bind(), checkfirst=True)
    parse_status.create(op.get_bind(), checkfirst=True)
    media_type.create(op.get_bind(), checkfirst=True)

    op.create_table(
        "users",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("email", sa.String(length=320), nullable=False),
        sa.Column("display_name", sa.String(length=255), nullable=False),
        sa.Column("given_name", sa.String(length=100), nullable=True),
        sa.Column("family_name", sa.String(length=100), nullable=True),
        sa.Column("locale", sa.String(length=16), nullable=False, server_default="en-US"),
        sa.Column("home_airport_code", sa.String(length=10), nullable=True),
        sa.Column("legacy_username", sa.String(length=255), nullable=True),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("CURRENT_TIMESTAMP")),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("CURRENT_TIMESTAMP")),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("email", name="uq_users_email")
    )
    op.create_index("ix_users_legacy_username", "users", ["legacy_username"], unique=False)

    op.create_table(
        "identities",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("user_id", sa.UUID(), nullable=False),
        sa.Column("provider", identity_provider, nullable=False),
        sa.Column("provider_subject", sa.String(length=255), nullable=False),
        sa.Column("email_verified", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("CURRENT_TIMESTAMP")),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("provider", "provider_subject", name="uq_identity_provider_subject")
    )

    op.create_table(
        "airports",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("code", sa.String(length=10), nullable=False),
        sa.Column("facility_type", sa.String(length=5), nullable=False, server_default="A"),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("country", sa.String(length=255), nullable=True),
        sa.Column("admin1", sa.String(length=255), nullable=True),
        sa.Column("latitude", sa.Numeric(9, 6), nullable=False),
        sa.Column("longitude", sa.Numeric(9, 6), nullable=False),
        sa.Column("position", Geometry(geometry_type="POINT", srid=4326), nullable=True),
        sa.Column("source_user_id", sa.UUID(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("CURRENT_TIMESTAMP")),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("CURRENT_TIMESTAMP")),
        sa.ForeignKeyConstraint(["source_user_id"], ["users.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("code", "facility_type", name="uq_airports_code_type")
    )
    op.create_index("ix_airports_country_admin1", "airports", ["country", "admin1"], unique=False)

    op.create_table(
        "aircraft",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("owner_user_id", sa.UUID(), nullable=False),
        sa.Column("tail_number", sa.String(length=30), nullable=False),
        sa.Column("display_name", sa.String(length=255), nullable=False),
        sa.Column("model_name", sa.String(length=255), nullable=True),
        sa.Column("category_class", sa.String(length=100), nullable=True),
        sa.Column("engine_type", sa.String(length=100), nullable=True),
        sa.Column("is_complex", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("is_high_performance", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("is_retractable", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("CURRENT_TIMESTAMP")),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("CURRENT_TIMESTAMP")),
        sa.ForeignKeyConstraint(["owner_user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id")
    )
    op.create_index("ix_aircraft_owner_tail", "aircraft", ["owner_user_id", "tail_number"], unique=False)

    op.create_table(
        "telemetry_uploads",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("user_id", sa.UUID(), nullable=False),
        sa.Column("source_format", telemetry_format, nullable=False, server_default="unknown"),
        sa.Column("original_filename", sa.String(length=255), nullable=False),
        sa.Column("storage_key", sa.String(length=512), nullable=False),
        sa.Column("parse_status", parse_status, nullable=False, server_default="queued"),
        sa.Column("detected_departure_code", sa.String(length=10), nullable=True),
        sa.Column("detected_arrival_code", sa.String(length=10), nullable=True),
        sa.Column("metadata", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("CURRENT_TIMESTAMP")),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("CURRENT_TIMESTAMP")),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id")
    )
    op.create_index("ix_telemetry_uploads_user_status", "telemetry_uploads", ["user_id", "parse_status"], unique=False)

    op.create_table(
        "flights",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("user_id", sa.UUID(), nullable=False),
        sa.Column("aircraft_id", sa.UUID(), nullable=False),
        sa.Column("telemetry_upload_id", sa.UUID(), nullable=True),
        sa.Column("flight_date", sa.Date(), nullable=False),
        sa.Column("route", sa.String(length=255), nullable=False, server_default=""),
        sa.Column("remarks", sa.Text(), nullable=True),
        sa.Column("total_time", sa.Numeric(10, 2), nullable=False, server_default="0"),
        sa.Column("pic_time", sa.Numeric(10, 2), nullable=False, server_default="0"),
        sa.Column("sic_time", sa.Numeric(10, 2), nullable=False, server_default="0"),
        sa.Column("dual_given", sa.Numeric(10, 2), nullable=False, server_default="0"),
        sa.Column("dual_received", sa.Numeric(10, 2), nullable=False, server_default="0"),
        sa.Column("cross_country", sa.Numeric(10, 2), nullable=False, server_default="0"),
        sa.Column("night", sa.Numeric(10, 2), nullable=False, server_default="0"),
        sa.Column("imc", sa.Numeric(10, 2), nullable=False, server_default="0"),
        sa.Column("simulated_instrument", sa.Numeric(10, 2), nullable=False, server_default="0"),
        sa.Column("landings", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("full_stop_landings_day", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("full_stop_landings_night", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("approaches", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("CURRENT_TIMESTAMP")),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("CURRENT_TIMESTAMP")),
        sa.ForeignKeyConstraint(["aircraft_id"], ["aircraft.id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["telemetry_upload_id"], ["telemetry_uploads.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id")
    )
    op.create_index("ix_flights_user_date", "flights", ["user_id", "flight_date"], unique=False)

    op.create_table(
        "image_assets",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("user_id", sa.UUID(), nullable=False),
        sa.Column("flight_id", sa.UUID(), nullable=True),
        sa.Column("storage_key", sa.String(length=512), nullable=False),
        sa.Column("original_filename", sa.String(length=255), nullable=False),
        sa.Column("media_type", media_type, nullable=False, server_default="image"),
        sa.Column("metadata", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("CURRENT_TIMESTAMP")),
        sa.ForeignKeyConstraint(["flight_id"], ["flights.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id")
    )
    op.create_index("ix_image_assets_user_created", "image_assets", ["user_id", "created_at"], unique=False)

    op.create_table(
        "legacy_entity_mappings",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("legacy_system", sa.String(length=64), nullable=False),
        sa.Column("legacy_table", sa.String(length=128), nullable=False),
        sa.Column("legacy_identifier", sa.String(length=255), nullable=False),
        sa.Column("entity_type", sa.String(length=64), nullable=False),
        sa.Column("canonical_entity_id", sa.UUID(), nullable=False),
        sa.Column("metadata", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("CURRENT_TIMESTAMP")),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("legacy_system", "legacy_table", "legacy_identifier", name="uq_legacy_mapping_source")
    )
    op.create_index("ix_legacy_mapping_entity", "legacy_entity_mappings", ["entity_type", "canonical_entity_id"], unique=False)


def downgrade() -> None:
    op.drop_index("ix_legacy_mapping_entity", table_name="legacy_entity_mappings")
    op.drop_table("legacy_entity_mappings")
    op.drop_index("ix_image_assets_user_created", table_name="image_assets")
    op.drop_table("image_assets")
    op.drop_index("ix_flights_user_date", table_name="flights")
    op.drop_table("flights")
    op.drop_index("ix_telemetry_uploads_user_status", table_name="telemetry_uploads")
    op.drop_table("telemetry_uploads")
    op.drop_index("ix_aircraft_owner_tail", table_name="aircraft")
    op.drop_table("aircraft")
    op.drop_index("ix_airports_country_admin1", table_name="airports")
    op.drop_table("airports")
    op.drop_table("identities")
    op.drop_index("ix_users_legacy_username", table_name="users")
    op.drop_table("users")
    media_type.drop(op.get_bind(), checkfirst=True)
    parse_status.drop(op.get_bind(), checkfirst=True)
    telemetry_format.drop(op.get_bind(), checkfirst=True)
    identity_provider.drop(op.get_bind(), checkfirst=True)
