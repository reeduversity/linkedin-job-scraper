import json
import unittest
from datetime import datetime, timezone
from pathlib import Path
from unittest.mock import MagicMock, patch

from fastapi.testclient import TestClient

from app.database import DatabaseError
from app.main_api import app
from app.models import LinkedInJob
from app.validation import ValidationError as AppValidationError


class Stage12Tests(unittest.TestCase):
    def setUp(self) -> None:
        self.client = TestClient(app)

    def _make_dummy_job(self) -> LinkedInJob:
        return LinkedInJob(
            job_title="DevOps Engineer",
            company_name="Cloud Corp",
            company_url="https://cloud.example.com",
            linkedin_job_url="https://www.linkedin.com/jobs/view/999",
            job_id="999",
            location="Berlin",
            country="DE",
            workplace_type="HYBRID",
            employment_type="FULL_TIME",
            experience_level="MID_SENIOR",
            easy_apply=True,
            posted_date=datetime(2026, 4, 1, tzinfo=timezone.utc),
            scraped_timestamp=datetime(2026, 7, 15, tzinfo=timezone.utc),
            skills=["Docker", "Kubernetes"],
            raw_json={"jobId": "999"}
        )

    @patch("app.config_validator.verify_postgres_connection")
    def test_health_endpoint(self, mock_verify_db) -> None:
        # DB connection success
        response = self.client.get("/api/health")
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertTrue(data["success"])
        self.assertEqual(data["data"]["database"], "healthy")
        self.assertEqual(data["data"]["version"], "1.0.0")

        # DB connection failure should return database status as unhealthy
        mock_verify_db.side_effect = Exception("DB Down")
        response = self.client.get("/api/health")
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data["data"]["database"], "unhealthy")
        self.assertEqual(data["data"]["status"], "degraded")

    @patch("app.repository.JobRepository.get_all_jobs")
    @patch("app.repository.JobRepository.count_jobs")
    def test_jobs_list_endpoint(self, mock_count, mock_get_all) -> None:
        mock_get_all.return_value = [self._make_dummy_job()]
        mock_count.return_value = 1

        response = self.client.get("/api/jobs?page=1&limit=5&keyword=DevOps")
        self.assertEqual(response.status_code, 200)
        
        # Verify custom header timing middleware
        self.assertIn("X-Process-Time", response.headers)

        data = response.json()
        self.assertTrue(data["success"])
        self.assertEqual(data["data"]["total"], 1)
        self.assertEqual(len(data["data"]["items"]), 1)
        self.assertEqual(data["data"]["items"][0]["job_title"], "DevOps Engineer")

    @patch("app.repository.JobRepository.get_job_by_id")
    def test_single_job_endpoint(self, mock_get_by_id) -> None:
        mock_get_by_id.return_value = self._make_dummy_job()
        
        response = self.client.get("/api/jobs/999")
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertTrue(data["success"])
        self.assertEqual(data["data"]["job_id"], "999")

        # 404 handler check
        mock_get_by_id.return_value = None
        response = self.client.get("/api/jobs/notfound")
        self.assertEqual(response.status_code, 404)
        data = response.json()
        self.assertFalse(data["success"])
        self.assertIn("not found", data["error"])

    @patch("app.config_validator.verify_apify_token")
    @patch("app.config_validator.verify_postgres_connection")
    @patch("app.scraper.JobScraper.fetch_jobs")
    @patch("app.repository.JobRepository.save_jobs")
    def test_jobs_scrape_endpoint(self, mock_save, mock_fetch, mock_verify_db, mock_verify_apify) -> None:
        mock_fetch.return_value = [self._make_dummy_job()]
        # Mock metrics counters
        mock_fetch.self = MagicMock()
        with patch("app.scraper.JobScraper.last_run_raw_count", 1), \
             patch("app.scraper.JobScraper.last_run_validated_count", 1), \
             patch("app.scraper.JobScraper.last_run_duplicate_count", 0), \
             patch("app.repository.JobRepository.last_run_saved_count", 1), \
             patch("app.repository.JobRepository.last_run_updated_count", 0):
            
            response = self.client.post("/api/jobs/scrape", json={
                "keyword": "DevOps",
                "location": "Berlin"
            })
            self.assertEqual(response.status_code, 200)
            data = response.json()
            self.assertTrue(data["success"])
            self.assertEqual(data["data"]["saved"], 1)

    @patch("app.repository.JobRepository.get_statistics")
    def test_statistics_endpoint(self, mock_stats) -> None:
        mock_stats.return_value = {"total_jobs": 42}
        response = self.client.get("/api/statistics")
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertTrue(data["success"])
        self.assertEqual(data["data"]["total_jobs"], 42)

    @patch("app.exporter.ExportService.export_csv")
    def test_export_endpoints(self, mock_csv) -> None:
        # Mock file response
        with patch("app.api.routes.exports.FileResponse") as mock_response:
            mock_response.return_value = "file_stream"
            response = self.client.get("/api/export/csv")
            self.assertEqual(response.status_code, 200)

    def test_scheduler_endpoints(self) -> None:
        # Get status
        response = self.client.get("/api/scheduler/status")
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertTrue(data["success"])
        self.assertIn("running", data["data"])

        # Stop scheduler
        response = self.client.post("/api/scheduler/stop")
        self.assertEqual(response.status_code, 200)
        
        # Start scheduler
        response = self.client.post("/api/scheduler/start")
        self.assertEqual(response.status_code, 200)

        # Run once (triggered background task)
        response = self.client.post("/api/scheduler/run-once")
        self.assertEqual(response.status_code, 200)

    @patch("app.repository.JobRepository.get_all_jobs")
    def test_global_exception_handler_middleware(self, mock_get_all) -> None:
        # Force a database exception to check global exception mapping and lack of raw python traceback
        mock_get_all.side_effect = DatabaseError("PostgreSQL server gone")
        response = self.client.get("/api/jobs")
        self.assertEqual(response.status_code, 500)
        data = response.json()
        self.assertFalse(data["success"])
        self.assertEqual(data["message"], "Database Error")
        self.assertEqual(data["error"], "Database operation failed: PostgreSQL server gone")
        
        # Force a validation error
        mock_get_all.side_effect = AppValidationError("Fields invalid")
        response = self.client.get("/api/jobs")
        self.assertEqual(response.status_code, 400)
        data = response.json()
        self.assertFalse(data["success"])
        self.assertEqual(data["message"], "Validation Error")

    def test_validation_input_errors(self) -> None:
        # Send bad inputs (e.g., negative page / limit numbers) to verify request validators
        response = self.client.get("/api/jobs?page=-5")
        self.assertEqual(response.status_code, 400)
        data = response.json()
        self.assertFalse(data["success"])
        self.assertEqual(data["message"], "Request Validation Error")


if __name__ == "__main__":
    unittest.main()
