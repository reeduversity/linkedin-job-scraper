-- Production-ready PostgreSQL schema for the LinkedIn job collection pipeline.
-- This script is safe to run repeatedly.

CREATE TABLE IF NOT EXISTS jobs (
    id BIGSERIAL PRIMARY KEY,
    job_title TEXT,
    company_name TEXT,
    company_url TEXT,
    linkedin_job_url TEXT NOT NULL UNIQUE,
    job_id TEXT,
    location TEXT,
    country TEXT,
    workplace_type TEXT,
    employment_type TEXT,
    experience_level TEXT,
    salary TEXT,
    currency TEXT,
    description TEXT,
    job_summary TEXT,
    skills TEXT[],
    industry TEXT,
    benefits TEXT,
    recruiter TEXT,
    recruiter_url TEXT,
    company_logo TEXT,
    company_size TEXT,
    application_url TEXT,
    easy_apply BOOLEAN,
    posted_date TIMESTAMPTZ,
    scraped_timestamp TIMESTAMPTZ NOT NULL DEFAULT now(),
    raw_json JSONB NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    -- HIRING_POST specific columns
    source_type TEXT DEFAULT 'LINKEDIN_JOB',
    post_url TEXT,
    post_text TEXT,
    post_author_name TEXT,
    post_author_profile_url TEXT,
    post_author_role TEXT,
    poster_designation TEXT,
    poster_role_category TEXT,
    hiring_confidence_score DOUBLE PRECISION,
    detection_method TEXT,
    extraction_method TEXT,
    extraction_quality TEXT,
    image_url TEXT,
    image_urls JSONB,
    ocr_text TEXT,
    ocr_confidence DOUBLE PRECISION,
    ocr_processed BOOLEAN DEFAULT FALSE,
    ocr_extraction_status TEXT,
    hashtags JSONB,
    application_method TEXT,
    application_methods JSONB,
    application_email TEXT,
    application_emails JSONB,
    application_platform TEXT,
    application_urls JSONB,
    application_form_url TEXT,
    application_url_type TEXT,
    apify_run_id TEXT
);

CREATE INDEX IF NOT EXISTS idx_jobs_company_name ON jobs (company_name);
CREATE INDEX IF NOT EXISTS idx_jobs_posted_date ON jobs (posted_date);
CREATE INDEX IF NOT EXISTS idx_jobs_location ON jobs (location);
CREATE INDEX IF NOT EXISTS idx_jobs_job_title ON jobs (job_title);
CREATE INDEX IF NOT EXISTS idx_jobs_linkedin_job_url ON jobs (linkedin_job_url);
CREATE INDEX IF NOT EXISTS idx_jobs_source_type ON jobs (source_type);
CREATE INDEX IF NOT EXISTS idx_jobs_hiring_confidence ON jobs (hiring_confidence_score);

CREATE OR REPLACE FUNCTION set_updated_at()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = now();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

DROP TRIGGER IF EXISTS trg_jobs_updated_at ON jobs;
CREATE TRIGGER trg_jobs_updated_at
BEFORE UPDATE ON jobs
FOR EACH ROW
EXECUTE FUNCTION set_updated_at();

