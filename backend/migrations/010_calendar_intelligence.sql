-- Migration 010: Calendar Intelligence System
-- Adds tables for session management, enhanced calendar events, and agent profile

-- =====================================================
-- Session state for multi-turn clarifications
-- =====================================================
CREATE TABLE IF NOT EXISTS sessions (
    id TEXT PRIMARY KEY,
    user_id TEXT NOT NULL,
    intent TEXT,
    pending_fields TEXT[],
    partial_data JSONB DEFAULT '{}'::jsonb,
    conversation_history JSONB[] DEFAULT ARRAY[]::JSONB[],
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    expires_at TIMESTAMP WITH TIME ZONE,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    status TEXT DEFAULT 'pending' CHECK (status IN ('pending', 'completed', 'cancelled', 'expired'))
);

-- Index for finding active sessions by user
CREATE INDEX IF NOT EXISTS idx_sessions_user_status 
ON sessions(user_id, status) 
WHERE status = 'pending';

-- Index for cleanup of expired sessions
CREATE INDEX IF NOT EXISTS idx_sessions_expires 
ON sessions(expires_at) 
WHERE status = 'pending';

-- =====================================================
-- Enhanced calendar events with full context
-- =====================================================
CREATE TABLE IF NOT EXISTS calendar_events (
    id SERIAL PRIMARY KEY,
    user_id TEXT NOT NULL,
    session_id TEXT REFERENCES sessions(id) ON DELETE SET NULL,
    raw_user_text TEXT NOT NULL,
    resolved_title TEXT NOT NULL,
    resolved_start_iso TIMESTAMP WITH TIME ZONE NOT NULL,
    resolved_end_iso TIMESTAMP WITH TIME ZONE NOT NULL,
    attendees TEXT[] DEFAULT ARRAY[]::TEXT[],
    location TEXT,
    google_event_id TEXT,
    confidence_score FLOAT DEFAULT 1.0 CHECK (confidence_score >= 0.0 AND confidence_score <= 1.0),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Indexes for calendar_events
CREATE INDEX IF NOT EXISTS idx_calendar_events_user 
ON calendar_events(user_id);

CREATE INDEX IF NOT EXISTS idx_calendar_events_start_time 
ON calendar_events(resolved_start_iso);

CREATE INDEX IF NOT EXISTS idx_calendar_events_session 
ON calendar_events(session_id);

-- =====================================================
-- Conversation history linked to sessions
-- =====================================================
CREATE TABLE IF NOT EXISTS conversations (
    id SERIAL PRIMARY KEY,
    user_id TEXT NOT NULL,
    session_id TEXT REFERENCES sessions(id) ON DELETE CASCADE,
    message TEXT NOT NULL,
    role TEXT NOT NULL CHECK (role IN ('user', 'assistant', 'system')),
    intent TEXT,
    metadata JSONB DEFAULT '{}'::jsonb,
    timestamp TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Indexes for conversations
CREATE INDEX IF NOT EXISTS idx_conversations_session 
ON conversations(session_id);

CREATE INDEX IF NOT EXISTS idx_conversations_user_time 
ON conversations(user_id, timestamp DESC);

-- =====================================================
-- Agent profile for self-description
-- =====================================================
CREATE TABLE IF NOT EXISTS agent_profile (
    id SERIAL PRIMARY KEY,
    name TEXT NOT NULL,
    owner TEXT NOT NULL,
    capabilities JSONB DEFAULT '[]'::jsonb,
    default_timezone TEXT NOT NULL DEFAULT 'Asia/Karachi',
    version TEXT,
    metadata JSONB DEFAULT '{}'::jsonb,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Insert default agent profile
INSERT INTO agent_profile (name, owner, capabilities, default_timezone, version, metadata)
VALUES (
    'Zyana',
    'Sami',
    '[
        "Schedule and manage calendar events",
        "Track financial transactions and loans",
        "Transcribe voice messages via Groq Whisper",
        "Generate invoices and manage clients",
        "Learn habits and preferences",
        "Provide intelligent insights and analysis",
        "Natural conversation with context awareness"
    ]'::jsonb,
    'Asia/Karachi',
    '2.0.0',
    '{
        "features": ["calendar_intelligence", "multi_turn_clarification", "vector_memory"],
        "ai_models": ["Fal AI GPT-5", "Groq Whisper", "OpenAI Embeddings"]
    }'::jsonb
)
ON CONFLICT DO NOTHING;

-- =====================================================
-- Update events table to link with calendar_events
-- =====================================================
-- Add column to link legacy events table with new calendar_events
ALTER TABLE events 
ADD COLUMN IF NOT EXISTS calendar_event_id INTEGER REFERENCES calendar_events(id) ON DELETE SET NULL;

-- =====================================================
-- Cleanup function for expired sessions
-- =====================================================
CREATE OR REPLACE FUNCTION cleanup_expired_sessions()
RETURNS INTEGER AS $$
DECLARE
    deleted_count INTEGER;
BEGIN
    UPDATE sessions
    SET status = 'expired'
    WHERE status = 'pending'
    AND expires_at < NOW();
    
    GET DIAGNOSTICS deleted_count = ROW_COUNT;
    
    RETURN deleted_count;
END;
$$ LANGUAGE plpgsql;

-- =====================================================
-- Comments for documentation
-- =====================================================
COMMENT ON TABLE sessions IS 'Multi-turn conversation sessions for clarifications';
COMMENT ON TABLE calendar_events IS 'Enhanced calendar events with full conversation context';
COMMENT ON TABLE conversations IS 'Message history linked to sessions';
COMMENT ON TABLE agent_profile IS 'Agent self-description and capabilities';

COMMENT ON COLUMN sessions.pending_fields IS 'Array of field names that need clarification';
COMMENT ON COLUMN sessions.partial_data IS 'JSON object with partially resolved event data';
COMMENT ON COLUMN sessions.conversation_history IS 'Array of JSON messages in the conversation';

COMMENT ON COLUMN calendar_events.raw_user_text IS 'Original natural language request from user';
COMMENT ON COLUMN calendar_events.confidence_score IS 'AI confidence in datetime parsing (0.0-1.0)';
COMMENT ON COLUMN calendar_events.resolved_start_iso IS 'Final resolved start time with timezone';
COMMENT ON COLUMN calendar_events.resolved_end_iso IS 'Final resolved end time with timezone';

-- =====================================================
-- Grant permissions (adjust as needed for your setup)
-- =====================================================
-- GRANT ALL ON sessions TO your_app_user;
-- GRANT ALL ON calendar_events TO your_app_user;
-- GRANT ALL ON conversations TO your_app_user;
-- GRANT ALL ON agent_profile TO your_app_user;
-- GRANT USAGE, SELECT ON ALL SEQUENCES IN SCHEMA public TO your_app_user;

