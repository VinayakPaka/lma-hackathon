-- Migration: Add hashed_password column to users table
-- Run this if you're seeing: column users.hashed_password does not exist

-- Step 1: Add hashed_password column to users table
-- Using a default empty string initially, you should update existing users' passwords
ALTER TABLE users 
ADD COLUMN IF NOT EXISTS hashed_password VARCHAR(255);

-- Step 2: For existing users, set a temporary hashed password
-- IMPORTANT: You should update this with actual password hashes for existing users
-- This is a bcrypt hash of 'changeme123' - users should change their passwords
UPDATE users 
SET hashed_password = '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/X4.qWfaQCdvAwXqv.' 
WHERE hashed_password IS NULL;

-- Step 3: Now make the column NOT NULL
ALTER TABLE users 
ALTER COLUMN hashed_password SET NOT NULL;

-- Verify the column exists
SELECT column_name, data_type, is_nullable 
FROM information_schema.columns 
WHERE table_name = 'users' AND column_name = 'hashed_password';
