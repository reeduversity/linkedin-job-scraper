import unittest
from contextlib import contextmanager
from unittest.mock import patch

import psycopg

from app.models import LinkedInJob
from app.repository import DatabaseError, JobRepository


class FakeCursor:
    def __init__(self, connection: "FakeConnection") -> None:
        self.connection = connection
        self.executed_queries: list[str] = []

    def execute(self, query: str, params: tuple | None = None) -> None:
        self.executed_queries.append(query)
        self.connection.queries.append(query)
        if self.connection.fail_on_execute:
            raise psycopg.Error("simulated failure")
        if "SELECT created_at" in query:
            if self.connection.fetchone_results:
                self.connection._fetchone_result = self.connection.fetchone_results.pop(0)
            else:
                self.connection._fetchone_result = None
        else:
            self.connection._fetchone_result = None

    def fetchone(self):
        return self.connection._fetchone_result

    def __enter__(self) -> "FakeCursor":
        return self

    def __exit__(self, exc_type, exc, tb) -> bool:
        return False


class FakeConnection:
    def __init__(self, *, fetchone_results: list | None = None, fail_on_execute: bool = False) -> None:
        self.fetchone_results = list(fetchone_results or [])
        self._fetchone_result = None
        self.fail_on_execute = fail_on_execute
        self.queries: list[str] = []
        self.commits = 0
        self.rollbacks = 0
        self.closed = False

    def cursor(self) -> FakeCursor:
        return FakeCursor(self)

    def commit(self) -> None:
        self.commits += 1

    def rollback(self) -> None:
        self.rollbacks += 1

    def close(self) -> None:
        self.closed = True


class Stage8RepositoryTests(unittest.TestCase):
    def _make_job(self, url: str) -> LinkedInJob:
        return LinkedInJob(
            job_title="Python Engineer",
            company_name="Acme",
            linkedin_job_url=url,
            application_url="https://careers.example.com/apply",
            raw_json={"source": "test"},
        )

    def _patch_connection(self, connection: FakeConnection):
        @contextmanager
        def fake_get_connection():
            yield connection

        return patch("app.repository.get_connection", fake_get_connection)

    def test_save_job_inserts_new_job(self) -> None:
        connection = FakeConnection(fetchone_results=[None])
        repository = JobRepository()

        with patch("app.repository.initialize_database"), self._patch_connection(connection):
            saved = repository.save_job(self._make_job("https://www.linkedin.com/jobs/view/1"))

        self.assertIsNotNone(saved)
        self.assertTrue(any("INSERT INTO jobs" in query for query in connection.queries))
        self.assertEqual(connection.commits, 1)

    def test_update_existing_job_preserves_created_at(self) -> None:
        connection = FakeConnection(fetchone_results=[("2024-01-01T00:00:00Z",)])
        repository = JobRepository()

        with patch("app.repository.initialize_database"), self._patch_connection(connection):
            repository.save_job(self._make_job("https://www.linkedin.com/jobs/view/2"))

        self.assertTrue(any("UPDATE jobs" in query for query in connection.queries))
        self.assertEqual(connection.commits, 1)

    def test_duplicate_prevention_in_bulk_save(self) -> None:
        connection = FakeConnection(fetchone_results=[None, None, None])
        repository = JobRepository()
        jobs = [self._make_job("https://www.linkedin.com/jobs/view/3"), self._make_job("https://www.linkedin.com/jobs/view/3"), self._make_job("https://www.linkedin.com/jobs/view/4")]

        with patch("app.repository.initialize_database"), self._patch_connection(connection):
            repository.save_jobs(jobs)

        self.assertEqual(sum(1 for query in connection.queries if "INSERT INTO jobs" in query), 2)

    def test_rollback_on_failure(self) -> None:
        connection = FakeConnection(fetchone_results=[None], fail_on_execute=True)
        repository = JobRepository()

        with patch("app.repository.initialize_database"), self._patch_connection(connection):
            with self.assertRaises(DatabaseError):
                repository.save_job(self._make_job("https://www.linkedin.com/jobs/view/5"))

        self.assertEqual(connection.rollbacks, 1)
        self.assertEqual(connection.commits, 0)

    def test_bulk_insert_handles_large_batch(self) -> None:
        connection = FakeConnection(fetchone_results=[None] * 100)
        repository = JobRepository()
        jobs = [self._make_job(f"https://www.linkedin.com/jobs/view/{index}") for index in range(100)]

        with patch("app.repository.initialize_database"), self._patch_connection(connection):
            saved = repository.save_jobs(jobs)

        self.assertEqual(len(saved), 100)
        self.assertEqual(connection.commits, 1)

    def test_connection_failures_raise_database_error(self) -> None:
        repository = JobRepository()

        with patch("app.repository.initialize_database"), patch("app.repository.get_connection", side_effect=psycopg.Error("db down")):
            with self.assertRaises(DatabaseError):
                repository.save_job(self._make_job("https://www.linkedin.com/jobs/view/6"))


if __name__ == "__main__":
    unittest.main()
