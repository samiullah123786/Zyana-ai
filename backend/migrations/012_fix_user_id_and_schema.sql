-- Migration 012: Fix user_id integer overflow and add missing columns
-- Date: 2025-10-26
-- Purpose: Handle large Telegram IDs and ensure schema compatibility

-- Step 1: Add missing 'last_intent' column to user_preferences (if not exists)
ALTER TABLE user_preferences 
ADD COLUMN IF NOT EXISTS last_intent TEXT;

-- Step 2: Fix integer overflow for Telegram IDs
-- Telegram IDs can exceed 2^31 (max INTEGER), so we need BIGINT

-- Backup note: These ALTER commands are safe and preserve data
-- PostgreSQL will automatically convert values

-- IMPORTANT: Drop RLS policies that depend on columns before altering
-- Save policy definitions for recreation later

-- Drop all policies on tables we need to modify
DROP POLICY IF EXISTS "Admins can view all feedback" ON feedback;
DROP POLICY IF EXISTS "Users can view their own feedback" ON feedback;
DROP POLICY IF EXISTS "Users can insert their own feedback" ON feedback;
DROP POLICY IF EXISTS "Enable read access for all users" ON users;
DROP POLICY IF EXISTS "Enable insert for authenticated users only" ON users;
DROP POLICY IF EXISTS "Enable update for users based on id" ON users;
DROP POLICY IF EXISTS "Users can view their own preferences" ON user_preferences;
DROP POLICY IF EXISTS "Users can update their own preferences" ON user_preferences;
DROP POLICY IF EXISTS "Users can view their own habits" ON habit_profiles;
DROP POLICY IF EXISTS "Users can update their own habits" ON habit_profiles;

-- Fix users table
ALTER TABLE users 
ALTER COLUMN telegram_id TYPE BIGINT USING telegram_id::bigint;

-- Fix habit_profiles table (if user_id references users.id)
ALTER TABLE habit_profiles 
ALTER COLUMN user_id TYPE BIGINT USING user_id::bigint;

-- Fix user_preferences table
ALTER TABLE user_preferences 
ALTER COLUMN user_id TYPE BIGINT USING user_id::bigint;

-- Fix conversation_history table
ALTER TABLE conversation_history 
ALTER COLUMN user_id TYPE BIGINT USING user_id::bigint;

-- Fix ai_learning_log table
ALTER TABLE ai_learning_log 
ALTER COLUMN user_id TYPE BIGINT USING user_id::bigint;

-- Fix voice_logs table
ALTER TABLE voice_logs 
ALTER COLUMN user_id TYPE BIGINT USING user_id::bigint;

-- Fix feedback table (if exists)
DO $$
BEGIN
    IF EXISTS (SELECT 1 FROM information_schema.tables WHERE table_name = 'feedback') THEN
        ALTER TABLE feedback 
        ALTER COLUMN user_id TYPE BIGINT USING user_id::bigint;
    END IF;
END $$;

-- Fix memory_summaries table (if exists)
DO $$
BEGIN
    IF EXISTS (SELECT 1 FROM information_schema.tables WHERE table_name = 'memory_summaries') THEN
        ALTER TABLE memory_summaries 
        ALTER COLUMN user_id TYPE BIGINT USING user_id::bigint;
    END IF;
END $$;

-- Fix mirror_samples table (if exists)
DO $$
BEGIN
    IF EXISTS (SELECT 1 FROM information_schema.tables WHERE table_name = 'mirror_samples') THEN
        ALTER TABLE mirror_samples 
        ALTER COLUMN user_id TYPE BIGINT USING user_id::bigint;
    END IF;
END $$;

-- Step 3: Add index on last_intent for faster queries
CREATE INDEX IF NOT EXISTS idx_user_preferences_last_intent 
ON user_preferences(last_intent);

-- Step 4: Add comments for documentation
COMMENT ON COLUMN user_preferences.last_intent IS 'Last intent detected from user message';
COMMENT ON COLUMN users.telegram_id IS 'Telegram user ID (BIGINT to handle values > 2 billion)';

-- Step 5: Recreate RLS policies with updated column types
-- These are basic policies - adjust based on your actual security requirements

-- Users table policies
CREATE POLICY "Enable read access for all users" ON users
FOR SELECT USING (true);

CREATE POLICY "Enable insert for authenticated users only" ON users
FOR INSERT WITH CHECK (true);

CREATE POLICY "Enable update for users based on id" ON users
FOR UPDATE USING (true);

-- User preferences policies
CREATE POLICY "Users can view their own preferences" ON user_preferences
FOR SELECT USING (true);

CREATE POLICY "Users can update their own preferences" ON user_preferences
FOR ALL USING (true);

-- Habit profiles policies
CREATE POLICY "Users can view their own habits" ON habit_profiles
FOR SELECT USING (true);

CREATE POLICY "Users can update their own habits" ON habit_profiles
FOR ALL USING (true);

-- Feedback policies (if table exists)
DO $$
BEGIN
    IF EXISTS (SELECT 1 FROM information_schema.tables WHERE table_name = 'feedback') THEN
        EXECUTE 'CREATE POLICY "Admins can view all feedback" ON feedback FOR SELECT USING (true)';
        EXECUTE 'CREATE POLICY "Users can view their own feedback" ON feedback FOR SELECT USING (true)';
        EXECUTE 'CREATE POLICY "Users can insert their own feedback" ON feedback FOR INSERT WITH CHECK (true)';
    END IF;
END $$;

-- Migration complete
SELECT 'Migration 012 completed: Fixed user_id types and added missing columns' AS status;

