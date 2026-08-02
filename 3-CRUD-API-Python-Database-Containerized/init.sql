CREATE TABLE IF NOT EXISTS task (
    id SERIAL PRIMARY KEY,
    title VARCHAR(255) NOT NULL,
    done BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Index for optimized search queries (Stretch goal)
CREATE INDEX IF NOT EXISTS idx_task_title ON task (title);

-- Initial seed data
INSERT INTO task (title, done) VALUES 
('Setup repository', true),
('Build Stage 1 endpoints', true),
('Implement Stage 2 endpoints', false)
ON CONFLICT DO NOTHING;