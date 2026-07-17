import argparse
import sys
import unittest
from unittest.mock import MagicMock, patch

from app.config_validator import ConfigurationError
from app.apify_client import (
    ApifyAuthenticationError,
    ApifyConfigurationError,
    ApifyRuntimeError,
    ApifyTimeoutError,
)
from app.database import DatabaseError
from app.validation import ValidationError
from main import main, map_days_to_date_posted, parse_arguments


class Stage9Tests(unittest.TestCase):
    def test_map_days_to_date_posted(self) -> None:
        self.assertIsNone(map_days_to_date_posted(None))
        self.assertEqual(map_days_to_date_posted("1"), "today")
        self.assertEqual(map_days_to_date_posted("3"), "3days")
        self.assertEqual(map_days_to_date_posted("7"), "week")
        self.assertEqual(map_days_to_date_posted("30"), "month")
        self.assertEqual(map_days_to_date_posted("other"), "other")

    @patch("sys.argv", ["main.py", "--keywords", "Go", "--location", "Berlin", "--limit", "15"])
    def test_parse_arguments(self) -> None:
        args = parse_arguments()
        self.assertEqual(args.keywords, "Go")
        self.assertEqual(args.location, "Berlin")
        self.assertEqual(args.limit, 15)

    @patch("main.parse_arguments")
    @patch("app.config_validator.load_environment")
    @patch("app.config_validator.validate_required_env")
    @patch("app.config_validator.build_config")
    def test_configuration_error_exit_code(
        self, mock_build, mock_validate, mock_load, mock_parse
    ) -> None:
        # Simulate environment error during validation
        mock_parse.return_value.schedule = False
        mock_parse.return_value.interval = None
        mock_parse.return_value.stats = False
        mock_parse.return_value.export = None
        mock_parse.return_value.output = None
        mock_validate.side_effect = EnvironmentError("Missing env var")
        with patch("sys.stdout"), patch("sys.stderr"):
            exit_code = main()
        self.assertEqual(exit_code, 1)

    @patch("main.parse_arguments")
    @patch("app.config_validator.load_environment")
    @patch("app.config_validator.validate_required_env")
    @patch("app.config_validator.build_config")
    @patch("app.config_validator.verify_apify_token")
    def test_apify_auth_error_exit_code(
        self, mock_verify, mock_build, mock_validate, mock_load, mock_parse
    ) -> None:
        # Simulate Apify auth error (which should map to exit code 3, Apify Error)
        mock_parse.return_value.schedule = False
        mock_parse.return_value.interval = None
        mock_parse.return_value.stats = False
        mock_parse.return_value.export = None
        mock_parse.return_value.output = None
        mock_verify.side_effect = ApifyAuthenticationError("Auth failed")
        with patch("sys.stdout"), patch("sys.stderr"):
            exit_code = main()
        self.assertEqual(exit_code, 3)

    @patch("main.parse_arguments")
    @patch("app.config_validator.load_environment")
    @patch("app.config_validator.validate_required_env")
    @patch("app.config_validator.build_config")
    @patch("app.config_validator.verify_apify_token")
    @patch("app.config_validator.create_directories")
    @patch("app.config_validator.create_database_if_missing")
    @patch("app.config_validator.verify_postgres_connection")
    def test_database_error_exit_code(
        self, mock_verify_db, mock_create_db, mock_dirs, mock_verify_apify, mock_build, mock_validate, mock_load, mock_parse
    ) -> None:
        # Simulate Database error during connectivity verify (maps to 2)
        mock_parse.return_value.schedule = False
        mock_parse.return_value.interval = None
        mock_parse.return_value.stats = False
        mock_parse.return_value.export = None
        mock_parse.return_value.output = None
        mock_verify_db.side_effect = DatabaseError("Database down")
        with patch("sys.stdout"), patch("sys.stderr"):
            exit_code = main()
        self.assertEqual(exit_code, 2)

    @patch("main.parse_arguments")
    @patch("app.config_validator.load_environment")
    @patch("app.config_validator.validate_required_env")
    @patch("app.config_validator.build_config")
    @patch("app.config_validator.verify_apify_token")
    @patch("app.config_validator.create_directories")
    @patch("app.config_validator.create_database_if_missing")
    @patch("app.config_validator.verify_postgres_connection")
    @patch("main.initialize_database")
    @patch("main.JobScraper")
    def test_validation_error_exit_code(
        self, mock_scraper_class, mock_init_db, mock_verify_db, mock_create_db, mock_dirs, mock_verify_apify, mock_build, mock_validate, mock_load, mock_parse
    ) -> None:
        # Simulate ValidationError during scraper fetch (maps to 4)
        mock_parse.return_value = argparse.Namespace(
            keywords=None,
            location=None,
            remote=None,
            hybrid=None,
            onsite=None,
            days=None,
            experience=None,
            company=None,
            limit=None,
            schedule=False,
            interval=None,
            run_once=True,
            stats=False,
            export=None,
            output=None,
        )
        mock_scraper = MagicMock()
        mock_scraper_class.return_value = mock_scraper
        mock_scraper.fetch_jobs.side_effect = ValidationError("Invalid records found")
        with patch("sys.stdout"), patch("sys.stderr"):
            exit_code = main()
        self.assertEqual(exit_code, 4)

    @patch("main.parse_arguments")
    @patch("app.config_validator.load_environment")
    @patch("app.config_validator.validate_required_env")
    @patch("app.config_validator.build_config")
    @patch("app.config_validator.verify_apify_token")
    @patch("app.config_validator.create_directories")
    @patch("app.config_validator.create_database_if_missing")
    @patch("app.config_validator.verify_postgres_connection")
    @patch("main.initialize_database")
    @patch("main.JobScraper")
    def test_unexpected_error_exit_code(
        self, mock_scraper_class, mock_init_db, mock_verify_db, mock_create_db, mock_dirs, mock_verify_apify, mock_build, mock_validate, mock_load, mock_parse
    ) -> None:
        # Simulate generic unexpected runtime exception (maps to 5)
        mock_parse.return_value = argparse.Namespace(
            keywords=None,
            location=None,
            remote=None,
            hybrid=None,
            onsite=None,
            days=None,
            experience=None,
            company=None,
            limit=None,
            schedule=False,
            interval=None,
            run_once=True,
            stats=False,
            export=None,
            output=None,
        )
        mock_scraper = MagicMock()
        mock_scraper_class.return_value = mock_scraper
        mock_scraper.fetch_jobs.side_effect = RuntimeError("Something bad happened")
        with patch("sys.stdout"), patch("sys.stderr"):
            exit_code = main()
        self.assertEqual(exit_code, 5)


if __name__ == "__main__":
    unittest.main()
