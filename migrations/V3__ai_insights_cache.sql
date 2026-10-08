-- V3__ai_insights_cache.sql
-- Flyway DDL Migration: AI Insights Cache Table

CREATE TABLE IF NOT EXISTS ai_insights_cache (
    id SERIAL PRIMARY KEY,
    cache_key VARCHAR(100) UNIQUE NOT NULL DEFAULT 'latest_enrichment',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    insights_json JSONB NOT NULL,
    model_used VARCHAR(50) DEFAULT 'gemini-2.5-flash'
);

CREATE INDEX IF NOT EXISTS idx_ai_insights_cache_key ON ai_insights_cache(cache_key);
