-- Migration: Rename belsky_* tables to scott_belsky_* convention
-- Run this in Supabase SQL Editor BEFORE using the updated scripts.
--
-- This renames the tables to match the first-last naming convention
-- used throughout the codebase (brains/scott-belsky/).
--
-- The rename preserves all data, indexes, constraints, and foreign keys.

-- 1. Rename tables
ALTER TABLE belsky_atoms RENAME TO scott_belsky_atoms;
ALTER TABLE belsky_connections RENAME TO scott_belsky_connections;

-- 2. Rename enrichment log if it exists
ALTER TABLE IF EXISTS belsky_enrichment_log RENAME TO scott_belsky_enrichment_log;

-- 3. Update brain_metadata row to reflect new table names
UPDATE brain_metadata
SET atoms_table = 'scott_belsky_atoms',
    connections_table = 'scott_belsky_connections'
WHERE slug = 'scott-belsky' OR slug = 'belsky';

-- Also update the slug itself if it was the old format
UPDATE brain_metadata
SET slug = 'scott-belsky'
WHERE slug = 'belsky';

-- 4. Update cross_connections if it references old table names in metadata
-- (cross_connections uses atom IDs directly, so data is unaffected —
--  only update if there's a source_table column)
-- UPDATE cross_connections SET source_table = 'scott_belsky_atoms' WHERE source_table = 'belsky_atoms';

-- 5. If pg_cron jobs reference the old table names, update them:
-- SELECT * FROM cron.job WHERE command LIKE '%belsky_atoms%';
-- Then: SELECT cron.alter_job(job_id, command := replace(command, 'belsky_atoms', 'scott_belsky_atoms'));

-- 6. Verify
SELECT 'scott_belsky_atoms' AS table_name, count(*) AS row_count FROM scott_belsky_atoms
UNION ALL
SELECT 'scott_belsky_connections', count(*) FROM scott_belsky_connections;
