-- Service-role-only SQL executor used by the BrainsFor build factory.
--
-- auto-build-brain.py's ensure_supabase_tables() calls this via the PostgREST RPC
-- endpoint (/rest/v1/rpc/exec_sql) to run templates/create-brain-tables.sql, because
-- the build runs standalone with no direct Postgres connection (no psql / psycopg).
--
-- Why it exists: before this, the factory tried to run DDL through bogus endpoints
-- (/rest/v1/rpc/ and /pg) with a malformed auth header, swallowed every error, and
-- printed a fake "Executed N statements" success. Result: NO recent build's tables
-- were ever created, and every brain since was silently orphaned from Supabase.
--
-- Security: SECURITY DEFINER but EXECUTE is granted ONLY to service_role (revoked from
-- anon/authenticated/PUBLIC). The build holds the service key; anon/website cannot call
-- it. search_path includes `extensions` so the pgvector `vector` type resolves inside
-- the restricted definer context (it lives in the extensions schema on Supabase).
--
-- Idempotent — safe to re-run.

CREATE OR REPLACE FUNCTION public.exec_sql(query text)
RETURNS void
LANGUAGE plpgsql
SECURITY DEFINER
SET search_path = public, extensions
AS $$
BEGIN
  EXECUTE query;
END;
$$;

REVOKE ALL ON FUNCTION public.exec_sql(text) FROM PUBLIC, anon, authenticated;
GRANT EXECUTE ON FUNCTION public.exec_sql(text) TO service_role;

COMMENT ON FUNCTION public.exec_sql(text) IS
  'Service-role-only DDL/DML executor for the BrainsFor build factory (auto-build-brain.py table creation). Not callable by anon/authenticated.';
