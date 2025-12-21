-- SBTi Data Tables for KPI Benchmarking Engine
-- Run this in your Supabase SQL Editor after supabase_setup.sql

-- ================================================
-- SBTi Companies Reference Table
-- ================================================
CREATE TABLE IF NOT EXISTS sbti_companies (
    id SERIAL PRIMARY KEY,
    company_name VARCHAR(255) NOT NULL,
    isin VARCHAR(20),
    lei VARCHAR(30),
    country VARCHAR(100),
    region VARCHAR(100),
    sector VARCHAR(150) NOT NULL,
    industry VARCHAR(200),
    company_status VARCHAR(50), -- Committed, Targets Set, etc.
    target_classification VARCHAR(100),
    near_term_target_year INTEGER,
    net_zero_committed BOOLEAN DEFAULT FALSE,
    net_zero_year INTEGER,
    date_joined DATE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Indexes for efficient peer filtering
CREATE INDEX IF NOT EXISTS idx_sbti_companies_sector ON sbti_companies(sector);
CREATE INDEX IF NOT EXISTS idx_sbti_companies_region ON sbti_companies(region);
CREATE INDEX IF NOT EXISTS idx_sbti_companies_country ON sbti_companies(country);
CREATE INDEX IF NOT EXISTS idx_sbti_companies_status ON sbti_companies(company_status);

-- ================================================
-- SBTi Targets Detail Table
-- ================================================
CREATE TABLE IF NOT EXISTS sbti_targets (
    id SERIAL PRIMARY KEY,
    company_id INTEGER REFERENCES sbti_companies(id) ON DELETE CASCADE,
    target_type VARCHAR(50) NOT NULL, -- Near-term, Long-term, Net-Zero
    scope VARCHAR(50) NOT NULL, -- Scope 1, Scope 2, Scope 1+2, Scope 3
    scope_category VARCHAR(100), -- For Scope 3: Purchased goods, Transportation, etc.
    coverage_percentage FLOAT,
    reduction_percentage FLOAT,
    base_year INTEGER,
    target_year INTEGER,
    ambition_level VARCHAR(50), -- 1.5°C, Well-below 2°C, 2°C
    methodology VARCHAR(150),
    is_validated BOOLEAN DEFAULT FALSE,
    validation_date DATE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Indexes for efficient target filtering
CREATE INDEX IF NOT EXISTS idx_sbti_targets_company ON sbti_targets(company_id);
CREATE INDEX IF NOT EXISTS idx_sbti_targets_scope ON sbti_targets(scope);
CREATE INDEX IF NOT EXISTS idx_sbti_targets_type ON sbti_targets(target_type);
CREATE INDEX IF NOT EXISTS idx_sbti_targets_year ON sbti_targets(target_year);
CREATE INDEX IF NOT EXISTS idx_sbti_targets_ambition ON sbti_targets(ambition_level);

-- ================================================
-- Regulatory Knowledge Base Metadata
-- ================================================
CREATE TABLE IF NOT EXISTS regulatory_documents (
    id SERIAL PRIMARY KEY,
    document_name VARCHAR(255) NOT NULL,
    document_type VARCHAR(100) NOT NULL, -- eu_taxonomy, sllp, glp, csrd, etc.
    version VARCHAR(50),
    effective_date DATE,
    file_path VARCHAR(500),
    is_embedded BOOLEAN DEFAULT FALSE,
    embedding_date TIMESTAMP WITH TIME ZONE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_regulatory_docs_type ON regulatory_documents(document_type);

-- ================================================
-- Borrower Document Types (for validation)
-- ================================================
CREATE TABLE IF NOT EXISTS borrower_document_types (
    id SERIAL PRIMARY KEY,
    type_code VARCHAR(50) NOT NULL UNIQUE,
    type_name VARCHAR(100) NOT NULL,
    description TEXT,
    is_mandatory BOOLEAN DEFAULT FALSE,
    sort_order INTEGER DEFAULT 0
);

-- Pre-populate document types
INSERT INTO borrower_document_types (type_code, type_name, description, is_mandatory, sort_order)
VALUES 
    ('csrd_report', 'CSRD / Non-Financial Reporting Statement', 
     'Mandatory annual ESG report with audited environmental, social, and governance data', true, 1),
    ('spts', 'Sustainability Performance Targets (SPTs)', 
     'Formal document defining the sustainability goals and KPI targets for the loan', true, 2),
    ('spo', 'Second Party Opinion (SPO)', 
     'Independent review from rating agency certifying target ambition', false, 3),
    ('taxonomy_report', 'EU Taxonomy Alignment Report', 
     'Spreadsheet showing percentage of green revenue/CapEx/OpEx', false, 4),
    ('transition_plan', 'Transition Plan', 
     'Strategic roadmap showing how company will achieve targets', false, 5),
    ('ghg_inventory', 'GHG Inventory Report', 
     'Detailed greenhouse gas emissions inventory by scope', false, 6),
    ('verification_report', 'Third-Party Verification Report', 
     'Independent verification/assurance statement for emissions data', false, 7)
ON CONFLICT (type_code) DO NOTHING;

-- ================================================
-- KPI Evaluation Documents (enhanced junction table)
-- ================================================
-- Drop existing if needed to recreate with document_type
DROP TABLE IF EXISTS kpi_evaluation_documents_v2;

CREATE TABLE IF NOT EXISTS kpi_evaluation_documents_v2 (
    id SERIAL PRIMARY KEY,
    evaluation_id INTEGER NOT NULL,
    document_id INTEGER NOT NULL,
    document_type_code VARCHAR(50) REFERENCES borrower_document_types(type_code),
    is_primary BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    UNIQUE(evaluation_id, document_id)
);

CREATE INDEX IF NOT EXISTS idx_eval_docs_v2_eval ON kpi_evaluation_documents_v2(evaluation_id);
CREATE INDEX IF NOT EXISTS idx_eval_docs_v2_type ON kpi_evaluation_documents_v2(document_type_code);

-- ================================================
-- Function to select peer companies
-- ================================================
CREATE OR REPLACE FUNCTION select_sbti_peers(
    p_sector VARCHAR(150),
    p_scope VARCHAR(50),
    p_region VARCHAR(100) DEFAULT NULL,
    p_target_year INTEGER DEFAULT NULL,
    p_year_tolerance INTEGER DEFAULT 3
)
RETURNS TABLE (
    company_id INTEGER,
    company_name VARCHAR(255),
    sector VARCHAR(150),
    region VARCHAR(100),
    target_type VARCHAR(50),
    scope VARCHAR(50),
    reduction_percentage FLOAT,
    base_year INTEGER,
    target_year INTEGER,
    ambition_level VARCHAR(50)
)
LANGUAGE plpgsql
AS $$
BEGIN
    RETURN QUERY
    SELECT 
        c.id as company_id,
        c.company_name,
        c.sector,
        c.region,
        t.target_type,
        t.scope,
        t.reduction_percentage,
        t.base_year,
        t.target_year,
        t.ambition_level
    FROM sbti_companies c
    INNER JOIN sbti_targets t ON c.id = t.company_id
    WHERE 
        c.sector = p_sector
        AND t.scope = p_scope
        AND t.reduction_percentage IS NOT NULL
        AND (p_region IS NULL OR c.region = p_region)
        AND (p_target_year IS NULL OR 
             ABS(t.target_year - p_target_year) <= p_year_tolerance)
    ORDER BY t.reduction_percentage DESC;
END;
$$;

-- ================================================
-- Function to compute peer percentiles
-- ================================================
CREATE OR REPLACE FUNCTION compute_peer_percentiles(
    p_sector VARCHAR(150),
    p_scope VARCHAR(50),
    p_region VARCHAR(100) DEFAULT NULL
)
RETURNS TABLE (
    peer_count INTEGER,
    min_reduction FLOAT,
    p25_reduction FLOAT,
    median_reduction FLOAT,
    p75_reduction FLOAT,
    max_reduction FLOAT,
    mean_reduction FLOAT,
    stddev_reduction FLOAT
)
LANGUAGE plpgsql
AS $$
BEGIN
    RETURN QUERY
    WITH peer_data AS (
        SELECT t.reduction_percentage
        FROM sbti_companies c
        INNER JOIN sbti_targets t ON c.id = t.company_id
        WHERE 
            c.sector = p_sector
            AND t.scope = p_scope
            AND t.reduction_percentage IS NOT NULL
            AND (p_region IS NULL OR c.region = p_region)
    )
    SELECT 
        COUNT(*)::INTEGER as peer_count,
        MIN(reduction_percentage) as min_reduction,
        PERCENTILE_CONT(0.25) WITHIN GROUP (ORDER BY reduction_percentage) as p25_reduction,
        PERCENTILE_CONT(0.50) WITHIN GROUP (ORDER BY reduction_percentage) as median_reduction,
        PERCENTILE_CONT(0.75) WITHIN GROUP (ORDER BY reduction_percentage) as p75_reduction,
        MAX(reduction_percentage) as max_reduction,
        AVG(reduction_percentage) as mean_reduction,
        STDDEV(reduction_percentage) as stddev_reduction
    FROM peer_data;
END;
$$;

-- Grant permissions
GRANT SELECT, INSERT, UPDATE, DELETE ON sbti_companies TO authenticated;
GRANT SELECT, INSERT, UPDATE, DELETE ON sbti_targets TO authenticated;
GRANT SELECT ON regulatory_documents TO authenticated;
GRANT SELECT ON borrower_document_types TO authenticated;
GRANT SELECT, INSERT, DELETE ON kpi_evaluation_documents_v2 TO authenticated;
GRANT EXECUTE ON FUNCTION select_sbti_peers TO authenticated;
GRANT EXECUTE ON FUNCTION compute_peer_percentiles TO authenticated;

-- Also for anon during development
GRANT SELECT, INSERT, UPDATE, DELETE ON sbti_companies TO anon;
GRANT SELECT, INSERT, UPDATE, DELETE ON sbti_targets TO anon;
GRANT SELECT ON regulatory_documents TO anon;
GRANT SELECT ON borrower_document_types TO anon;
GRANT SELECT, INSERT, DELETE ON kpi_evaluation_documents_v2 TO anon;
GRANT EXECUTE ON FUNCTION select_sbti_peers TO anon;
GRANT EXECUTE ON FUNCTION compute_peer_percentiles TO anon;

-- Verify setup
SELECT 'SBTi tables created successfully' as status;
