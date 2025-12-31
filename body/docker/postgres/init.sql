-- =============================================================================
-- SCORPION - PostgreSQL Initialization
-- =============================================================================
-- Creates databases and tables for SCORPION services.
-- =============================================================================

-- Create n8n database
CREATE DATABASE n8n;

-- Create scorpion application database
CREATE DATABASE scorpion_app;

-- Switch to scorpion_app database
\c scorpion_app;

-- Create schemas
CREATE SCHEMA IF NOT EXISTS leads;
CREATE SCHEMA IF NOT EXISTS crm;
CREATE SCHEMA IF NOT EXISTS lcms;
CREATE SCHEMA IF NOT EXISTS calls;

-- Leads table
CREATE TABLE IF NOT EXISTS leads.leads (
    id VARCHAR(50) PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    email VARCHAR(255) NOT NULL,
    phone VARCHAR(50),
    company VARCHAR(255),
    source VARCHAR(50),
    score INTEGER DEFAULT 0,
    priority INTEGER DEFAULT 5,
    status VARCHAR(50) DEFAULT 'new',
    assigned_leg VARCHAR(50),
    metadata JSONB DEFAULT '{}',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- CRM deals table
CREATE TABLE IF NOT EXISTS crm.deals (
    id VARCHAR(50) PRIMARY KEY,
    lead_id VARCHAR(50) REFERENCES leads.leads(id),
    name VARCHAR(255) NOT NULL,
    company VARCHAR(255),
    value DECIMAL(12,2) DEFAULT 0,
    stage VARCHAR(50) DEFAULT 'new',
    probability INTEGER DEFAULT 10,
    owner VARCHAR(100),
    expected_close DATE,
    actual_close DATE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- LCMS courses table
CREATE TABLE IF NOT EXISTS lcms.courses (
    id VARCHAR(50) PRIMARY KEY,
    title VARCHAR(255) NOT NULL,
    description TEXT,
    instructor VARCHAR(255),
    is_published BOOLEAN DEFAULT FALSE,
    price DECIMAL(10,2) DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- LCMS enrollments table
CREATE TABLE IF NOT EXISTS lcms.enrollments (
    id VARCHAR(50) PRIMARY KEY,
    student_id VARCHAR(50) NOT NULL,
    course_id VARCHAR(50) REFERENCES lcms.courses(id),
    status VARCHAR(50) DEFAULT 'active',
    progress DECIMAL(5,2) DEFAULT 0,
    started_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    completed_at TIMESTAMP
);

-- Call logs table
CREATE TABLE IF NOT EXISTS calls.call_logs (
    id VARCHAR(50) PRIMARY KEY,
    patient_name VARCHAR(255) NOT NULL,
    patient_phone VARCHAR(50),
    outcome VARCHAR(50) NOT NULL,
    notes TEXT,
    duration_seconds INTEGER DEFAULT 0,
    appointment_date DATE,
    appointment_time TIME,
    provider VARCHAR(255),
    caller_id VARCHAR(100),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Create indexes
CREATE INDEX IF NOT EXISTS idx_leads_email ON leads.leads(email);
CREATE INDEX IF NOT EXISTS idx_leads_status ON leads.leads(status);
CREATE INDEX IF NOT EXISTS idx_deals_stage ON crm.deals(stage);
CREATE INDEX IF NOT EXISTS idx_enrollments_student ON lcms.enrollments(student_id);
CREATE INDEX IF NOT EXISTS idx_calls_date ON calls.call_logs(created_at);

-- Grant permissions
GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA leads TO scorpion;
GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA crm TO scorpion;
GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA lcms TO scorpion;
GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA calls TO scorpion;
