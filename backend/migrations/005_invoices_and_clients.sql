-- Migration 005: Invoices and Clients System
-- Adds client management and invoice tracking capabilities

-- Clients table
CREATE TABLE IF NOT EXISTS clients (
    id SERIAL PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    contact VARCHAR(255),
    email VARCHAR(255),
    company VARCHAR(255),
    business_id INTEGER REFERENCES businesses(id) ON DELETE CASCADE,
    notes TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Invoices table
CREATE TABLE IF NOT EXISTS invoices (
    id SERIAL PRIMARY KEY,
    invoice_number VARCHAR(50) UNIQUE NOT NULL,
    client_id INTEGER REFERENCES clients(id) ON DELETE CASCADE,
    business_id INTEGER REFERENCES businesses(id) ON DELETE CASCADE,
    user_id INTEGER REFERENCES users(id) ON DELETE CASCADE,
    amount DECIMAL(15, 2) NOT NULL CHECK (amount > 0),
    currency VARCHAR(10) DEFAULT 'PKR',
    due_date DATE NOT NULL,
    status VARCHAR(50) DEFAULT 'pending' CHECK (status IN ('pending', 'paid', 'overdue', 'cancelled')),
    payment_date DATE,
    notes TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Indexes for performance
CREATE INDEX idx_clients_business_id ON clients(business_id);
CREATE INDEX idx_clients_name ON clients(name);
CREATE INDEX idx_invoices_client_id ON invoices(client_id);
CREATE INDEX idx_invoices_business_id ON invoices(business_id);
CREATE INDEX idx_invoices_status ON invoices(status);
CREATE INDEX idx_invoices_due_date ON invoices(due_date);
CREATE INDEX idx_invoices_invoice_number ON invoices(invoice_number);

-- Function to auto-update status to overdue
CREATE OR REPLACE FUNCTION update_invoice_status()
RETURNS void AS $$
BEGIN
    UPDATE invoices
    SET status = 'overdue'
    WHERE status = 'pending' 
    AND due_date < CURRENT_DATE;
END;
$$ LANGUAGE plpgsql;

-- Enable RLS
ALTER TABLE clients ENABLE ROW LEVEL SECURITY;
ALTER TABLE invoices ENABLE ROW LEVEL SECURITY;

-- RLS Policies
CREATE POLICY "Users can view all clients" ON clients
    FOR SELECT USING (true);

CREATE POLICY "Users can insert clients" ON clients
    FOR INSERT WITH CHECK (true);

CREATE POLICY "Users can update clients" ON clients
    FOR UPDATE USING (true);

CREATE POLICY "Users can delete clients" ON clients
    FOR DELETE USING (true);

CREATE POLICY "Users can view all invoices" ON invoices
    FOR SELECT USING (true);

CREATE POLICY "Users can insert invoices" ON invoices
    FOR INSERT WITH CHECK (true);

CREATE POLICY "Users can update invoices" ON invoices
    FOR UPDATE USING (true);

CREATE POLICY "Users can delete invoices" ON invoices
    FOR DELETE USING (true);

