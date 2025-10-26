-- Migration 013: Self-Aware AI Memory System with Auto-Healing
-- Date: 2025-10-26
-- Purpose: Add multi-layer memory (short-term, long-term, semantic) and health monitoring

-- Chat sessions (short-term memory)
CREATE TABLE IF NOT EXISTS chat_sessions (
    id SERIAL PRIMARY KEY,
    user_id TEXT NOT NULL,
    role TEXT NOT NULL CHECK (role IN ('user', 'assistant', 'system')),
    content TEXT NOT NULL,
    timestamp TIMESTAMP DEFAULT NOW(),
    intent TEXT,
    success BOOLEAN DEFAULT true
);
CREATE INDEX idx_chat_sessions_user_time ON chat_sessions(user_id, timestamp DESC);

-- User memory (long-term facts)
CREATE TABLE IF NOT EXISTS user_memory (
    user_id TEXT PRIMARY KEY,
    facts JSONB DEFAULT '[]'::jsonb,
    preferences JSONB DEFAULT '{}'::jsonb,
    last_updated TIMESTAMP DEFAULT NOW()
);

-- Health monitoring (separate from conversational memory)
CREATE TABLE IF NOT EXISTS system_health_log (
    id SERIAL PRIMARY KEY,
    agent_name TEXT NOT NULL,
    status TEXT NOT NULL CHECK (status IN ('healthy', 'degraded', 'failed')),
    error_message TEXT,
    auto_repair_attempted BOOLEAN DEFAULT false,
    auto_repair_success BOOLEAN,
    timestamp TIMESTAMP DEFAULT NOW()
);
CREATE INDEX idx_health_timestamp ON system_health_log(timestamp DESC);
CREATE INDEX idx_health_agent_time ON system_health_log(agent_name, timestamp DESC);

-- Daily health summaries
CREATE TABLE IF NOT EXISTS daily_health_summary (
    id SERIAL PRIMARY KEY,
    date DATE UNIQUE NOT NULL DEFAULT CURRENT_DATE,
    total_checks INTEGER DEFAULT 0,
    failed_checks INTEGER DEFAULT 0,
    issues JSONB DEFAULT '[]'::jsonb,
    summary_sent BOOLEAN DEFAULT false,
    created_at TIMESTAMP DEFAULT NOW()
);
CREATE INDEX idx_daily_summary_date ON daily_health_summary(date DESC);

-- Add comments for documentation
COMMENT ON TABLE chat_sessions IS 'Short-term memory: Recent conversation history';
COMMENT ON TABLE user_memory IS 'Long-term memory: Persistent facts and preferences';
COMMENT ON TABLE system_health_log IS 'Health monitoring: Agent status and auto-repair logs';
COMMENT ON TABLE daily_health_summary IS 'Daily health reports sent to user';

-- Migration complete
SELECT 'Migration 013 completed: Self-Aware AI Memory System with Auto-Healing' AS status;

