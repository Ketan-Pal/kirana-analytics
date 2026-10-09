-- Migration V4: Festival Calendar Table for Official Indian Regional Gazette
-- Backed by ADR-001 (https://calendar-api-d7a8.onrender.com/v1/holidays?country=IN&region=UP&year={YEAR})

CREATE TABLE IF NOT EXISTS festival_calendar (
    id SERIAL PRIMARY KEY,
    festival_name VARCHAR(120) NOT NULL,
    calendar_year INT NOT NULL,
    festival_date DATE NOT NULL,
    prep_lead_days INT DEFAULT 14,
    surge_categories JSONB DEFAULT '[]'::jsonb,
    surge_items JSONB DEFAULT '[]'::jsonb,
    source VARCHAR(100) DEFAULT 'india.gov.in',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT uq_festival_year UNIQUE (festival_name, calendar_year)
);

CREATE INDEX IF NOT EXISTS idx_festival_date ON festival_calendar (festival_date);
CREATE INDEX IF NOT EXISTS idx_festival_year ON festival_calendar (calendar_year);
