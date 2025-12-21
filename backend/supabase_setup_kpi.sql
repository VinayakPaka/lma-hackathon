-- KPI Evaluation Tables

-- Main evaluation table
CREATE TABLE IF NOT EXISTS kpi_evaluations (
    id SERIAL PRIMARY KEY,
    loan_reference_id VARCHAR(100) NOT NULL,
    company_name VARCHAR(255) NOT NULL,
    industry_sector VARCHAR(100) NOT NULL,
    region VARCHAR(100) NOT NULL,
    metric VARCHAR(100) NOT NULL,
    target_value FLOAT NOT NULL,
    target_unit VARCHAR(50) NOT NULL,
    timeline_start_year INTEGER NOT NULL,
    timeline_end_year INTEGER NOT NULL,
    baseline_value FLOAT,
    baseline_unit VARCHAR(50),
    baseline_year INTEGER,
    baseline_verification VARCHAR(50), -- audited, third_party_verified, self_reported, unknown
    
    -- Optional fields
    company_size_proxy VARCHAR(100),
    emissions_scope VARCHAR(50),
    methodology VARCHAR(255),
    capex_budget VARCHAR(100),
    plan_description TEXT,
    csrd_reporting_status VARCHAR(50),
    
    -- Evaluation status and results
    status VARCHAR(50) DEFAULT 'draft', -- draft, processing, completed, failed
    result_summary TEXT, -- Short summary
    assessment_grade VARCHAR(20), -- WEAK, MODERATE, AMBITIOUS
    success_probability FLOAT,
    needs_review BOOLEAN DEFAULT FALSE,
    banker_decision VARCHAR(50), -- PENDING, ACCEPT_AS_IS, NEGOTIATE, REJECT, OVERRIDE_AI
    banker_override_reason TEXT,
    
    created_by_user_id INTEGER,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS ix_kpi_evaluations_company_name ON kpi_evaluations(company_name);
CREATE INDEX IF NOT EXISTS ix_kpi_evaluations_status ON kpi_evaluations(status);

-- Junction table for documents attached to evaluations
CREATE TABLE IF NOT EXISTS kpi_evaluation_documents (
    evaluation_id INTEGER NOT NULL REFERENCES kpi_evaluations(id) ON DELETE CASCADE,
    document_id INTEGER NOT NULL REFERENCES documents(id) ON DELETE CASCADE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    PRIMARY KEY (evaluation_id, document_id)
);

-- Store full detailed JSON result to avoid massive columns in main table
CREATE TABLE IF NOT EXISTS kpi_evaluation_results (
    id SERIAL PRIMARY KEY,
    evaluation_id INTEGER NOT NULL REFERENCES kpi_evaluations(id) ON DELETE CASCADE,
    result_json JSONB NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Audit logs for AI operations
CREATE TABLE IF NOT EXISTS ai_audit_logs (
    id SERIAL PRIMARY KEY,
    evaluation_id INTEGER REFERENCES kpi_evaluations(id) ON DELETE SET NULL,
    action_type VARCHAR(50) NOT NULL, -- EXTRACT, BENCHMARK, SCORE, LLM_GENERATE
    model_provider VARCHAR(50), -- Voyage, Perplexity, OpenAI, etc.
    input_snapshot JSONB,
    output_snapshot JSONB,
    latency_ms INTEGER,
    timestamp TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS ix_ai_audit_logs_evaluation_id ON ai_audit_logs(evaluation_id);
