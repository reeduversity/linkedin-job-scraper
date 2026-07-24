#!/usr/bin/env python3
"""Main application orchestrator for the LinkedIn Job Scraper.

Coordinates configuration validation, database initialization, job collection
via Apify, validation, deduplication, database persistence, and prints
a detailed production-quality execution summary.
"""

from __future__ import annotations

import argparse
import sys
import threading
import time
from datetime import datetime, timezone
from typing import Any

import psycopg

from app import config_validator
from app.apify_client import (
    ApifyAuthenticationError,
    ApifyConfigurationError,
    ApifyRuntimeError,
    ApifyTimeoutError,
)
from app.config_validator import ConfigurationError
from app.config import settings
from app.database import DatabaseError, initialize_database
from app.models import JobSearchRequest
from app.repository import JobRepository
from app.scraper import JobScraper
from app.validation import ValidationError


def map_days_to_date_posted(days: str | int | None) -> str | None:
    """Map a numeric or textual days indicator to the Apify datePosted format.

    Args:
        days: Days indicator (e.g., "1", 3, "week").

    Returns:
        The mapped datePosted string identifier, or the original value.
    """
    if days is None:
        return None
    val = str(days).strip().lower()
    if val in {"1", "today", "day"}:
        return "today"
    if val in {"3", "3days"}:
        return "3days"
    if val in {"7", "week", "7days"}:
        return "week"
    if val in {"30", "month", "30days"}:
        return "month"
    return val


def parse_arguments() -> argparse.Namespace:
    """Parse command line arguments for the job collection run.

    Returns:
        The parsed command-line arguments.
    """
    parser = argparse.ArgumentParser(
        description="LinkedIn Job Collection System Orchestrator.",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    parser.add_argument(
        "--keywords",
        type=str,
        help="Search query keywords (e.g. 'python')",
    )
    parser.add_argument(
        "--location",
        type=str,
        help="Search geographic location (e.g. 'Remote')",
    )
    parser.add_argument(
        "--limit",
        type=int,
        help="Maximum number of job listings to retrieve",
    )
    parser.add_argument(
        "--remote",
        action="store_true",
        default=None,
        help="Filter for remote jobs",
    )
    parser.add_argument(
        "--hybrid",
        action="store_true",
        default=None,
        help="Filter for hybrid jobs",
    )
    parser.add_argument(
        "--onsite",
        action="store_true",
        default=None,
        help="Filter for on-site jobs",
    )
    parser.add_argument(
        "--days",
        type=str,
        help="Age of jobs to fetch (1=today, 3=3days, 7=week, 30=month)",
    )
    parser.add_argument(
        "--experience",
        type=str,
        help="Experience level filter (e.g. 'Entry Level')",
    )
    parser.add_argument(
        "--company",
        type=str,
        help="Company name filter to search for",
    )
    parser.add_argument(
        "--schedule",
        action="store_true",
        help="Start the automated scheduler to run the pipeline at configured intervals",
    )
    parser.add_argument(
        "--interval",
        type=int,
        help="Execution interval in minutes for the scheduler (overrides configuration)",
    )
    parser.add_argument(
        "--run-once",
        action="store_true",
        help="Run the pipeline once and exit (default behavior)",
    )
    parser.add_argument(
        "--export",
        choices=["csv", "excel", "json"],
        help="Export jobs from PostgreSQL database to selected format",
    )
    parser.add_argument(
        "--output",
        type=str,
        help="Output file path for the export",
    )
    parser.add_argument(
        "--stats",
        action="store_true",
        help="Print job collection database statistics",
    )
    parser.add_argument(
        "--version",
        action="version",
        version="LinkedIn Job Scraper 1.0.0",
        help="Show program version and exit",
    )
    return parser.parse_args()


def print_summary(
    start_time: datetime,
    end_time: datetime,
    total_fetched: int,
    total_validated: int,
    duplicate_removed: int,
    jobs_saved: int,
    jobs_updated: int,
    db_status: str,
    apify_status: str,
    exit_status: str,
    exit_code: int,
) -> None:
    """Print a production-quality execution summary to the standard output.

    Args:
        start_time: Start timestamp of execution.
        end_time: End timestamp of execution.
        total_fetched: Raw job count fetched.
        total_validated: Validated job count.
        duplicate_removed: Duplicate job count removed.
        jobs_saved: Newly saved job count in database.
        jobs_updated: Updated job count in database.
        db_status: Final status of the database connection.
        apify_status: Final status of the Apify verification.
        exit_status: Descriptive exit state.
        exit_code: The exit status integer code.
    """
    duration = (end_time - start_time).total_seconds()
    invalid_jobs = max(0, total_fetched - total_validated)
    failed_jobs = invalid_jobs  # validation/parsing failures

    print("\n" + "=" * 55)
    print("           LINKEDIN JOB COLLECTION RUN SUMMARY")
    print("=" * 55)
    print(f"Start Time:             {start_time.strftime('%Y-%m-%d %H:%M:%S UTC')}")
    print(f"End Time:               {end_time.strftime('%Y-%m-%d %H:%M:%S UTC')}")
    print(f"Total Execution Time:   {duration:.2f} seconds")
    print("-" * 55)
    print(f"Jobs Fetched:           {total_fetched}")
    print(f"Jobs Validated:         {total_validated}")
    print(f"Invalid Jobs:           {invalid_jobs}")
    print(f"Duplicate Jobs Removed: {duplicate_removed}")
    print(f"Jobs Saved:             {jobs_saved}")
    print(f"Jobs Updated:           {jobs_updated}")
    print(f"Failed Jobs:            {failed_jobs}")
    print("-" * 55)
    print(f"Database Status:        {db_status}")
    print(f"Apify Status:           {apify_status}")
    print(f"Exit Status:            {exit_status}")
    print("=" * 55 + "\n")


def run_pipeline(args: argparse.Namespace) -> tuple[int, dict[str, Any]]:
    """Run the main scraper pipeline orchestration flow.

    Args:
        args: The parsed command line arguments.

    Returns:
        A tuple of (exit_code, metrics).
    """
    start_time = datetime.now(timezone.utc)

    # Initialize execution metrics
    total_fetched = 0
    total_validated = 0
    duplicate_removed = 0
    jobs_saved = 0
    jobs_updated = 0
    db_status = "Pending"
    apify_status = "Pending"

    exit_code = 0
    exit_status = "Success"

    try:
        # Step 1: Validate configuration
        try:
            config_validator.load_environment()
            env_values = config_validator.validate_required_env()
            config = config_validator.build_config(env_values)
        except (EnvironmentError, ValueError) as exc:
            raise ConfigurationError(f"Configuration check failed: {exc}")

        # Verify Apify connectivity
        try:
            config_validator.verify_apify_token(config.apify_token)
            apify_status = "Verified"
        except Exception as exc:
            apify_status = "Failed"
            raise ApifyAuthenticationError(f"Apify token verification failed: {exc}")

        # Verify Database directories and PostgreSQL connectivity
        try:
            config_validator.create_directories()
            config_validator.create_database_if_missing(
                config.postgres_host,
                config.postgres_port,
                config.postgres_db,
                config.postgres_user,
                config.postgres_password,
            )
            config_validator.verify_postgres_connection(
                config.postgres_host,
                config.postgres_port,
                config.postgres_db,
                config.postgres_user,
                config.postgres_password,
            )
            db_status = "Connected"
        except Exception as exc:
            db_status = "Failed"
            raise DatabaseError(f"PostgreSQL database connection failed: {exc}")

        # Step 2: Initialize PostgreSQL database tables
        try:
            initialize_database()
        except Exception as exc:
            db_status = "Failed"
            raise DatabaseError(f"Database table initialization failed: {exc}")

        # Step 3: Create the JobScraper using the validated runtime configuration
        # (no fallback to app/config.py defaults)
        scraper = JobScraper(
            apify_token=config.apify_token,
            apify_actor_id=config.apify_actor_id,
        )

        # Determine if custom query argument filters are supplied
        has_user_query = any(
            getattr(args, attr) is not None
            for attr in [
                "keywords",
                "location",
                "remote",
                "hybrid",
                "onsite",
                "days",
                "experience",
                "company",
            ]
        )

        if not has_user_query:
            # Fall back to sensible defaults
            keyword = "Python"
            location = "Remote"
            remote = True
            max_results = args.limit or settings.max_results
            date_posted = None
            hybrid = None
            onsite = None
            experience = None
            company = None
        else:
            keyword = args.keywords
            location = args.location
            remote = args.remote
            max_results = args.limit or settings.max_results
            date_posted = map_days_to_date_posted(args.days)
            hybrid = args.hybrid
            onsite = args.onsite
            experience = args.experience
            company = args.company

        request = JobSearchRequest(
            keyword=keyword,
            location=location,
            max_results=max_results,
            remote=remote,
            hybrid=hybrid,
            onsite=onsite,
            experience_level=experience,
            company=company,
            date_posted=date_posted,
        )

        # Step 5: Fetch jobs using the existing pipeline
        # fetch_jobs internally executes Apify, normalizes, validates, and dedupes.
        jobs = scraper.fetch_jobs(request)

        # Gather metrics from the scraper execution
        total_fetched = scraper.last_run_raw_count
        total_validated = scraper.last_run_validated_count
        duplicate_removed = scraper.last_run_duplicate_count

        if settings.post_scraper_enabled:
            try:
                from app.scraper import PostScraper
                from app.apify_client import ApifyClient
                post_scraper = PostScraper(
                    client=ApifyClient(token=config.apify_token, actor_id=settings.apify_post_actor_id)
                )
                posts = post_scraper.fetch_posts(request)
                jobs.extend(posts)
                total_fetched += post_scraper.last_run_raw_count
                total_validated += post_scraper.last_run_validated_count
                duplicate_removed += post_scraper.last_run_duplicate_count
            except Exception as exc:
                print(f"Warning: Post scraping failed, continuing with jobs: {exc}", file=sys.stderr)

        # Step 6: Persist jobs using JobRepository
        repository = JobRepository()
        repository.save_jobs(jobs)

        # Gather metrics from repository save
        jobs_saved = repository.last_run_saved_count
        jobs_updated = repository.last_run_updated_count

    except (ApifyAuthenticationError, ApifyTimeoutError, ApifyRuntimeError) as exc:
        print(f"Error: {exc}", file=sys.stderr)
        exit_code = 3
        exit_status = "Apify Error"

    except DatabaseError as exc:
        print(f"Error: {exc}", file=sys.stderr)
        exit_code = 2
        exit_status = "Database Error"

    except ValidationError as exc:
        print(f"Error: {exc}", file=sys.stderr)
        exit_code = 4
        exit_status = "Validation Error"

    except (ConfigurationError, ApifyConfigurationError, EnvironmentError, ValueError) as exc:
        print(f"Error: {exc}", file=sys.stderr)
        exit_code = 1
        exit_status = "Configuration Error"

    except Exception as exc:
        print(f"Unexpected Exception occurred: {exc}", file=sys.stderr)
        exit_code = 5
        exit_status = "Unexpected Error"

    # Step 7: Print Execution Summary
    end_time = datetime.now(timezone.utc)
    print_summary(
        start_time=start_time,
        end_time=end_time,
        total_fetched=total_fetched,
        total_validated=total_validated,
        duplicate_removed=duplicate_removed,
        jobs_saved=jobs_saved,
        jobs_updated=jobs_updated,
        db_status=db_status,
        apify_status=apify_status,
        exit_status=exit_status,
        exit_code=exit_code,
    )

    metrics = {
        "total_fetched": total_fetched,
        "total_validated": total_validated,
        "duplicate_removed": duplicate_removed,
        "jobs_saved": jobs_saved,
        "jobs_updated": jobs_updated,
        "db_status": db_status,
        "apify_status": apify_status,
        "exit_status": exit_status,
    }

    return exit_code, metrics


def main() -> int:
    """Run the main scraper pipeline orchestration flow.

    Returns:
        The exit status code (0 for success, non-zero for failures).
    """
    args = parse_arguments()

    if args.stats:
        from app.exporter import ExportService
        from app.database import DatabaseError

        try:
            config_validator.load_environment()
            env_values = config_validator.validate_required_env()
            config = config_validator.build_config(env_values)
            config_validator.verify_postgres_connection(
                config.postgres_host,
                config.postgres_port,
                config.postgres_db,
                config.postgres_user,
                config.postgres_password,
            )

            service = ExportService()
            stats = service.get_statistics()

            print("\n" + "=" * 55)
            print("                JOB DATABASE STATISTICS")
            print("=" * 55)
            print(f"Total Jobs:             {stats['total_jobs']}")
            print(f"Total Companies:        {stats['total_companies']}")
            print(f"Total Countries:        {stats['total_countries']}")
            print(f"Remote Jobs:            {stats['remote_jobs']}")
            print(f"Hybrid Jobs:            {stats['hybrid_jobs']}")
            print(f"Onsite Jobs:            {stats['onsite_jobs']}")
            print(f"Easy Apply Jobs:        {stats['easy_apply_jobs']}")
            print(f"Duplicate Jobs:         {stats['duplicate_count']}")
            print(f"Latest Scrape Date:     {stats['latest_scrape_date'].strftime('%Y-%m-%d %H:%M:%S UTC') if stats['latest_scrape_date'] else 'None'}")
            print(f"Oldest Scrape Date:     {stats['oldest_scrape_date'].strftime('%Y-%m-%d %H:%M:%S UTC') if stats['oldest_scrape_date'] else 'None'}")
            print("=" * 55 + "\n")
            return 0
        except (ConfigurationError, EnvironmentError, ValueError) as exc:
            print(f"Error: Configuration validation failed: {exc}", file=sys.stderr)
            return 1
        except DatabaseError as exc:
            print(f"Error: Database connection failed: {exc}", file=sys.stderr)
            return 2
        except Exception as exc:
            print(f"Error: Unexpected exception: {exc}", file=sys.stderr)
            return 5

    elif args.export:
        from app.exporter import ExportService
        from app.database import DatabaseError

        try:
            config_validator.load_environment()
            env_values = config_validator.validate_required_env()
            config = config_validator.build_config(env_values)
            config_validator.verify_postgres_connection(
                config.postgres_host,
                config.postgres_port,
                config.postgres_db,
                config.postgres_user,
                config.postgres_password,
            )

            output_path = args.output
            if not output_path:
                if args.export == "csv":
                    output_path = config.csv_export_path
                elif args.export == "excel":
                    output_path = config.excel_export_path
                elif args.export == "json":
                    output_path = "data/jobs.json"

            service = ExportService()
            if args.export == "csv":
                service.export_csv(output_path)
            elif args.export == "excel":
                service.export_excel(output_path)
            elif args.export == "json":
                service.export_json(output_path)

            print(f"Jobs successfully exported to {args.export.upper()} at: {output_path}")
            return 0
        except FileNotFoundError as exc:
            print(f"Error: Output path parent directory does not exist: {exc}", file=sys.stderr)
            return 1
        except PermissionError as exc:
            print(f"Error: Permission denied writing to file: {exc}", file=sys.stderr)
            return 1
        except (ConfigurationError, EnvironmentError, ValueError) as exc:
            print(f"Error: Configuration validation failed: {exc}", file=sys.stderr)
            return 1
        except DatabaseError as exc:
            print(f"Error: Database connection failed: {exc}", file=sys.stderr)
            return 2
        except Exception as exc:
            print(f"Error: Unexpected exception: {exc}", file=sys.stderr)
            return 5

    elif args.schedule:
        import signal
        from app.scheduler import JobScheduler

        scheduler = JobScheduler()
        # Register job (interval is overridden if explicitly passed via --interval)
        scheduler.register_job(run_pipeline, args, interval_minutes=args.interval)
        scheduler.start()

        shutdown_event = threading.Event()

        def handle_signal(signum, frame):
            print(f"\nReceived signal {signum}. Shutting down scheduler gracefully...", flush=True)
            scheduler.stop()
            shutdown_event.set()

        signal.signal(signal.SIGINT, handle_signal)
        signal.signal(signal.SIGTERM, handle_signal)

        print("Scheduler running in background. Press Ctrl+C to exit.", flush=True)
        try:
            while not shutdown_event.is_set():
                shutdown_event.wait(timeout=1.0)
        except (KeyboardInterrupt, SystemExit):
            print("\nShutting down scheduler gracefully...", flush=True)
            scheduler.stop()

        return 0
    else:
        # Default behavior: run the pipeline once and return the exit code
        exit_code, _ = run_pipeline(args)
        return exit_code


if __name__ == "__main__":
    sys.exit(main())
