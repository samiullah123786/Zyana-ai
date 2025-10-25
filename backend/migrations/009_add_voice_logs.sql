-- Migration 009: Add voice_logs table for Groq Whisper transcription tracking
-- This table stores all voice message transcriptions from Telegram, Discord, etc.

-- Create voice_logs table
CREATE TABLE IF NOT EXISTS voice_logs (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id integer REFERENCES users(id) ON DELETE SET NULL,
  source text NOT NULL,                 -- e.g., 'telegram_voice', 'telegram_audio', 'discord'
  file_url text,                        -- Signed URL to original audio in Supabase Storage
  file_size_bytes bigint,
  duration_seconds numeric,
  transcription text,
  language text,
  confidence numeric,                   -- Confidence score from Groq (if available)
  model_used text DEFAULT 'whisper-large-v3-turbo',  -- Which Groq model was used
  meta jsonb DEFAULT '{}',              -- Additional metadata (chunks, timestamps, etc.)
  created_at timestamptz DEFAULT now(),
  updated_at timestamptz DEFAULT now()
);

-- Create indexes for faster queries
CREATE INDEX IF NOT EXISTS idx_voice_logs_userid ON voice_logs(user_id);
CREATE INDEX IF NOT EXISTS idx_voice_logs_created_at ON voice_logs(created_at DESC);
CREATE INDEX IF NOT EXISTS idx_voice_logs_source ON voice_logs(source);

-- Create updated_at trigger
CREATE OR REPLACE FUNCTION update_voice_logs_updated_at()
RETURNS TRIGGER AS $$
BEGIN
  NEW.updated_at = now();
  RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER voice_logs_updated_at
  BEFORE UPDATE ON voice_logs
  FOR EACH ROW
  EXECUTE FUNCTION update_voice_logs_updated_at();

-- Add comment
COMMENT ON TABLE voice_logs IS 'Stores voice message transcriptions from Groq Whisper API';
COMMENT ON COLUMN voice_logs.source IS 'Platform source: telegram_voice, telegram_audio, discord, etc.';
COMMENT ON COLUMN voice_logs.file_url IS 'Signed URL to original audio file in Supabase Storage';
COMMENT ON COLUMN voice_logs.meta IS 'JSON metadata: chunks, timestamps, error logs, etc.';

-- Grant permissions (adjust based on your RLS policies)
-- For admin access only:
-- ALTER TABLE voice_logs ENABLE ROW LEVEL SECURITY;
-- CREATE POLICY "Admin can view all voice logs" ON voice_logs FOR SELECT USING (auth.role() = 'admin');

