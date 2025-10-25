-- Migration 007: Work Sessions and Routine Tracking
-- Adds work pattern detection and routine optimization

-- Work sessions table for activity tracking
CREATE TABLE IF NOT EXISTS work_sessions (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES users(id) ON DELETE CASCADE,
    activity_type VARCHAR(100) DEFAULT 'message',
    timestamp TIMESTAMP WITH TIME ZONE NOT NULL,
    day_of_week INTEGER CHECK (day_of_week >= 0 AND day_of_week <= 6),
    hour_of_day INTEGER CHECK (hour_of_day >= 0 AND hour_of_day <= 23),
    metadata JSONB DEFAULT '{}',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Extend habit_profiles table with work pattern fields
ALTER TABLE habit_profiles 
ADD COLUMN IF NOT EXISTS work_hours_start INTEGER CHECK (work_hours_start >= 0 AND work_hours_start <= 23),
ADD COLUMN IF NOT EXISTS work_hours_end INTEGER CHECK (work_hours_end >= 0 AND work_hours_end <= 23),
ADD COLUMN IF NOT EXISTS busy_periods JSONB DEFAULT '[]',
ADD COLUMN IF NOT EXISTS break_suggestions JSONB DEFAULT '[]';

-- Indexes for performance
CREATE INDEX idx_work_sessions_user_id ON work_sessions(user_id);
CREATE INDEX idx_work_sessions_timestamp ON work_sessions(timestamp DESC);
CREATE INDEX idx_work_sessions_day_hour ON work_sessions(day_of_week, hour_of_day);

-- Function to extract day and hour from timestamp
CREATE OR REPLACE FUNCTION set_work_session_time_fields()
RETURNS TRIGGER AS $$
BEGIN
    NEW.day_of_week := EXTRACT(DOW FROM NEW.timestamp);
    NEW.hour_of_day := EXTRACT(HOUR FROM NEW.timestamp);
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Trigger to auto-populate day_of_week and hour_of_day
CREATE TRIGGER trigger_set_work_session_time_fields
BEFORE INSERT ON work_sessions
FOR EACH ROW
EXECUTE FUNCTION set_work_session_time_fields();

-- Enable RLS
ALTER TABLE work_sessions ENABLE ROW LEVEL SECURITY;

-- RLS Policies
CREATE POLICY "Users can view their work sessions" ON work_sessions
    FOR SELECT USING (auth.uid() = (SELECT supabase_user_id FROM users WHERE id = user_id));

CREATE POLICY "Users can insert their work sessions" ON work_sessions
    FOR INSERT WITH CHECK (auth.uid() = (SELECT supabase_user_id FROM users WHERE id = user_id));

