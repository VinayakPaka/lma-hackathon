-- Migration: Fix result_json column type and add unique constraint
-- Run this if you have existing data and the column is VARCHAR instead of TEXT/JSONB

-- Step 1: Check current column type (informational only)
-- SELECT column_name, data_type, character_maximum_length 
-- FROM information_schema.columns 
-- WHERE table_name = 'kpi_evaluation_results' AND column_name = 'result_json';

-- Step 2: Alter column to use TEXT (unlimited length) if it's VARCHAR
-- For PostgreSQL:
ALTER TABLE kpi_evaluation_results 
ALTER COLUMN result_json TYPE TEXT;

-- Step 3: Add unique constraint on evaluation_id if not exists
-- This ensures only one result per evaluation
DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM pg_constraint 
        WHERE conname = 'kpi_evaluation_results_evaluation_id_key'
    ) THEN
        ALTER TABLE kpi_evaluation_results 
        ADD CONSTRAINT kpi_evaluation_results_evaluation_id_key UNIQUE (evaluation_id);
    END IF;
END $$;

-- Step 4: Add index on evaluation_id for faster lookups
CREATE INDEX IF NOT EXISTS ix_kpi_evaluation_results_evaluation_id 
ON kpi_evaluation_results(evaluation_id);

-- Verify changes
SELECT column_name, data_type, character_maximum_length 
FROM information_schema.columns 
WHERE table_name = 'kpi_evaluation_results';
