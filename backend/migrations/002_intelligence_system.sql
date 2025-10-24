-- Migration 002: JARVIS-Level Intelligence System
-- Adds tables for conversation tracking, AI learning, and user preferences

-- Conversation history for context-aware responses
CREATE TABLE IF NOT EXISTS conversation_history (
    id BIGSERIAL PRIMARY KEY,
    user_id TEXT NOT NULL,
    message TEXT NOT NULL,
    intent TEXT,
    timestamp TIMESTAMPTZ DEFAULT NOW(),
    metadata JSONB DEFAULT '{}'::jsonb
);

CREATE INDEX idx_conversation_user_time ON conversation_history(user_id, timestamp DESC);

-- AI learning log for pattern detection
CREATE TABLE IF NOT EXISTS ai_learning_log (
    id BIGSERIAL PRIMARY KEY,
    user_id TEXT NOT NULL,
    message TEXT NOT NULL,
    intent TEXT NOT NULL,
    entities JSONB DEFAULT '{}'::jsonb,
    outcome TEXT NOT NULL,
    confidence FLOAT,
    timestamp TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_learning_user_intent ON ai_learning_log(user_id, intent);
CREATE INDEX idx_learning_timestamp ON ai_learning_log(timestamp DESC);

-- User preferences for personalization
CREATE TABLE IF NOT EXISTS user_preferences (
    id BIGSERIAL PRIMARY KEY,
    user_id TEXT UNIQUE NOT NULL,
    timezone TEXT DEFAULT 'UTC',
    language TEXT DEFAULT 'en',
    default_currency TEXT DEFAULT 'PKR',
    default_business_id BIGINT REFERENCES businesses(id) ON DELETE SET NULL,
    notification_preferences JSONB DEFAULT '{}'::jsonb,
    ai_settings JSONB DEFAULT '{}'::jsonb,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_prefs_user ON user_preferences(user_id);

-- Smart insights cache
CREATE TABLE IF NOT EXISTS insights_cache (
    id BIGSERIAL PRIMARY KEY,
    user_id TEXT NOT NULL,
    insight_type TEXT NOT NULL,
    data JSONB NOT NULL,
    generated_at TIMESTAMPTZ DEFAULT NOW(),
    expires_at TIMESTAMPTZ
);

CREATE INDEX idx_insights_user_type ON insights_cache(user_id, insight_type);
CREATE INDEX idx_insights_expiry ON insights_cache(expires_at);

-- Function to auto-update updated_at timestamp
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER update_user_preferences_updated_at
    BEFORE UPDATE ON user_preferences
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

-- Grant permissions (adjust as needed)
-- Note: In Supabase, you may need to set RLS policies instead

COMMENT ON TABLE conversation_history IS 'Stores conversation context for multi-turn interactions';
COMMENT ON TABLE ai_learning_log IS 'Logs AI interactions for pattern learning and improvement';
COMMENT ON TABLE user_preferences IS 'User settings and learned preferences';
COMMENT ON TABLE insights_cache IS 'Cached intelligent insights to reduce computation';

