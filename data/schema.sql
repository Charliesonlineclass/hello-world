-- SCORPION CRM Database Schema
-- SQLite3
-- Run: sqlite3 crm.db < schema.sql

-- =============================================================================
-- LEADS TABLE
-- =============================================================================
CREATE TABLE IF NOT EXISTS leads (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    contact TEXT NOT NULL,
    project_type TEXT DEFAULT 'other' CHECK (project_type IN ('full', 'kitchen', 'bathroom', 'other')),
    source TEXT DEFAULT 'manual',
    urgency TEXT DEFAULT 'later' CHECK (urgency IN ('asap', 'soon', 'later')),
    budget TEXT DEFAULT 'under5k' CHECK (budget IN ('over30k', '15to30k', '5to15k', 'under5k')),
    score INTEGER DEFAULT 0,
    status TEXT DEFAULT 'new' CHECK (status IN ('new', 'contacted', 'qualified', 'proposal', 'won', 'lost')),
    assigned_agent TEXT,
    notes TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- =============================================================================
-- AGENTS TABLE
-- =============================================================================
CREATE TABLE IF NOT EXISTS agents (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL UNIQUE,
    email TEXT,
    phone TEXT,
    active INTEGER DEFAULT 1,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- =============================================================================
-- ACTIVITY LOG (for tracking lead changes)
-- =============================================================================
CREATE TABLE IF NOT EXISTS activity_log (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    lead_id INTEGER,
    agent_name TEXT,
    action TEXT NOT NULL,
    old_value TEXT,
    new_value TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (lead_id) REFERENCES leads(id) ON DELETE CASCADE
);

-- =============================================================================
-- INDEXES
-- =============================================================================
-- Speed up common queries
CREATE INDEX IF NOT EXISTS idx_leads_status ON leads(status);
CREATE INDEX IF NOT EXISTS idx_leads_agent ON leads(assigned_agent);
CREATE INDEX IF NOT EXISTS idx_leads_score ON leads(score DESC);
CREATE INDEX IF NOT EXISTS idx_leads_created ON leads(created_at DESC);
CREATE INDEX IF NOT EXISTS idx_leads_urgency ON leads(urgency);
CREATE INDEX IF NOT EXISTS idx_activity_lead ON activity_log(lead_id);
CREATE INDEX IF NOT EXISTS idx_activity_date ON activity_log(created_at DESC);

-- =============================================================================
-- TRIGGERS
-- =============================================================================
-- Auto-update updated_at timestamp
CREATE TRIGGER IF NOT EXISTS update_lead_timestamp
AFTER UPDATE ON leads
FOR EACH ROW
BEGIN
    UPDATE leads SET updated_at = CURRENT_TIMESTAMP WHERE id = NEW.id;
END;

-- =============================================================================
-- VIEWS
-- =============================================================================
-- Hot leads view (score > 50)
CREATE VIEW IF NOT EXISTS hot_leads AS
SELECT * FROM leads
WHERE score > 50 AND status NOT IN ('won', 'lost')
ORDER BY score DESC;

-- Pipeline summary view
CREATE VIEW IF NOT EXISTS pipeline_summary AS
SELECT
    status,
    COUNT(*) as count,
    AVG(score) as avg_score,
    SUM(CASE
        WHEN budget = 'over30k' THEN 35000
        WHEN budget = '15to30k' THEN 22500
        WHEN budget = '5to15k' THEN 10000
        ELSE 2500
    END) as estimated_value
FROM leads
WHERE status NOT IN ('won', 'lost')
GROUP BY status;

-- Agent performance view
CREATE VIEW IF NOT EXISTS agent_performance AS
SELECT
    assigned_agent,
    COUNT(*) as total_leads,
    SUM(CASE WHEN status = 'contacted' THEN 1 ELSE 0 END) as contacted,
    SUM(CASE WHEN status = 'qualified' THEN 1 ELSE 0 END) as qualified,
    SUM(CASE WHEN status = 'proposal' THEN 1 ELSE 0 END) as proposals,
    SUM(CASE WHEN status = 'won' THEN 1 ELSE 0 END) as won,
    SUM(CASE WHEN status = 'lost' THEN 1 ELSE 0 END) as lost,
    ROUND(
        CAST(SUM(CASE WHEN status = 'won' THEN 1 ELSE 0 END) AS FLOAT) /
        NULLIF(SUM(CASE WHEN status IN ('won', 'lost') THEN 1 ELSE 0 END), 0) * 100,
        1
    ) as conversion_rate
FROM leads
WHERE assigned_agent IS NOT NULL AND assigned_agent != ''
GROUP BY assigned_agent;

-- =============================================================================
-- SAMPLE DATA (Optional - remove in production)
-- =============================================================================
-- Uncomment to insert sample agents:
-- INSERT INTO agents (name, email, phone) VALUES
--     ('Gio', 'gio@j3construction.com', '555-0101'),
--     ('Marco', 'marco@j3construction.com', '555-0102'),
--     ('Carlos', 'carlos@j3construction.com', '555-0103');

-- Uncomment to insert sample leads:
-- INSERT INTO leads (name, contact, project_type, source, urgency, budget, score, status, assigned_agent, notes) VALUES
--     ('John Smith', '555-1234', 'kitchen', 'google', 'asap', '15to30k', 65, 'new', 'Gio', 'Wants modern design'),
--     ('Maria Garcia', '555-5678', 'full', 'referral', 'soon', 'over30k', 70, 'contacted', 'Marco', 'Large home renovation'),
--     ('Bob Johnson', '555-9012', 'bathroom', 'facebook', 'later', '5to15k', 35, 'new', NULL, 'Master bath update');
