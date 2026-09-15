#!/bin/bash
set -e

DB_URL=${1:-postgresql://admin:secure_password@localhost:5432/metadata}

echo "Setting up database at $DB_URL..."

psql $DB_URL << EOF
-- Model registry
CREATE TABLE IF NOT EXISTS model_registry (
    id VARCHAR(100) PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    version VARCHAR(50) NOT NULL,
    path VARCHAR(500) NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    metadata JSONB
);

-- Query history
CREATE TABLE IF NOT EXISTS query_history (
    id SERIAL PRIMARY KEY,
    query_id VARCHAR(100) NOT NULL,
    user_query TEXT NOT NULL,
    sql_query TEXT NOT NULL,
    results JSONB,
    metadata JSONB,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Training jobs
CREATE TABLE IF NOT EXISTS training_jobs (
    id SERIAL PRIMARY KEY,
    job_id VARCHAR(100) NOT NULL,
    status VARCHAR(50) NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    completed_at TIMESTAMP,
    metadata JSONB
);

-- Create indexes
CREATE INDEX IF NOT EXISTS idx_query_history_query_id ON query_history(query_id);
CREATE INDEX IF NOT EXISTS idx_query_history_created_at ON query_history(created_at);
CREATE INDEX IF NOT EXISTS idx_training_jobs_job_id ON training_jobs(job_id);

-- Sample data
INSERT INTO model_registry (id, name, version, path, metadata) 
VALUES ('qwen_enterprise_v1', 'Qwen Enterprise Model', '1.0.0', '/app/models/registry/models/qwen_enterprise_v1/model.gguf', '{"base": "Qwen/Qwen2.5-Coder-7B"}')
ON CONFLICT (id) DO NOTHING;
EOF

echo -e "\033[32mDatabase setup complete!\033[0m"