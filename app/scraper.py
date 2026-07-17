from __future__ import annotations

from datetime import datetime, timezone
import logging
from typing import Any

from tenacity import retry, retry_if_exception, stop_after_attempt, wait_exponential

from app.apify_client import (

    ApifyAuthenticationError,
    ApifyClient,
    ApifyConfigurationError,
    ApifyNetworkError,
    ApifyRateLimitError,
    ApifyRuntimeError,
    ApifyTimeoutError,
)
from app.duplicate_detector import remove_duplicates
from app.models import JobSearchRequest, LinkedInJob
from app.utils import is_valid_url, normalize_date, normalize_optional_string, normalize_salary
from app.validation import validate_jobs


class Scraper:
    """Backward-compatible alias for the scraper entry point."""

    def __init__(self, client: ApifyClient | None = None) -> None:
        self._job_scraper = JobScraper(client=client)

    @property
    def last_run_raw_count(self) -> int:
        return self._job_scraper.last_run_raw_count

    @property
    def last_run_validated_count(self) -> int:
        return self._job_scraper.last_run_validated_count

    @property
    def last_run_duplicate_count(self) -> int:
        return self._job_scraper.last_run_duplicate_count

    @property
    def last_run_unique_count(self) -> int:
        return self._job_scraper.last_run_unique_count

    def fetch_jobs(self, request: JobSearchRequest | None = None, **filters: Any) -> list[LinkedInJob]:
        return self._job_scraper.fetch_jobs(request=request, **filters)


logger = logging.getLogger("scraper")


class JobScraper:

    """Reusable scraper that calls the Apify LinkedIn Jobs Actor."""

    # Test-stage compatibility: tests patch these as *class attributes*
    last_run_raw_count: int = 0
    last_run_validated_count: int = 0
    last_run_duplicate_count: int = 0
    last_run_unique_count: int = 0

    def __init__(
        self,
        client: ApifyClient | None = None,
        *,
        apify_token: str | None = None,
        apify_actor_id: str | None = None,
    ) -> None:
        """
        Ensure the scraper uses explicitly validated runtime config when provided.

        Backward compatible:
        - If `client` is provided, it is used as-is.
        - Otherwise, if `apify_token`/`apify_actor_id` are provided, they are used to construct ApifyClient.
        - Otherwise, fall back to ApifyClient() (legacy behavior; kept for backward compatibility/tests).
        """
        if client is not None:
            self.client = client
        elif apify_token is not None or apify_actor_id is not None:
            # Explicit config path: do not silently fall back to app/config.py defaults.
            self.client = ApifyClient(token=apify_token, actor_id=apify_actor_id)
        else:
            # Legacy behavior
            self.client = ApifyClient()

        # Keep instance attributes in sync with class-level defaults
        self.last_run_raw_count = JobScraper.last_run_raw_count
        self.last_run_validated_count = JobScraper.last_run_validated_count
        self.last_run_duplicate_count = JobScraper.last_run_duplicate_count
        self.last_run_unique_count = JobScraper.last_run_unique_count

    @retry(
        retry=retry_if_exception(lambda exc: isinstance(exc, (ApifyTimeoutError, ApifyNetworkError, ApifyRateLimitError))),
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=10),
        reraise=True,
    )
    def fetch_jobs(self, request: JobSearchRequest | None = None, **filters: Any) -> list[LinkedInJob]:
        # Always reset metrics for each run so API/tests can rely on deterministic values.
        self.last_run_raw_count = 0
        self.last_run_validated_count = 0
        self.last_run_duplicate_count = 0
        self.last_run_unique_count = 0

        search_request = self._build_request(request, filters)
        input_data = search_request.to_actor_input()

        raw_items = self.client.run_actor(input_data, timeout=120)

        jobs: list[LinkedInJob] = []
        for item in raw_items:
            job = self._normalize_item(item)
            if job is not None:
                jobs.append(job)

        validated_jobs = validate_jobs(jobs)
        unique_jobs = remove_duplicates(validated_jobs)

        self.last_run_raw_count = len(raw_items)
        self.last_run_validated_count = len(validated_jobs)
        self.last_run_duplicate_count = len(validated_jobs) - len(unique_jobs)
        self.last_run_unique_count = len(unique_jobs)

        logger.info("Scrape metrics: total=%s duplicates_removed=%s unique=%s", len(validated_jobs), len(validated_jobs) - len(unique_jobs), len(unique_jobs))
        return unique_jobs


    def _build_request(self, request: JobSearchRequest | None, filters: dict[str, Any]) -> JobSearchRequest:
        if request is not None:
            payload = request.model_dump(exclude_none=True)
            payload.update({key: value for key, value in filters.items() if value is not None})
            return JobSearchRequest(**payload)
        if filters:
            return JobSearchRequest(**filters)
        return JobSearchRequest()

    def _normalize_item(self, item: dict[str, Any]) -> LinkedInJob | None:
        if not isinstance(item, dict):
            return None

        linkedin_url = normalize_optional_string(item.get("linkedinJobUrl") or item.get("linkedin_job_url") or item.get("url"))
        if not linkedin_url or not is_valid_url(linkedin_url):
            return None

        raw_json = dict(item)
        return LinkedInJob(
            job_title=normalize_optional_string(item.get("title") or item.get("jobTitle") or item.get("job_title")),
            company_name=normalize_optional_string(item.get("companyName") or item.get("company_name") or item.get("company")),
            company_url=normalize_optional_string(item.get("companyUrl") or item.get("company_url")),
            linkedin_job_url=linkedin_url,
            job_id=normalize_optional_string(item.get("jobId") or item.get("job_id") or item.get("id")),
            location=normalize_optional_string(item.get("location") or item.get("jobLocation")),
            country=normalize_optional_string(item.get("country") or item.get("countryCode")),
            workplace_type=normalize_optional_string(item.get("workplaceType") or item.get("workplace_type")),
            employment_type=normalize_optional_string(item.get("employmentType") or item.get("employment_type")),
            experience_level=normalize_optional_string(item.get("experienceLevel") or item.get("experience_level")),
            salary=normalize_salary(item.get("salary") or item.get("salaryRange")),
            currency=normalize_optional_string(item.get("currency")),
            description=normalize_optional_string(item.get("description") or item.get("descriptionSnippet")),
            job_summary=normalize_optional_string(item.get("jobSummary") or item.get("summary")),
            skills=self._normalize_skills(item.get("skills") or item.get("requiredSkills")),
            industry=normalize_optional_string(item.get("industry")),
            benefits=normalize_optional_string(item.get("benefits")),
            recruiter=normalize_optional_string(item.get("recruiter") or item.get("recruiterName")),
            recruiter_url=normalize_optional_string(item.get("recruiterUrl") or item.get("recruiter_url")),
            company_logo=normalize_optional_string(item.get("companyLogo") or item.get("company_logo")),
            company_size=normalize_optional_string(item.get("companySize") or item.get("company_size")),
            application_url=normalize_optional_string(item.get("applicationUrl") or item.get("application_url")),
            easy_apply=self._normalize_bool(item.get("easyApply") or item.get("easy_apply")),
            posted_date=normalize_date(item.get("postedDate") or item.get("posted_date") or item.get("postedAt")),
            scraped_timestamp=datetime.now(timezone.utc),
            raw_json=raw_json,
        )

    def _normalize_skills(self, value: Any) -> list[str] | None:
        if value is None:
            return None
        if isinstance(value, str):
            items = [item.strip() for item in value.split(",") if item.strip()]
            return list(dict.fromkeys(items))
        if isinstance(value, list):
            return list(dict.fromkeys(str(item).strip() for item in value if str(item).strip()))
        return None

    def _normalize_bool(self, value: Any) -> bool | None:
        if value is None:
            return None
        if isinstance(value, bool):
            return value
        if isinstance(value, str):
            lowered = value.strip().lower()
            if lowered in {"true", "1", "yes"}:
                return True
            if lowered in {"false", "0", "no"}:
                return False
        return None
