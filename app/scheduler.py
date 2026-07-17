import logging
from pathlib import Path
import threading
import time
from typing import Any, Callable

from apscheduler.schedulers.background import BackgroundScheduler
from app.config import settings

logger = logging.getLogger("scheduler")


def _ensure_file_logger() -> None:
    """Initialize file logging lazily (avoid import-time side effects)."""
    if any(isinstance(h, logging.FileHandler) for h in logger.handlers):
        return

    # Ensure log directory exists
    Path("logs").mkdir(exist_ok=True)

    handler = logging.FileHandler("logs/scheduler.log", encoding="utf-8")
    formatter = logging.Formatter("%(asctime)s - %(levelname)s - %(message)s")
    handler.setFormatter(formatter)
    logger.addHandler(handler)



class JobScheduler:
    """Production-ready background scheduler using APScheduler."""

    def __init__(self) -> None:
        self._scheduler = BackgroundScheduler()
        self._lock = threading.Lock()
        self._is_running = False
        _ensure_file_logger()


    def start(self) -> None:
        """Start the background scheduler."""
        if not settings.scraper_enabled:
            logger.info("Scheduler not started: scraper is disabled via SCRAPER_ENABLED config.")
            return

        with self._lock:
            if not self._is_running:
                self._scheduler.start()
                self._is_running = True
                logger.info("Scheduler started")

    def stop(self) -> None:
        """Stop the scheduler gracefully."""
        with self._lock:
            if self._is_running:
                self._scheduler.shutdown(wait=True)
                self._is_running = False
                logger.info("Scheduler stopped")

    def register_job(
        self,
        run_pipeline_func: Callable[[Any], tuple[int, dict[str, Any]]],
        args: Any,
        interval_minutes: int | None = None,
    ) -> None:
        """Register a scraping pipeline execution job."""
        interval = interval_minutes if interval_minutes is not None else settings.scraper_interval_minutes

        max_instances = settings.scraper_max_instances
        coalesce = settings.scraper_coalesce
        misfire_grace_time = settings.scraper_misfire_grace_time

        job_run_lock = threading.Lock()

        def job_wrapper() -> None:
            if not job_run_lock.acquire(blocking=False):
                logger.warning("Job execution skipped: Previous instance is still running (overlap prevention).")
                return

            logger.info("Job started")
            start_time = time.monotonic()
            try:
                exit_code, metrics = run_pipeline_func(args)
                duration = time.monotonic() - start_time
                if exit_code == 0:
                    logger.info(
                        f"Job completed successfully in {duration:.2f}s | "
                        f"Jobs Fetched: {metrics.get('total_fetched', 0)} | "
                        f"Jobs Saved: {metrics.get('jobs_saved', 0)}"
                    )
                else:
                    logger.error(
                        f"Job completed with error status '{metrics.get('exit_status', 'Unknown Error')}' "
                        f"(code {exit_code}) in {duration:.2f}s | "
                        f"Jobs Fetched: {metrics.get('total_fetched', 0)} | "
                        f"Jobs Saved: {metrics.get('jobs_saved', 0)}"
                    )
            except Exception as exc:
                duration = time.monotonic() - start_time
                logger.exception(f"Job failed with unexpected error after {duration:.2f}s: {exc}")
            finally:
                job_run_lock.release()

        self._scheduler.add_job(
            job_wrapper,
            "interval",
            minutes=interval,
            id="scraping_job",
            max_instances=max_instances,
            coalesce=coalesce,
            misfire_grace_time=misfire_grace_time,
        )
        logger.info(f"Registered job 'scraping_job' with interval {interval} minute(s)")
