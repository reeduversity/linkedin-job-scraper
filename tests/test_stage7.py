import time
import unittest

from app.models import LinkedInJob
from app.duplicate_detector import remove_duplicates, is_duplicate, generate_job_signature


class Stage7DuplicateDetectionTests(unittest.TestCase):
    def test_duplicate_url_is_removed(self) -> None:
        first = LinkedInJob(
            job_title="Python Engineer",
            company_name="Acme",
            linkedin_job_url="https://www.linkedin.com/jobs/view/12345",
            raw_json={"source": "apify"},
        )
        second = LinkedInJob(
            job_title="Python Engineer",
            company_name="Acme",
            linkedin_job_url="https://www.linkedin.com/jobs/view/12345",
            raw_json={"source": "apify"},
        )

        unique_jobs = remove_duplicates([first, second])

        self.assertEqual(len(unique_jobs), 1)
        self.assertEqual(unique_jobs[0].linkedin_job_url, "https://www.linkedin.com/jobs/view/12345")

    def test_duplicate_job_id_is_removed(self) -> None:
        first = LinkedInJob(job_title="Data Engineer", company_name="Example", job_id="abc-123", linkedin_job_url="https://www.linkedin.com/jobs/view/1", raw_json={})
        second = LinkedInJob(job_title="Data Engineer", company_name="Example", job_id="abc-123", linkedin_job_url="https://www.linkedin.com/jobs/view/2", raw_json={})

        self.assertTrue(is_duplicate(first, second))
        self.assertEqual(len(remove_duplicates([first, second])), 1)

    def test_duplicate_company_title_location_is_removed(self) -> None:
        first = LinkedInJob(job_title="Backend Engineer", company_name="Acme", location="Remote", linkedin_job_url="https://www.linkedin.com/jobs/view/3", raw_json={})
        second = LinkedInJob(job_title="  backend engineer  ", company_name="  ACME  ", location="  remote  ", linkedin_job_url="https://www.linkedin.com/jobs/view/4", raw_json={})

        self.assertTrue(is_duplicate(first, second))
        self.assertEqual(len(remove_duplicates([first, second])), 1)

    def test_application_url_duplicate_is_removed(self) -> None:
        first = LinkedInJob(job_title="DevOps", company_name="Contoso", linkedin_job_url="https://www.linkedin.com/jobs/view/5", application_url="https://careers.example.com/apply", raw_json={})
        second = LinkedInJob(job_title="DevOps", company_name="Contoso", linkedin_job_url="https://www.linkedin.com/jobs/view/6", application_url="https://careers.example.com/apply", raw_json={})

        self.assertTrue(is_duplicate(first, second, priority_order=["application_url"]))

    def test_missing_values_are_ignored_safely(self) -> None:
        first = LinkedInJob(job_title="Engineer", company_name="Acme", linkedin_job_url="https://www.linkedin.com/jobs/view/7", raw_json={})
        second = LinkedInJob(job_title="Engineer", company_name="Acme", linkedin_job_url="https://www.linkedin.com/jobs/view/8", raw_json={})

        self.assertIsNone(generate_job_signature(first, priority="linkedIn_job_url"))

    def test_large_list_is_processed(self) -> None:
        jobs = []
        for index in range(2000):
            jobs.append(
                LinkedInJob(
                    job_title="Engineer",
                    company_name="Acme",
                    linkedin_job_url=f"https://www.linkedin.com/jobs/view/{index}",
                    raw_json={},
                )
            )

        started = time.monotonic()
        unique = remove_duplicates(jobs)
        elapsed = time.monotonic() - started

        self.assertEqual(len(unique), 2000)
        self.assertLess(elapsed, 2.0)


if __name__ == "__main__":
    unittest.main()
