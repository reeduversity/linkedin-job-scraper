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
from app.post_parser import parse_post
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

        raw_items, run_id = self.client.run_actor(input_data, timeout=300)

        jobs: list[LinkedInJob] = []
        for item in raw_items:
            job = self._normalize_item(item, run_id)
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

    def _normalize_item(self, item: dict[str, Any], run_id: str | None = None) -> LinkedInJob | None:
        if not isinstance(item, dict):
            return None

        linkedin_url = normalize_optional_string(item.get("linkedinJobUrl") or item.get("linkedin_job_url") or item.get("url"))
        if not linkedin_url or not is_valid_url(linkedin_url):
            return None

        # Extract and normalize location
        loc = normalize_optional_string(item.get("location") or item.get("jobLocation"))
        
        # Parse country from location if missing
        country_val = normalize_optional_string(item.get("country") or item.get("countryCode"))
        if not country_val and loc:
            parts = [p.strip() for p in loc.split(",") if p.strip()]
            if parts:
                last_part = parts[-1]
                # US states list (2-letter abbreviations)
                us_states = {
                    "AL", "AK", "AZ", "AR", "CA", "CO", "CT", "DE", "FL", "GA", "HI", "ID", "IL", "IN", "IA", "KS", "KY",
                    "LA", "ME", "MD", "MA", "MI", "MN", "MS", "MO", "MT", "NE", "NV", "NH", "NJ", "NM", "NY", "NC", "ND",
                    "OH", "OK", "OR", "PA", "RI", "SC", "SD", "TN", "TX", "UT", "VT", "VA", "WA", "WV", "WI", "WY"
                }
                if last_part.upper() in us_states or last_part.lower() == "usa":
                    country_val = "United States"
                else:
                    country_val = last_part

        # Parse workplace_type from location
        wp_type = normalize_optional_string(item.get("workplaceType") or item.get("workplace_type"))
        if not wp_type and loc:
            loc_lower = loc.lower()
            if "remote" in loc_lower:
                wp_type = "REMOTE"
            elif "hybrid" in loc_lower:
                wp_type = "HYBRID"
            else:
                wp_type = "ONSITE"
        elif not wp_type:
            wp_type = "ONSITE"

        # Parse easy_apply from applyType
        easy_app = self._normalize_bool(item.get("easyApply") or item.get("easy_apply"))
        if easy_app is None:
            easy_app = (item.get("applyType") == "EASY_APPLY")

        raw_json = dict(item)
        return LinkedInJob(
            job_title=normalize_optional_string(item.get("title") or item.get("jobTitle") or item.get("job_title")),
            company_name=normalize_optional_string(item.get("companyName") or item.get("company_name") or item.get("company")),
            company_url=normalize_optional_string(item.get("companyUrl") or item.get("company_url")),
            linkedin_job_url=linkedin_url,
            job_id=normalize_optional_string(item.get("jobId") or item.get("job_id") or item.get("id")),
            location=loc,
            country=country_val,
            workplace_type=wp_type,
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
            easy_apply=easy_app,
            posted_date=normalize_date(item.get("postedDate") or item.get("posted_date") or item.get("postedAt")),
            scraped_timestamp=datetime.now(timezone.utc),
            apify_run_id=run_id,
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

class PostScraper:
    """Scraper that calls the Apify LinkedIn Post Actor and extracts HIRING_POSTs."""

    def __init__(self, client: ApifyClient | None = None) -> None:
        self.client = client or ApifyClient()
        self.last_run_raw_count: int = 0
        self.last_run_validated_count: int = 0
        self.last_run_duplicate_count: int = 0
        self.last_run_unique_count: int = 0

    def fetch_posts(self, request: JobSearchRequest | None = None, **filters: Any) -> list[LinkedInJob]:
        self.last_run_raw_count = 0
        self.last_run_validated_count = 0
        self.last_run_duplicate_count = 0
        self.last_run_unique_count = 0

        # Build generic search query from request.
        # For posts, keep the query broad to catch more results, filtering happens after fetching.
        query_parts = []
        if request:
            if request.keyword: query_parts.append(request.keyword)
            if request.company: query_parts.append(request.company)
            # We explicitly do NOT append location, remote, hybrid, etc. to the query string 
            # because human-written posts might not contain these exact words, 
            # and it will cause LinkedIn to return 0 results.
            
        # Always append a hiring keyword to narrow down LinkedIn posts to actual job opportunities
        query_parts.append("hiring")
        query = " ".join(query_parts)
        
        input_data = {
            "keywords": [query], 
            "max_posts": max(10, request.max_results if request else 10)
        }

        raw_items, run_id = self.client.run_actor(input_data, timeout=300)

        jobs: list[LinkedInJob] = []
        for item in raw_items:
            job = self._normalize_post_item(item, run_id)
            if job is not None:
                # Apply strict date filtering since actor cannot filter by date natively
                if request and request.date_posted and job.posted_date:
                    now_utc = datetime.now(timezone.utc)
                    job_dt = job.posted_date
                    if job_dt.tzinfo is None:
                        job_dt = job_dt.replace(tzinfo=timezone.utc)
                    delta = (now_utc - job_dt).total_seconds()
                    
                    if request.date_posted == "past-24h" and delta > 86400:
                        continue
                    if request.date_posted == "past-week" and delta > 604800:
                        continue
                    if request.date_posted == "past-month" and delta > 2592000:
                        continue

                post_text_lower = (job.post_text or "").lower()

                # Apply exact company matching if requested
                if request and request.company:
                    req_company = request.company.lower()
                    if job.company_name and job.company_name != "Unknown Company":
                        if req_company not in job.company_name.lower():
                            continue
                    else:
                        if req_company not in post_text_lower:
                            continue

                # Apply workplace type if requested (only if explicitly parsed)
                if request and (request.remote or request.hybrid or request.onsite):
                    has_match = False
                    if request.remote and ("remote" in post_text_lower or "work from home" in post_text_lower or "wfh" in post_text_lower): has_match = True
                    if request.hybrid and "hybrid" in post_text_lower: has_match = True
                    if request.onsite and ("onsite" in post_text_lower or "on-site" in post_text_lower or "office" in post_text_lower): has_match = True
                    
                    if not has_match:
                        continue
                
                # Apply employment type if requested
                if request and request.employment_type:
                    emp_type = request.employment_type.lower()
                    if emp_type == "full-time" and ("full-time" not in post_text_lower and "full time" not in post_text_lower): continue
                    if emp_type == "part-time" and ("part-time" not in post_text_lower and "part time" not in post_text_lower): continue
                    if emp_type == "contract" and "contract" not in post_text_lower: continue

                jobs.append(job)

        # Duplicate detection and validation
        validated_jobs = validate_jobs(jobs)
        unique_jobs = remove_duplicates(validated_jobs)

        self.last_run_raw_count = len(raw_items)
        self.last_run_validated_count = len(validated_jobs)
        self.last_run_duplicate_count = len(validated_jobs) - len(unique_jobs)
        self.last_run_unique_count = len(unique_jobs)

        logger.info(f"Post Scrape metrics: total={len(validated_jobs)} unique={len(unique_jobs)}")
        return unique_jobs

    def _normalize_post_item(self, item: dict[str, Any], run_id: str | None = None) -> LinkedInJob | None:
        if not isinstance(item, dict):
            return None

        # Handle post text
        post_text = item.get("text")
        if not post_text and isinstance(item.get("content"), dict):
            post_text = item["content"].get("text")
        if not post_text:
            return None
            
        post_url = item.get("post_url") or item.get("url") or item.get("link")
        if not post_url or not is_valid_url(post_url):
            return None

        # Call parser
        parsed = parse_post(post_text)
        if not parsed.get("is_hiring_post"):
            return None

        author_data = item.get("author", {})
        author_name = author_data.get("name") or item.get("owner_name") or "LinkedIn User"
        author_profile_url = author_data.get("profile_url") or item.get("owner_profile_picture")
        author_role = author_data.get("headline") or ""
        
        posted_at_data = item.get("posted_at", {})
        posted_date_raw = posted_at_data.get("timestamp") or item.get("timestamp") or posted_at_data.get("date")

        raw_json = dict(item)
        return LinkedInJob(
            job_title=parsed.get("job_title"),
            company_name=parsed.get("company_name"),  # Do NOT assume author name is company name
            linkedin_job_url=post_url, # Use post URL as unique identifier in DB
            source_type="LINKEDIN_HIRING_POST",
            post_url=post_url,
            post_text=post_text,
            post_author_name=author_name,
            post_author_profile_url=author_profile_url,
            post_author_role=author_role,
            application_method=parsed.get("application_method"),
            application_methods=parsed.get("application_methods"),
            application_email=parsed.get("application_email"),
            application_platform=parsed.get("application_platform"),
            application_url=parsed.get("application_url"),
            posted_date=normalize_date(posted_date_raw),
            scraped_timestamp=datetime.now(timezone.utc),
            apify_run_id=run_id,
            raw_json=raw_json,
        )
