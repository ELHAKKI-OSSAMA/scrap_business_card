"""Lock the tables against Supabase's auto-generated REST/GraphQL API.

On Supabase every table in ``public`` is reachable with the publishable key through PostgREST
unless row-level security is on. The application connects as the table owner (RLS does not apply
to it), so: enable RLS with no policies and revoke all privileges from the ``anon`` and
``authenticated`` roles. On plain PostgreSQL (Docker) those roles do not exist and only RLS is
enabled, which changes nothing for the owner.

Revision ID: 0002
Revises: 0001
"""

from alembic import op

revision = "0002"
down_revision = "0001"
branch_labels = None
depends_on = None

TABLES = [
    "users", "refresh_tokens", "workspaces", "memberships", "audit_events", "documents", "document_images",
    "document_keys", "processing_jobs", "review_events", "extraction_results", "ocr_regions", "alembic_version",
]


def upgrade() -> None:
    if op.get_bind().dialect.name != "postgresql":
        return
    for t in TABLES:
        op.execute(f'ALTER TABLE public."{t}" ENABLE ROW LEVEL SECURITY')
    op.execute(
        """
        DO $$
        DECLARE r text;
        BEGIN
          FOREACH r IN ARRAY ARRAY['anon', 'authenticated'] LOOP
            IF EXISTS (SELECT 1 FROM pg_roles WHERE rolname = r) THEN
              EXECUTE format('REVOKE ALL ON ALL TABLES IN SCHEMA public FROM %I', r);
              EXECUTE format('REVOKE ALL ON ALL SEQUENCES IN SCHEMA public FROM %I', r);
              EXECUTE format('ALTER DEFAULT PRIVILEGES IN SCHEMA public REVOKE ALL ON TABLES FROM %I', r);
            END IF;
          END LOOP;
        END $$;
        """
    )


def downgrade() -> None:
    if op.get_bind().dialect.name != "postgresql":
        return
    for t in TABLES:
        op.execute(f'ALTER TABLE public."{t}" DISABLE ROW LEVEL SECURITY')
