from __future__ import annotations

import os
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from apify_client import ApifyClient
import psycopg
from psycopg import sql
from dotenv import load_dotenv


class ConfigurationError(RuntimeError):
    """Raised when configuration validation fails."""


REQUIRED_ENV_VARS = [
    "APIFY_TOKEN",
    "APIFY_ACTOR_ID",
    "POSTGRES_HOST",
    "POSTGRES_PORT",
    "POSTGRES_DB",
    "POSTGRES_USER",
    "POSTGRES_PASSWORD",
    "CSV_EXPORT_PATH",
    "EXCEL_EXPORT_PATH",
    "LOG_LEVEL",
    "LOG_PATH",
    "MAX_RESULTS",
    "SCHEDULE_INTERVAL",
]


@dataclass(frozen=True)
class Config:
    apify_token: str
    apify_actor_id: str
    postgres_host: str
    postgres_port: int
    postgres_db: str
    postgres_user: str
    postgres_password: str
    csv_export_path: Path
    excel_export_path: Path
    log_level: str
    log_path: Path
    max_results: int
    schedule_interval: int


def mask_secret(value: str, visible: int = 6) -> str:
    if not value:
        return ""
    if len(value) <= visible:
        return "*" * len(value)
    return f"{value[:visible]}{'*' * (len(value) - visible)}"


def load_environment() -> None:
    env_path = Path(".env")
    if env_path.exists():
        load_dotenv(dotenv_path=env_path)
    else:
        load_dotenv()


def validate_int(name: str, value: str, minimum: int = 1) -> int:
    try:
        parsed = int(value)
    except ValueError as exc:
        raise ValueError(f"{name} must be an integer, got '{value}'") from exc
    if parsed < minimum:
        raise ValueError(f"{name} must be >= {minimum}, got {parsed}")
    return parsed


def validate_required_env() -> dict[str, str]:
    values: dict[str, str] = {}
    missing = []
    for key in REQUIRED_ENV_VARS:
        value = os.getenv(key, "").strip()
        if not value:
            missing.append(key)
        values[key] = value
    if missing:
        raise EnvironmentError(f"Missing required environment variables: {', '.join(missing)}")
    return values


def validate_paths(csv_path: Path, excel_path: Path, log_path: Path) -> None:
    for path in (csv_path, excel_path, log_path):
        if path.is_dir():
            raise ValueError(f"Configured path must be a file path, not a directory: {path}")

    if csv_path.suffix.lower() != ".csv":
        raise ValueError("CSV_EXPORT_PATH must be a .csv file")
    if excel_path.suffix.lower() not in {".xlsx", ".xls"}:
        raise ValueError("EXCEL_EXPORT_PATH must be an .xlsx or .xls file")
    if log_path.suffix.lower() not in {".log", ".txt"}:
        raise ValueError("LOG_PATH must be a .log or .txt file")


def verify_apify_token(token: str) -> None:
    client = ApifyClient(token)
    user = client.user().get()
    if user is None:
        raise ConnectionError("Apify authentication failed: no user data returned")


def create_database_if_missing(host: str, port: int, dbname: str, user: str, password: str) -> None:
    connection_string = f"dbname=postgres user={user} password={password} host={host} port={port}"
    with psycopg.connect(connection_string, autocommit=True) as conn:
        with conn.cursor() as cursor:
            cursor.execute("SELECT 1 FROM pg_database WHERE datname = %s", (dbname,))
            if cursor.fetchone() is None:
                cursor.execute(f"CREATE DATABASE {psycopg.sql.Identifier(dbname).as_string(conn)}")
                print(f"Database created: {dbname}")
            else:
                print(f"Database exists: {dbname}")


def verify_postgres_connection(host: str, port: int, dbname: str, user: str, password: str) -> None:
    connection_string = f"dbname={dbname} user={user} password={password} host={host} port={port}"
    with psycopg.connect(connection_string) as conn:
        with conn.cursor() as cursor:
            cursor.execute("SELECT 1")
            result = cursor.fetchone()
            if result != (1,):
                raise ConnectionError("Unexpected PostgreSQL test query result")


def create_directories() -> None:
    directories = [Path("data"), Path("data/csv"), Path("data/excel"), Path("logs")]
    for directory in directories:
        if not directory.exists():
            directory.mkdir(parents=True, exist_ok=True)
            print(f"Created directory: {directory}")
        else:
            print(f"Directory exists: {directory}")


def build_config(values: dict[str, str]) -> Config:
    csv_export_path = Path(values["CSV_EXPORT_PATH"])
    excel_export_path = Path(values["EXCEL_EXPORT_PATH"])
    log_path = Path(values["LOG_PATH"])
    validate_paths(csv_export_path, excel_export_path, log_path)

    return Config(
        apify_token=values["APIFY_TOKEN"],
        apify_actor_id=values["APIFY_ACTOR_ID"],
        postgres_host=values["POSTGRES_HOST"],
        postgres_port=validate_int("POSTGRES_PORT", values["POSTGRES_PORT"]),
        postgres_db=values["POSTGRES_DB"],
        postgres_user=values["POSTGRES_USER"],
        postgres_password=values["POSTGRES_PASSWORD"],
        csv_export_path=csv_export_path,
        excel_export_path=excel_export_path,
        log_level=values["LOG_LEVEL"],
        log_path=log_path,
        max_results=validate_int("MAX_RESULTS", values["MAX_RESULTS"], minimum=1),
        schedule_interval=validate_int("SCHEDULE_INTERVAL", values["SCHEDULE_INTERVAL"], minimum=1),
    )


def print_config_summary(config: Config) -> None:
    print("Configuration summary:")
    print(f"  APIFY_TOKEN={mask_secret(config.apify_token)}")
    print(f"  APIFY_ACTOR_ID={config.apify_actor_id}")
    print(f"  POSTGRES_HOST={config.postgres_host}")
    print(f"  POSTGRES_PORT={config.postgres_port}")
    print(f"  POSTGRES_DB={config.postgres_db}")
    print(f"  POSTGRES_USER={config.postgres_user}")
    print(f"  POSTGRES_PASSWORD={mask_secret(config.postgres_password)}")
    print(f"  CSV_EXPORT_PATH={config.csv_export_path}")
    print(f"  EXCEL_EXPORT_PATH={config.excel_export_path}")
    print(f"  LOG_LEVEL={config.log_level}")
    print(f"  LOG_PATH={config.log_path}")
    print(f"  MAX_RESULTS={config.max_results}")
    print(f"  SCHEDULE_INTERVAL={config.schedule_interval}")


def main() -> int:
    try:
        load_environment()
        values = validate_required_env()
        config = build_config(values)
        print_config_summary(config)
        verify_apify_token(config.apify_token)
        create_directories()
        create_database_if_missing(
            config.postgres_host,
            config.postgres_port,
            config.postgres_db,
            config.postgres_user,
            config.postgres_password,
        )
        verify_postgres_connection(
            config.postgres_host,
            config.postgres_port,
            config.postgres_db,
            config.postgres_user,
            config.postgres_password,
        )
        print("\nEnvironment configuration validated successfully.")
        return 0
    except Exception as exc:
        print(f"Configuration validation error: {exc}")
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
