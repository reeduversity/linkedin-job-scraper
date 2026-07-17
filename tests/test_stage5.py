import unittest

from app.models import ActorResponse, JobSearchRequest, LinkedInJob
from app.scraper import JobScraper


class Stage5Tests(unittest.TestCase):
    def test_search_request_accepts_filters(self) -> None:
        request = JobSearchRequest(keyword="python", location="Remote", max_results=5)
        self.assertEqual(request.keyword, "python")
        self.assertEqual(request.location, "Remote")
        self.assertEqual(request.max_results, 5)

    def test_actor_response_parses_jobs(self) -> None:
        response = ActorResponse(
            jobs=[{
                "linkedinJobUrl": "https://www.linkedin.com/jobs/view/12345",
                "title": "Python Engineer",
                "companyName": "Acme",
            }]
        )
        self.assertEqual(len(response.jobs), 1)
        self.assertEqual(response.jobs[0].linkedin_job_url, "https://www.linkedin.com/jobs/view/12345")

    def test_scraper_normalizes_to_linkedin_job_model(self) -> None:
        scraper = JobScraper.__new__(JobScraper)
        item = {
            "linkedinJobUrl": "https://www.linkedin.com/jobs/view/12345",
            "title": "Python Engineer",
            "companyName": "Acme",
            "companyUrl": "https://example.com",
            "location": "Remote",
            "country": "US",
            "employmentType": "Full-Time",
            "experienceLevel": "Entry Level",
            "skills": ["Python", "Postgres"],
        }
        job = scraper._normalize_item(item)
        self.assertIsInstance(job, LinkedInJob)
        self.assertEqual(job.job_title, "Python Engineer")
        self.assertEqual(job.company_name, "Acme")
        self.assertEqual(job.linkedin_job_url, "https://www.linkedin.com/jobs/view/12345")


if __name__ == "__main__":
    unittest.main()
