-- Migration 001: Create datasets table
CREATE TABLE IF NOT EXISTS datasets (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name TEXT NOT NULL,
    description TEXT,
    source TEXT,
    status TEXT NOT NULL DEFAULT 'registered',
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    CONSTRAINT chk_datasets_status CHECK (status IN ('registered', 'processing', 'ready', 'failed'))
);

CREATE INDEX IF NOT EXISTS idx_datasets_status ON datasets(status);
