"""Capture requests: the PC asks the phone to photograph a document side.

Revision ID: 0005
Revises: 0004
"""

import sqlalchemy as sa
from alembic import op

revision = "0005"
down_revision = "0004"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "capture_requests",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column("user_id", sa.Uuid(), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True),
        sa.Column("document_id", sa.Uuid(), sa.ForeignKey("documents.id", ondelete="CASCADE"), nullable=False),
        sa.Column("side", sa.String(16), nullable=False),
        sa.Column("status", sa.String(16), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    )
    if op.get_bind().dialect.name == "postgresql":
        # same lock-down as 0002: never reachable through Supabase's auto REST API
        op.execute('ALTER TABLE public."capture_requests" ENABLE ROW LEVEL SECURITY')
        op.execute("""
            DO $$ DECLARE r text; BEGIN
              FOREACH r IN ARRAY ARRAY['anon','authenticated'] LOOP
                IF EXISTS (SELECT 1 FROM pg_roles WHERE rolname = r) THEN
                  EXECUTE format('REVOKE ALL ON public.capture_requests FROM %I', r);
                END IF;
              END LOOP;
            END $$;""")


def downgrade() -> None:
    op.drop_table("capture_requests")
