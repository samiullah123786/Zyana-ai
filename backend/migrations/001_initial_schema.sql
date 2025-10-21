-- Zyana Initial Database Schema
-- Run this on Supabase SQL Editor or via psql

-- Enable UUID extension
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- Businesses table
CREATE TABLE IF NOT EXISTS businesses (
    id SERIAL PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    slug VARCHAR(255) UNIQUE NOT NULL,
    type VARCHAR(100) DEFAULT 'general',
    description TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Users table (extends Supabase auth.users)
CREATE TABLE IF NOT EXISTS users (
    id SERIAL PRIMARY KEY,
    supabase_user_id UUID REFERENCES auth.users(id) ON DELETE CASCADE,
    name VARCHAR(255),
    email VARCHAR(255),
    preferences JSONB DEFAULT '{}',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    UNIQUE(supabase_user_id)
);

-- Transactions table
CREATE TABLE IF NOT EXISTS transactions (
    id SERIAL PRIMARY KEY,
    business_id INTEGER REFERENCES businesses(id) ON DELETE CASCADE,
    user_id INTEGER REFERENCES users(id) ON DELETE CASCADE,
    type VARCHAR(50) NOT NULL CHECK (type IN ('income', 'expense', 'transfer')),
    amount DECIMAL(15, 2) NOT NULL CHECK (amount > 0),
    currency VARCHAR(10) DEFAULT 'PKR',
    category VARCHAR(100),
    person VARCHAR(255),
    date DATE NOT NULL,
    description TEXT,
    tags TEXT[] DEFAULT '{}',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Loans table
CREATE TABLE IF NOT EXISTS loans (
    id SERIAL PRIMARY KEY,
    business_id INTEGER REFERENCES businesses(id) ON DELETE CASCADE,
    user_id INTEGER REFERENCES users(id) ON DELETE CASCADE,
    person VARCHAR(255) NOT NULL,
    amount DECIMAL(15, 2) NOT NULL CHECK (amount > 0),
    currency VARCHAR(10) DEFAULT 'PKR',
    date DATE NOT NULL,
    status VARCHAR(50) DEFAULT 'active' CHECK (status IN ('active', 'partially_paid', 'paid')),
    remaining_amount DECIMAL(15, 2),
    description TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Loan repayments table
CREATE TABLE IF NOT EXISTS loan_repayments (
    id SERIAL PRIMARY KEY,
    loan_id INTEGER REFERENCES loans(id) ON DELETE CASCADE,
    amount DECIMAL(15, 2) NOT NULL CHECK (amount > 0),
    date DATE NOT NULL,
    description TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Goals table
CREATE TABLE IF NOT EXISTS goals (
    id SERIAL PRIMARY KEY,
    business_id INTEGER REFERENCES businesses(id) ON DELETE CASCADE,
    user_id INTEGER REFERENCES users(id) ON DELETE CASCADE,
    title VARCHAR(255) NOT NULL,
    target_amount DECIMAL(15, 2) NOT NULL,
    current_amount DECIMAL(15, 2) DEFAULT 0,
    currency VARCHAR(10) DEFAULT 'PKR',
    deadline DATE,
    status VARCHAR(50) DEFAULT 'active' CHECK (status IN ('active', 'completed', 'cancelled')),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Events/Calendar table
CREATE TABLE IF NOT EXISTS events (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES users(id) ON DELETE CASCADE,
    title VARCHAR(255) NOT NULL,
    start_time TIMESTAMP WITH TIME ZONE NOT NULL,
    end_time TIMESTAMP WITH TIME ZONE NOT NULL,
    description TEXT,
    location VARCHAR(255),
    google_event_id VARCHAR(255) UNIQUE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Agent logs table
CREATE TABLE IF NOT EXISTS agent_logs (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES users(id) ON DELETE CASCADE,
    agent_type VARCHAR(100) NOT NULL,
    action VARCHAR(255) NOT NULL,
    input_data JSONB,
    output_data JSONB,
    status VARCHAR(50) DEFAULT 'pending' CHECK (status IN ('success', 'error', 'pending')),
    error_message TEXT,
    timestamp TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Habit profiles table
CREATE TABLE IF NOT EXISTS habit_profiles (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES users(id) ON DELETE CASCADE,
    key VARCHAR(255) NOT NULL,
    value TEXT NOT NULL,
    confidence_score DECIMAL(3, 2) DEFAULT 0.5 CHECK (confidence_score >= 0 AND confidence_score <= 1),
    occurrences INTEGER DEFAULT 1,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    UNIQUE(user_id, key)
);

-- Memory summaries table
CREATE TABLE IF NOT EXISTS memory_summaries (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES users(id) ON DELETE CASCADE,
    date DATE NOT NULL,
    summary TEXT NOT NULL,
    embedding_id VARCHAR(255),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    UNIQUE(user_id, date)
);

-- Indexes for performance
CREATE INDEX idx_transactions_business_id ON transactions(business_id);
CREATE INDEX idx_transactions_date ON transactions(date DESC);
CREATE INDEX idx_transactions_person ON transactions(person);
CREATE INDEX idx_loans_business_id ON loans(business_id);
CREATE INDEX idx_loans_person ON loans(person);
CREATE INDEX idx_loans_status ON loans(status);
CREATE INDEX idx_events_user_id ON events(user_id);
CREATE INDEX idx_events_start_time ON events(start_time);
CREATE INDEX idx_agent_logs_user_id ON agent_logs(user_id);
CREATE INDEX idx_agent_logs_timestamp ON agent_logs(timestamp DESC);
CREATE INDEX idx_habit_profiles_user_id ON habit_profiles(user_id);

-- Materialized view for business balances
CREATE MATERIALIZED VIEW business_balances AS
SELECT 
    b.id as business_id,
    b.name as business_name,
    b.slug,
    COALESCE(SUM(CASE WHEN t.type = 'income' THEN t.amount ELSE 0 END), 0) as total_income,
    COALESCE(SUM(CASE WHEN t.type = 'expense' THEN t.amount ELSE 0 END), 0) as total_expenses,
    COALESCE(SUM(CASE WHEN t.type = 'income' THEN t.amount ELSE -t.amount END), 0) as balance
FROM businesses b
LEFT JOIN transactions t ON b.id = t.business_id
GROUP BY b.id, b.name, b.slug;

-- Index on materialized view
CREATE UNIQUE INDEX idx_business_balances_id ON business_balances(business_id);

-- Function to refresh business balances
CREATE OR REPLACE FUNCTION refresh_business_balances()
RETURNS TRIGGER AS $$
BEGIN
    REFRESH MATERIALIZED VIEW CONCURRENTLY business_balances;
    RETURN NULL;
END;
$$ LANGUAGE plpgsql;

-- Trigger to refresh balances on transaction changes
CREATE TRIGGER trigger_refresh_balances
AFTER INSERT OR UPDATE OR DELETE ON transactions
FOR EACH STATEMENT
EXECUTE FUNCTION refresh_business_balances();

-- Enable Row Level Security (RLS)
ALTER TABLE businesses ENABLE ROW LEVEL SECURITY;
ALTER TABLE users ENABLE ROW LEVEL SECURITY;
ALTER TABLE transactions ENABLE ROW LEVEL SECURITY;
ALTER TABLE loans ENABLE ROW LEVEL SECURITY;
ALTER TABLE loan_repayments ENABLE ROW LEVEL SECURITY;
ALTER TABLE goals ENABLE ROW LEVEL SECURITY;
ALTER TABLE events ENABLE ROW LEVEL SECURITY;
ALTER TABLE agent_logs ENABLE ROW LEVEL SECURITY;
ALTER TABLE habit_profiles ENABLE ROW LEVEL SECURITY;
ALTER TABLE memory_summaries ENABLE ROW LEVEL SECURITY;

-- RLS Policies (allow users to access their own data)
CREATE POLICY "Users can view their own data" ON users
    FOR SELECT USING (auth.uid() = supabase_user_id);

CREATE POLICY "Users can view all businesses" ON businesses
    FOR SELECT USING (true);

CREATE POLICY "Users can view their transactions" ON transactions
    FOR SELECT USING (auth.uid() = (SELECT supabase_user_id FROM users WHERE id = user_id));

CREATE POLICY "Users can insert their transactions" ON transactions
    FOR INSERT WITH CHECK (auth.uid() = (SELECT supabase_user_id FROM users WHERE id = user_id));

CREATE POLICY "Users can view their loans" ON loans
    FOR SELECT USING (auth.uid() = (SELECT supabase_user_id FROM users WHERE id = user_id));

CREATE POLICY "Users can insert their loans" ON loans
    FOR INSERT WITH CHECK (auth.uid() = (SELECT supabase_user_id FROM users WHERE id = user_id));

CREATE POLICY "Users can view their events" ON events
    FOR SELECT USING (auth.uid() = (SELECT supabase_user_id FROM users WHERE id = user_id));

CREATE POLICY "Users can insert their events" ON events
    FOR INSERT WITH CHECK (auth.uid() = (SELECT supabase_user_id FROM users WHERE id = user_id));

-- Seed data: Initial businesses
INSERT INTO businesses (name, slug, type, description) VALUES
    ('Vidify', 'vidify', 'video_production', 'Video production and editing business'),
    ('MilkBusiness', 'milk-business', 'dairy', 'Dairy and milk distribution business'),
    ('Yazman Express', 'yazman-express', 'logistics', 'Transport and logistics services')
ON CONFLICT (slug) DO NOTHING;

-- Create default user (will be linked to Supabase auth later)
-- This is a placeholder; actual user creation happens via Supabase Auth

