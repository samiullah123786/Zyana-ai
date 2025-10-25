-- Migration 008: Mirror Mode (AI Style Learning)
-- Adds user message sampling and style learning

-- User message samples table for style learning
CREATE TABLE IF NOT EXISTS user_message_samples (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES users(id) ON DELETE CASCADE,
    message TEXT NOT NULL,
    intent VARCHAR(100),
    embedding_id VARCHAR(255),
    timestamp TIMESTAMP WITH TIME ZONE NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Extend users table with mirror mode settings
ALTER TABLE users 
ADD COLUMN IF NOT EXISTS mirror_mode_enabled BOOLEAN DEFAULT FALSE,
ADD COLUMN IF NOT EXISTS is_admin BOOLEAN DEFAULT FALSE,
ADD COLUMN IF NOT EXISTS telegram_id VARCHAR(255) UNIQUE;

-- Add style profile to habit_profiles
ALTER TABLE habit_profiles
ADD COLUMN IF NOT EXISTS style_profile JSONB DEFAULT '{}';

-- Indexes for performance
CREATE INDEX IF NOT EXISTS idx_user_message_samples_user_id ON user_message_samples(user_id);
CREATE INDEX IF NOT EXISTS idx_user_message_samples_timestamp ON user_message_samples(timestamp DESC);
CREATE INDEX IF NOT EXISTS idx_user_message_samples_embedding_id ON user_message_samples(embedding_id);
CREATE INDEX IF NOT EXISTS idx_users_telegram_id ON users(telegram_id);

-- Function to limit message samples to last 100 per user
CREATE OR REPLACE FUNCTION limit_message_samples()
RETURNS TRIGGER AS $$
BEGIN
    DELETE FROM user_message_samples
    WHERE user_id = NEW.user_id
    AND id NOT IN (
        SELECT id FROM user_message_samples
        WHERE user_id = NEW.user_id
        ORDER BY timestamp DESC
        LIMIT 100
    );
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Trigger to maintain sample limit
DROP TRIGGER IF EXISTS trigger_limit_message_samples ON user_message_samples;
CREATE TRIGGER trigger_limit_message_samples
AFTER INSERT ON user_message_samples
FOR EACH ROW
EXECUTE FUNCTION limit_message_samples();

-- Enable RLS
ALTER TABLE user_message_samples ENABLE ROW LEVEL SECURITY;

-- RLS Policies
DROP POLICY IF EXISTS "Users can view their message samples" ON user_message_samples;
CREATE POLICY "Users can view their message samples" ON user_message_samples
    FOR SELECT USING (auth.uid() = (SELECT supabase_user_id FROM users WHERE id = user_id));

DROP POLICY IF EXISTS "Users can insert their message samples" ON user_message_samples;
CREATE POLICY "Users can insert their message samples" ON user_message_samples
    FOR INSERT WITH CHECK (auth.uid() = (SELECT supabase_user_id FROM users WHERE id = user_id));

-- Set first user as admin (for single-user setup)
UPDATE users SET is_admin = TRUE WHERE id = 1;

