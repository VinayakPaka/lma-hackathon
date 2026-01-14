-- Report Chat tables (report-scoped banker Q&A)

CREATE TABLE IF NOT EXISTS report_chat_sessions (
    id SERIAL PRIMARY KEY,
    evaluation_id INTEGER NOT NULL REFERENCES kpi_evaluations(id) ON DELETE CASCADE,
    user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    title VARCHAR(255),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS ix_report_chat_sessions_evaluation_id ON report_chat_sessions(evaluation_id);
CREATE INDEX IF NOT EXISTS ix_report_chat_sessions_user_id ON report_chat_sessions(user_id);

CREATE TABLE IF NOT EXISTS report_chat_messages (
    id SERIAL PRIMARY KEY,
    session_id INTEGER NOT NULL REFERENCES report_chat_sessions(id) ON DELETE CASCADE,
    role VARCHAR(20) NOT NULL,
    content TEXT NOT NULL,
    citations_json TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS ix_report_chat_messages_session_id ON report_chat_messages(session_id);
