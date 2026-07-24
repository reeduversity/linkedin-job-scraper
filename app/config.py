from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path

from dotenv import load_dotenv


DOTENV_PATH = Path(".env")
if DOTENV_PATH.exists():
    load_dotenv(dotenv_path=DOTENV_PATH)
else:
    load_dotenv()


@dataclass(frozen=True)
class Settings:
    apify_api_token: str = os.getenv("APIFY_TOKEN", "")
    apify_actor_id: str = os.getenv("APIFY_ACTOR_ID", "apify/linkedin-jobs-scraper")
    apify_post_actor_id: str = os.getenv("APIFY_POST_ACTOR_ID", "datadoping/linkedin-posts-search-scraper")
    post_scraper_enabled: bool = os.getenv("POST_SCRAPER_ENABLED", "True").strip().lower() in {"true", "1", "yes"}
    postgres_host: str = os.getenv("POSTGRES_HOST", "localhost")
    postgres_port: int = int(os.getenv("POSTGRES_PORT", "5432"))
    postgres_db: str = os.getenv("POSTGRES_DB", "linkedin_jobs")
    postgres_user: str = os.getenv("POSTGRES_USER", "postgres")
    postgres_password: str = os.getenv("POSTGRES_PASSWORD", "postgres")
    csv_export_path: str = os.getenv("CSV_EXPORT_PATH", "data/csv/jobs.csv")
    excel_export_path: str = os.getenv("EXCEL_EXPORT_PATH", "data/excel/jobs.xlsx")
    log_level: str = os.getenv("LOG_LEVEL", "INFO")
    log_path: str = os.getenv("LOG_PATH", "logs/app.log")
    max_results: int = int(os.getenv("MAX_RESULTS", "100"))
    schedule_interval: int = int(os.getenv("SCHEDULE_INTERVAL", "60"))
    scraper_interval_minutes: int = int(os.getenv("SCRAPER_INTERVAL_MINUTES", os.getenv("SCHEDULE_INTERVAL", "60")))
    scraper_enabled: bool = os.getenv("SCRAPER_ENABLED", "True").strip().lower() in {"true", "1", "yes"}
    scraper_max_instances: int = int(os.getenv("SCRAPER_MAX_INSTANCES", "1"))
    scraper_coalesce: bool = os.getenv("SCRAPER_COALESCE", "True").strip().lower() in {"true", "1", "yes"}
    scraper_misfire_grace_time: int = int(os.getenv("SCRAPER_MISFIRE_GRACE_TIME", "60"))


settings = Settings()
