from __future__ import annotations

from contextlib import contextmanager
from typing import Iterator

import psycopg
from psycopg.rows import dict_row

from app.config import settings


class DatabaseError(RuntimeError):
    """Raised when database operations fail."""


@contextmanager
def get_connection() -> Iterator[psycopg.Connection]:
    conn: psycopg.Connection | None = None
    try:
        conn = psycopg.connect(
            host=settings.postgres_host,
            port=settings.postgres_port,
            dbname=settings.postgres_db,
            user=settings.postgres_user,
            password=settings.postgres_password,
        )
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
                    "raw_json JSONB NOT NULL,"
                    "created_at TIMESTAMPTZ NOT NULL DEFAULT now(),"
                    "updated_at TIMESTAMPTZ NOT NULL DEFAULT now()"
                    ")"
                )
                cursor.execute("CREATE INDEX IF NOT EXISTS idx_jobs_company_name ON jobs (company_name)")
                cursor.execute("CREATE INDEX IF NOT EXISTS idx_jobs_posted_date ON jobs (posted_date)")
                cursor.execute("CREATE INDEX IF NOT EXISTS idx_jobs_location ON jobs (location)")
                cursor.execute("CREATE INDEX IF NOT EXISTS idx_jobs_job_title ON jobs (job_title)")
                cursor.execute("CREATE INDEX IF NOT EXISTS idx_jobs_linkedin_job_url ON jobs (linkedin_job_url)")
                conn.commit()
    except psycopg.Error as exc:
        raise DatabaseError(f"Failed to initialize database schema: {exc}") from exc
