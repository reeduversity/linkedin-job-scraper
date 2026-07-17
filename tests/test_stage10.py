import logging
import os
import time
import unittest
from pathlib import Path
from unittest.mock import MagicMock, patch

from app.config import settings
from app.scheduler import JobScheduler, logger as scheduler_logger


class Stage10Tests(unittest.TestCase):
    def setUp(self) -> None:
        self.log_path = Path("logs/scheduler_test.log")
        # Direct log to test file
        self.test_handler = logging.FileHandler(self.log_path, encoding="utf-8")
        self.test_handler.setFormatter(logging.Formatter("%(asctime)s - %(levelname)s - %(message)s"))
        scheduler_logger.addHandler(self.test_handler)
        self.original_level = scheduler_logger.level
        scheduler_logger.setLevel(logging.INFO)

    def tearDown(self) -> None:
        scheduler_logger.removeHandler(self.test_handler)
        self.test_handler.close()
        if self.log_path.exists():
            try:
                self.log_path.unlink()
            except Exception:
                pass

    def test_config_defaults(self) -> None:
        self.assertIsNotNone(settings.scraper_interval_minutes)
        self.assertTrue(settings.scraper_enabled)
        self.assertEqual(settings.scraper_max_instances, 1)
        self.assertTrue(settings.scraper_coalesce)
        self.assertEqual(settings.scraper_misfire_grace_time, 60)

    def test_scheduler_lifecycle(self) -> None:
        scheduler = JobScheduler()
        self.assertFalse(scheduler._is_running)

        scheduler.start()
        self.assertTrue(scheduler._is_running)
        self.assertTrue(scheduler._scheduler.running)

        scheduler.stop()
        self.assertFalse(scheduler._is_running)
        self.assertFalse(scheduler._scheduler.running)

    def test_job_registration(self) -> None:
        scheduler = JobScheduler()
        mock_pipeline = MagicMock(return_value=(0, {}))

        scheduler.register_job(mock_pipeline, MagicMock(), interval_minutes=5)
        jobs = scheduler._scheduler.get_jobs()
        self.assertEqual(len(jobs), 1)
        self.assertEqual(jobs[0].id, "scraping_job")

    def test_logging_and_exception_handling(self) -> None:
        scheduler = JobScheduler()
        
        # Test successful job run logs
        mock_pipeline = MagicMock(return_value=(0, {"total_fetched": 10, "jobs_saved": 5}))
        scheduler.register_job(mock_pipeline, MagicMock(), interval_minutes=1)
        
        # Manually invoke the job function stored in the scheduler
        jobs = scheduler._scheduler.get_jobs()
        job_func = jobs[0].func
        
        job_func()
        mock_pipeline.assert_called_once()

        # Check log file
        self.assertTrue(self.log_path.exists())
        log_content = self.log_path.read_text(encoding="utf-8")
        self.assertIn("Job started", log_content)
        self.assertIn("Job completed successfully", log_content)
        self.assertIn("Jobs Fetched: 10", log_content)
        self.assertIn("Jobs Saved: 5", log_content)

        # Test job run with exceptions
        mock_pipeline_fail = MagicMock(side_effect=ValueError("Simulated pipeline failure"))
        scheduler_fail = JobScheduler()
        scheduler_fail.register_job(mock_pipeline_fail, MagicMock(), interval_minutes=1)
        
        job_func_fail = scheduler_fail._scheduler.get_jobs()[0].func
        
        # Calling job_func_fail should catch ValueError internally without raising
        try:
            job_func_fail()
        except Exception as exc:
            self.fail(f"job_func raised exception: {exc}")

        log_content_fail = self.log_path.read_text(encoding="utf-8")
        self.assertIn("Job failed with unexpected error", log_content_fail)

    def test_overlap_prevention(self) -> None:
        scheduler = JobScheduler()
        
        # Implement a slow mock pipeline that waits to release lock
        import threading
        pipeline_started = threading.Barrier(2)
        pipeline_finish = threading.Barrier(2)
        
        def slow_pipeline(args):
            pipeline_started.wait()
            pipeline_finish.wait()
            return 0, {}

        scheduler.register_job(slow_pipeline, MagicMock(), interval_minutes=1)
        job_func = scheduler._scheduler.get_jobs()[0].func

        import threading
        t1 = threading.Thread(target=job_func)
        t2 = threading.Thread(target=job_func)

        t1.start()
        # Wait for t1 to acquire lock and reach barrier
        pipeline_started.wait()
        
        # Now launch t2; it should find lock acquired and skip immediately
        t2.start()
        t2.join() # t2 completes instantly since it's skipped

        # Release t1
        pipeline_finish.wait()
        t1.join()

        log_content = self.log_path.read_text(encoding="utf-8")
        self.assertIn("Job execution skipped: Previous instance is still running", log_content)


if __name__ == "__main__":
    unittest.main()
