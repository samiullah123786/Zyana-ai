-- Migration 011: Feedback System
-- Adds feedback collection for response quality improvement

-- Feedback table for user ratings and comments
CREATE TABLE IF NOT EXISTS feedback (
    id SERIAL PRIMARY KEY,
    user_id TEXT NOT NULL,
    source_type TEXT NOT NULL,  -- 'message', 'calendar', 'transaction', 'general'
    source_id TEXT,              -- ID of the message/event/transaction
    rating INTEGER CHECK (rating BETWEEN 1 AND 5),
    comment TEXT,
    metadata JSONB DEFAULT '{}'::jsonb,
    reviewed BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Indexes for performance
CREATE INDEX IF NOT EXISTS idx_feedback_user ON feedback(user_id);
CREATE INDEX IF NOT EXISTS idx_feedback_source ON feedback(source_type, source_id);
CREATE INDEX IF NOT EXISTS idx_feedback_rating ON feedback(rating);
CREATE INDEX IF NOT EXISTS idx_feedback_reviewed ON feedback(reviewed);
CREATE INDEX IF NOT EXISTS idx_feedback_created ON feedback(created_at DESC);

-- Auto-update updated_at timestamp
CREATE OR REPLACE FUNCTION update_feedback_updated_at()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER feedback_updated_at
    BEFORE UPDATE ON feedback
    FOR EACH ROW
    EXECUTE FUNCTION update_feedback_updated_at();

-- Enable RLS
ALTER TABLE feedback ENABLE ROW LEVEL SECURITY;

-- RLS Policies
DROP POLICY IF EXISTS "Users can view their own feedback" ON feedback;
CREATE POLICY "Users can view their own feedback" ON feedback
    FOR SELECT USING (user_id = current_setting('app.current_user_id', TRUE));

DROP POLICY IF EXISTS "Users can insert their own feedback" ON feedback;
CREATE POLICY "Users can insert their own feedback" ON feedback
    FOR INSERT WITH CHECK (user_id = current_setting('app.current_user_id', TRUE));

-- Admin can view all feedback
DROP POLICY IF EXISTS "Admins can view all feedback" ON feedback;
CREATE POLICY "Admins can view all feedback" ON feedback
    FOR SELECT USING (
        EXISTS (
            SELECT 1 FROM users 
            WHERE telegram_id = current_setting('app.current_user_id', TRUE)
            AND is_admin = TRUE
        )
    );

-- Comments
COMMENT ON TABLE feedback IS 'User feedback for response quality improvement';
COMMENT ON COLUMN feedback.source_type IS 'Type of content being rated: message, calendar, transaction, general';
COMMENT ON COLUMN feedback.source_id IS 'ID of the source message/event/transaction';
COMMENT ON COLUMN feedback.rating IS 'Rating from 1 (poor) to 5 (excellent)';
COMMENT ON COLUMN feedback.reviewed IS 'Whether admin has reviewed this feedback';
COMMENT ON COLUMN feedback.metadata IS 'Additional context like original message, response, etc.';

