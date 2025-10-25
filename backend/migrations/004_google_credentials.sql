-- Migration 004: Add Google Calendar OAuth credentials storage
-- This allows credentials to persist across server restarts on Render

-- Add columns for storing Google OAuth credentials
ALTER TABLE users ADD COLUMN IF NOT EXISTS google_credentials TEXT;
ALTER TABLE users ADD COLUMN IF NOT EXISTS google_calendar_connected BOOLEAN DEFAULT FALSE;
ALTER TABLE users ADD COLUMN IF NOT EXISTS google_calendar_email TEXT;

-- Update existing user (user_id=1) to enable tracking
UPDATE users 
SET google_calendar_connected = FALSE 
WHERE id = 1 AND google_calendar_connected IS NULL;

-- Add index for faster lookups
CREATE INDEX IF NOT EXISTS idx_users_telegram_id ON users(telegram_id);
CREATE INDEX IF NOT EXISTS idx_users_google_connected ON users(google_calendar_connected);

