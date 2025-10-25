-- Migration 006: Scheduled Notifications System
-- Adds auto-notification and reminder scheduling

-- Scheduled notifications table
CREATE TABLE IF NOT EXISTS scheduled_notifications (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES users(id) ON DELETE CASCADE,
    message TEXT NOT NULL,
    scheduled_time TIMESTAMP WITH TIME ZONE NOT NULL,
    status VARCHAR(50) DEFAULT 'pending' CHECK (status IN ('pending', 'sent', 'cancelled', 'failed')),
    telegram_chat_id VARCHAR(255),
    error_message TEXT,
    sent_at TIMESTAMP WITH TIME ZONE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Indexes for performance
CREATE INDEX idx_scheduled_notifications_user_id ON scheduled_notifications(user_id);
CREATE INDEX idx_scheduled_notifications_status ON scheduled_notifications(status);
CREATE INDEX idx_scheduled_notifications_scheduled_time ON scheduled_notifications(scheduled_time);
CREATE INDEX idx_scheduled_notifications_pending ON scheduled_notifications(scheduled_time, status) 
    WHERE status = 'pending';

-- Enable RLS
ALTER TABLE scheduled_notifications ENABLE ROW LEVEL SECURITY;

-- RLS Policies
CREATE POLICY "Users can view their notifications" ON scheduled_notifications
    FOR SELECT USING (auth.uid() = (SELECT supabase_user_id FROM users WHERE id = user_id));

CREATE POLICY "Users can insert their notifications" ON scheduled_notifications
    FOR INSERT WITH CHECK (auth.uid() = (SELECT supabase_user_id FROM users WHERE id = user_id));

CREATE POLICY "Users can update their notifications" ON scheduled_notifications
    FOR UPDATE USING (auth.uid() = (SELECT supabase_user_id FROM users WHERE id = user_id));

CREATE POLICY "Users can delete their notifications" ON scheduled_notifications
    FOR DELETE USING (auth.uid() = (SELECT supabase_user_id FROM users WHERE id = user_id));

