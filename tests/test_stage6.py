import unittest

from app.models import LinkedInJob
from app.validation import ValidationError, validate_job, validate_jobs


class Stage6ValidationTests(unittest.TestCase):
    def test_validate_job_normalizes_and_preserves_raw_json(self) -> None:
        raw_job = LinkedInJob(
            job_title="  Python Engineer  ",
            company_name="  Acme  ",
            linkedin_job_url="https://www.linkedin.com/jobs/view/12345",
            salary="  $120k ",
            currency=" usd ",
            skills=[" Python ", "Postgres", "Python"],
            raw_json={"source": "apify"},
        )

        cleaned = validate_job(raw_job)

        self.assertEqual(cleaned.job_title, "Python Engineer")
        self.assertEqual(cleaned.company_name, "Acme")
        self.assertEqual(cleaned.salary, "$120k")
        self.assertEqual(cleaned.currency, "USD")
        self.assertEqual(cleaned.skills, ["Python", "Postgres"])
        self.assertEqual(cleaned.raw_json, {"source": "apify"})

    def test_validate_job_rejects_invalid_urls_and_missing_required_fields(self) -> None:
        invalid = LinkedInJob(
            job_title="",
            company_name="",
            linkedin_job_url="not-a-url",
            company_url="bad-url",
            application_url="still-bad",
            raw_json={},
        )

        with self.assertRaises(ValidationError):
            validate_job(invalid)

    def test_validate_jobs_only_returns_clean_records(self) -> None:
        valid = LinkedInJob(
            job_title="Data Engineer",
            company_name="Example",
            linkedin_job_url="https://www.linkedin.com/jobs/view/999",
            raw_json={"source": "apify"},
        )
        invalid = LinkedInJob(
            job_title="",
            company_name="",
            linkedin_job_url="not-a-url",
            raw_json={},
        )

        jobs = validate_jobs([valid, invalid])

        self.assertEqual(len(jobs), 1)
        self.assertEqual(jobs[0].job_title, "Data Engineer")


if __name__ == "__main__":
    unittest.main()
