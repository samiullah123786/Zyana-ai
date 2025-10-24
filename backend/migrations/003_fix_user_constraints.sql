-- Migration 003: Fix user_id foreign key constraints
-- Creates default user and makes constraints more flexible

-- Add telegram_id column to users table if it doesn't exist
DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns 
        WHERE table_name = 'users' AND column_name = 'telegram_id'
    ) THEN
        ALTER TABLE users ADD COLUMN telegram_id TEXT UNIQUE;
    END IF;
END $$;

-- Add name column if it doesn't exist
DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns 
        WHERE table_name = 'users' AND column_name = 'name'
    ) THEN
        ALTER TABLE users ADD COLUMN name TEXT;
    END IF;
END $$;

-- Insert default user with id=1 if it doesn't exist
INSERT INTO users (id, name, created_at)
VALUES (1, 'Default User', NOW())
ON CONFLICT (id) DO NOTHING;

-- Update the default user with telegram_id if not set
UPDATE users SET telegram_id = '1' WHERE id = 1 AND telegram_id IS NULL;

-- Reset the sequence to continue from 2
SELECT setval('users_id_seq', (SELECT MAX(id) FROM users));

-- Add index on telegram_id for fast lookups
CREATE INDEX IF NOT EXISTS idx_users_telegram_id ON users(telegram_id);

-- Drop and recreate foreign key constraints to be more flexible
-- (This allows us to use user_id=1 as default)

-- For transactions table
ALTER TABLE transactions 
DROP CONSTRAINT IF EXISTS transactions_user_id_fkey;

ALTER TABLE transactions
ADD CONSTRAINT transactions_user_id_fkey
FOREIGN KEY (user_id)
REFERENCES users(id)
ON DELETE SET NULL;

-- For loans table
ALTER TABLE loans
DROP CONSTRAINT IF EXISTS loans_user_id_fkey;

ALTER TABLE loans
ADD CONSTRAINT loans_user_id_fkey
FOREIGN KEY (user_id)
REFERENCES users(id)
ON DELETE SET NULL;

-- For habit_profiles table
ALTER TABLE habit_profiles
DROP CONSTRAINT IF EXISTS habit_profiles_user_id_fkey;

ALTER TABLE habit_profiles
ADD CONSTRAINT habit_profiles_user_id_fkey
FOREIGN KEY (user_id)
REFERENCES users(id)
ON DELETE CASCADE;

-- For goals table (if exists)
DO $$
BEGIN
    IF EXISTS (SELECT 1 FROM information_schema.tables WHERE table_name = 'goals') THEN
        ALTER TABLE goals DROP CONSTRAINT IF EXISTS goals_user_id_fkey;
        ALTER TABLE goals
        ADD CONSTRAINT goals_user_id_fkey
        FOREIGN KEY (user_id)
        REFERENCES users(id)
        ON DELETE CASCADE;
    END IF;
END $$;

-- Make user_id nullable in some tables for flexibility
ALTER TABLE transactions ALTER COLUMN user_id DROP NOT NULL;
ALTER TABLE loans ALTER COLUMN user_id DROP NOT NULL;

COMMENT ON TABLE users IS 'User accounts for Zyana AI - supports Telegram and email auth';
COMMENT ON COLUMN users.telegram_id IS 'Telegram user ID for bot integration';

