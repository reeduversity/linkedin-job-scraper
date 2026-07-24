from __future__ import annotations

from contextlib import contextmanager
from typing import Iterator
from urllib.parse import urlparse

import psycopg
from psycopg.rows import dict_row

from app.config import settings


class DatabaseError(RuntimeError):
    """Raised when database operations fail."""


def _build_connect_kwargs() -> dict:
    """
    Build psycopg connection kwargs.
    If DATABASE_URL is set (e.g. Neon cloud URL), parse it directly.
    Otherwise fall back to individual POSTGRES_* env vars.
    Neon requires sslmode=require which is included in the URL automatically.
    """
    import os
    database_url = os.getenv("DATABASE_URL", "").strip()

    if database_url:
        # Parse the URL and pass params explicitly so psycopg handles SSL correctly
        parsed = urlparse(database_url)
        kwargs: dict = {
            "host": parsed.hostname,
            "port": parsed.port or 5432,
            "dbname": parsed.path.lstrip("/"),
            "user": parsed.username,
            "password": parsed.password,
        }
        # Pass sslmode from query string if present (Neon uses ?sslmode=require)
        if parsed.query and "sslmode=require" in parsed.query:
            kwargs["sslmode"] = "require"
        elif parsed.query and "sslmode=disable" in parsed.query:
            kwargs["sslmode"] = "disable"
        else:
            # Neon always needs SSL — default to require when using DATABASE_URL
            kwargs["sslmode"] = "require"
        return kwargs

    # Local / individual env vars — no SSL by default
    return {
        "host": settings.postgres_host,
        "port": settings.postgres_port,
        "dbname": settings.postgres_db,
        "user": settings.postgres_user,
        "password": settings.postgres_password,
    }


@contextmanager
def get_connection() -> Iterator[psycopg.Connection]:
    conn: psycopg.Connection | None = None
    try:
        kwargs = _build_connect_kwargs()
        conn = psycopg.connect(**kwargs)
        yield conn
    except psycopg.Error as exc:
        raise DatabaseError(f"Failed to connect to PostgreSQL: {exc}") from exc
    finally:
        if conn is not None:
            conn.close()


def test_connection() -> bool:
    try:
        with get_connection() as conn:
            with conn.cursor() as cursor:
                cursor.execute("SELECT 1")
                return cursor.fetchone() == (1,)
    except Exception:
        return False


def initialize_database() -> None:
    try:
        with get_connection() as conn:
            with conn.cursor() as cursor:
                cursor.execute(
                    "CREATE TABLE IF NOT EXISTS jobs ("
                    "id BIGSERIAL PRIMARY KEY,"
                    "job_title TEXT,"
                    "company_name TEXT,"
                    "company_url TEXT,"
                    "linkedin_job_url TEXT NOT NULL UNIQUE,"
                    "job_id TEXT,"
                    "location TEXT,"
                    "country TEXT,"
                    "workplace_type TEXT,"
                    "employment_type TEXT,"
                    "experience_level TEXT,"
                    "salary TEXT,"
                    "currency TEXT,"
                    "description TEXT,"
                    "job_summary TEXT,"
                    "skills TEXT[],"
                    "industry TEXT,"
                    "benefits TEXT,"
                    "recruiter TEXT,"
                    "recruiter_url TEXT,"
                    "company_logo TEXT,"
                    "company_size TEXT,"
                    "application_url TEXT,"
                    "easy_apply BOOLEAN,"
                    "posted_date TIMESTAMPTZ,"
                    "scraped_timestamp TIMESTAMPTZ NOT NULL DEFAULT now(),"
                    "apify_run_id TEXT,"
                    "raw_json JSONB NOT NULL,"
                    "created_at TIMESTAMPTZ NOT NULL DEFAULT now(),"
                    "updated_at TIMESTAMPTZ NOT NULL DEFAULT now()"
                    ")"
                )
                cursor.execute("ALTER TABLE jobs ADD COLUMN IF NOT EXISTS apify_run_id TEXT")
                cursor.execute("ALTER TABLE jobs ADD COLUMN IF NOT EXISTS source_type TEXT DEFAULT 'JOB_LISTING'")
                cursor.execute("ALTER TABLE jobs ADD COLUMN IF NOT EXISTS post_url TEXT")
                cursor.execute("ALTER TABLE jobs ADD COLUMN IF NOT EXISTS post_text TEXT")
                cursor.execute("ALTER TABLE jobs ADD COLUMN IF NOT EXISTS post_author_name TEXT")
                cursor.execute("ALTER TABLE jobs ADD COLUMN IF NOT EXISTS post_author_profile_url TEXT")
                cursor.execute("ALTER TABLE jobs ADD COLUMN IF NOT EXISTS post_author_role TEXT")
                cursor.execute("ALTER TABLE jobs ADD COLUMN IF NOT EXISTS application_method TEXT")
                cursor.execute("ALTER TABLE jobs ADD COLUMN IF NOT EXISTS application_methods JSONB")
                cursor.execute("ALTER TABLE jobs ADD COLUMN IF NOT EXISTS application_email TEXT")
                cursor.execute("ALTER TABLE jobs ADD COLUMN IF NOT EXISTS application_platform TEXT")
                cursor.execute("ALTER TABLE jobs ADD COLUMN IF NOT EXISTS poster_designation TEXT")
                cursor.execute("ALTER TABLE jobs ADD COLUMN IF NOT EXISTS poster_role_category TEXT")
                cursor.execute("ALTER TABLE jobs ADD COLUMN IF NOT EXISTS hiring_confidence_score DOUBLE PRECISION")
                cursor.execute("ALTER TABLE jobs ADD COLUMN IF NOT EXISTS detection_method TEXT")
                cursor.execute("ALTER TABLE jobs ADD COLUMN IF NOT EXISTS extraction_method TEXT")
                cursor.execute("ALTER TABLE jobs ADD COLUMN IF NOT EXISTS extraction_quality TEXT")
                cursor.execute("ALTER TABLE jobs ADD COLUMN IF NOT EXISTS image_url TEXT")
                cursor.execute("ALTER TABLE jobs ADD COLUMN IF NOT EXISTS image_urls JSONB")
                cursor.execute("ALTER TABLE jobs ADD COLUMN IF NOT EXISTS ocr_text TEXT")
                cursor.execute("ALTER TABLE jobs ADD COLUMN IF NOT EXISTS ocr_confidence DOUBLE PRECISION")
                cursor.execute("ALTER TABLE jobs ADD COLUMN IF NOT EXISTS ocr_processed BOOLEAN DEFAULT FALSE")
                cursor.execute("ALTER TABLE jobs ADD COLUMN IF NOT EXISTS ocr_extraction_status TEXT")
                cursor.execute("ALTER TABLE jobs ADD COLUMN IF NOT EXISTS hashtags JSONB")
                cursor.execute("ALTER TABLE jobs ADD COLUMN IF NOT EXISTS application_emails JSONB")
                cursor.execute("ALTER TABLE jobs ADD COLUMN IF NOT EXISTS application_urls JSONB")
                cursor.execute("ALTER TABLE jobs ADD COLUMN IF NOT EXISTS application_form_url TEXT")
                cursor.execute("ALTER TABLE jobs ADD COLUMN IF NOT EXISTS application_url_type TEXT")
                cursor.execute("ALTER TABLE jobs ALTER COLUMN source_type SET DEFAULT 'LINKEDIN_JOB'")
                cursor.execute("CREATE INDEX IF NOT EXISTS idx_jobs_company_name ON jobs (company_name)")
                cursor.execute("CREATE INDEX IF NOT EXISTS idx_jobs_posted_date ON jobs (posted_date)")
                cursor.execute("CREATE INDEX IF NOT EXISTS idx_jobs_location ON jobs (location)")
                cursor.execute("CREATE INDEX IF NOT EXISTS idx_jobs_job_title ON jobs (job_title)")
                cursor.execute("CREATE INDEX IF NOT EXISTS idx_jobs_linkedin_job_url ON jobs (linkedin_job_url)")
                cursor.execute("CREATE INDEX IF NOT EXISTS idx_jobs_source_type ON jobs (source_type)")
                cursor.execute("CREATE INDEX IF NOT EXISTS idx_jobs_hiring_confidence ON jobs (hiring_confidence_score)")
                conn.commit()
    except psycopg.Error as exc:
        raise DatabaseError(f"Failed to initialize database schema: {exc}") from exc
