-- Model registry table
CREATE TABLE IF NOT EXISTS model_registry (
    id VARCHAR(100) PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    version VARCHAR(50) NOT NULL,
    path VARCHAR(500) NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    metadata JSONB,
    status VARCHAR(50) DEFAULT 'active'
);

-- Query history table
CREATE TABLE IF NOT EXISTS query_history (
    id SERIAL PRIMARY KEY,
    query_id VARCHAR(100) NOT NULL UNIQUE,
    user_query TEXT NOT NULL,
    sql_query TEXT NOT NULL,
    results JSONB,
    intent JSONB,
    metadata JSONB,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    execution_time_ms INTEGER,
    row_count INTEGER,
    status VARCHAR(50) DEFAULT 'success'
);

-- Training jobs table
CREATE TABLE IF NOT EXISTS training_jobs (
    id SERIAL PRIMARY KEY,
    job_id VARCHAR(100) NOT NULL UNIQUE,
    status VARCHAR(50) NOT NULL,
    started_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    completed_at TIMESTAMP,
    metadata JSONB,
    error_message TEXT,
    model_id VARCHAR(100)
);

-- Schema cache table
CREATE TABLE IF NOT EXISTS schema_cache (
    id SERIAL PRIMARY KEY,
    schema_hash VARCHAR(64) NOT NULL,
    schema_data JSONB NOT NULL,
    extracted_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    database_url VARCHAR(500)
);

-- Create indexes
CREATE INDEX IF NOT EXISTS idx_query_history_query_id ON query_history(query_id);
CREATE INDEX IF NOT EXISTS idx_query_history_created_at ON query_history(created_at);
CREATE INDEX IF NOT EXISTS idx_training_jobs_job_id ON training_jobs(job_id);
CREATE INDEX IF NOT EXISTS idx_training_jobs_status ON training_jobs(status);
CREATE INDEX IF NOT EXISTS idx_schema_cache_hash ON schema_cache(schema_hash);

-- Insert default model record
INSERT INTO model_registry (id, name, version, path, metadata, status)
VALUES (
    'qwen_enterprise_v1',
    'Qwen Enterprise Model',
    '1.0.0',
    '/app/models/registry/models/qwen_enterprise_v1/model.gguf',
    '{"base_model": "Qwen/Qwen2.5-Coder-7B", "fine_tuned_at": "2026-01-01", "dataset_version": "1.0"}',
    'active'
) ON CONFLICT (id) DO NOTHING;

-- Create a view for query statistics
CREATE OR REPLACE VIEW query_stats AS
SELECT 
    DATE(created_at) as date,
    COUNT(*) as total_queries,
    AVG(execution_time_ms) as avg_execution_time,
    SUM(row_count) as total_rows
FROM query_history
WHERE status = 'success'
GROUP BY DATE(created_at)
ORDER BY date DESC;

-- Grant permissions
GRANT SELECT, INSERT, UPDATE ON ALL TABLES IN SCHEMA public TO admin;
GRANT USAGE ON ALL SEQUENCES IN SCHEMA public TO admin;