from __future__ import annotations

from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator


class JobSearchRequest(BaseModel):
    """Filters used to request jobs from the Apify LinkedIn jobs actor."""

    keyword: str | None = None
    location: str | None = None
    country: str | None = None
    remote: bool | None = None
    hybrid: bool | None = None
    onsite: bool | None = None
    employment_type: str | None = None
    experience_level: str | None = None
    company: str | None = None
    date_posted: str | None = None
    max_results: int | None = Field(default=None, ge=1)

    def to_actor_input(self) -> dict[str, Any]:
        # Apify actor expects `input.remote` to be an ARRAY of workplace type enums.
        # Our public API still uses boolean flags, so convert them to the actor format.
        # Apify actor expects `input.remote` as an ARRAY of enum codes as strings: "1", "2", "3"
        # Mapping contract (verified):
        #   onsite=true  -> ["1"]
        #   remote=true  -> ["2"]
        #   hybrid=true  -> ["3"]
        workplace_types: list[str] = []
        if self.remote:
            workplace_types.append("2")
        if self.hybrid:
            workplace_types.append("3")
        if self.onsite:
            workplace_types.append("1")

        # Map experience_level to Apify's expected enum codes
        experience_map = {
            "Internship": "1",
            "Entry level": "2",
            "Associate": "3",
            "Mid-Senior level": "4",
            "Director": "5",
            "Executive": "6"
        }
        exp_levels = []
        if self.experience_level:
            mapped = experience_map.get(self.experience_level)
            if mapped:
                exp_levels.append(mapped)

        # Combine location and country for the actor, as it usually only takes a single location string.
        combined_location = self.location or ""
        if self.country:
            combined_location = f"{combined_location}, {self.country}" if combined_location else self.country

        # Map date_posted to Apify's expected enum codes
        date_map = {
            "past-24h": "r86400",
            "past-week": "r604800",
            "past-month": "r2592000",
        }
        mapped_date = date_map.get(self.date_posted) if self.date_posted else None

        # Apify expects employmentType to be an array of strings
        emp_types = [self.employment_type] if self.employment_type else None

        payload = {
            "searchKeywords": self.keyword,
            "location": combined_location or None,
            "remote": workplace_types or None,  # actor schema: array
            "employmentType": emp_types,
            "experienceLevel": exp_levels or None,
            "datePosted": mapped_date,
            "company": self.company,
            "maxResults": self.max_results,
        }
        return {key: value for key, value in payload.items() if value is not None}


class LinkedInJob(BaseModel):
    """Normalized LinkedIn job payload returned by the collection layer."""

    job_title: str | None = None
    company_name: str | None = None
    company_url: str | None = None
    linkedin_job_url: str = Field(...)
    job_id: str | None = None
    
    # HIRING_POST specific fields
    source_type: str = "LINKEDIN_JOB"
    post_url: str | None = None
    post_text: str | None = None
    post_author_name: str | None = None
    post_author_profile_url: str | None = None
    post_author_role: str | None = None
    poster_designation: str | None = None
    poster_role_category: str | None = None
    application_method: str | None = None
    application_methods: list[str] | None = None
    application_email: str | None = None
    application_emails: list[str] | None = None
    application_platform: str | None = None
    application_urls: list[str] | None = None
    application_form_url: str | None = None
    application_url_type: str | None = None
    # Hiring detection
    hiring_confidence_score: float | None = None
    detection_method: str | None = None
    extraction_method: str | None = None
    extraction_quality: str | None = None
    # OCR fields
    image_url: str | None = None
    image_urls: list[str] | None = None
    ocr_text: str | None = None
    ocr_confidence: float | None = None
    ocr_processed: bool | None = None
    ocr_extraction_status: str | None = None
    # Hashtags
    hashtags: list[str] | None = None
    location: str | None = None
    country: str | None = None
    workplace_type: str | None = None
    employment_type: str | None = None
    experience_level: str | None = None
    salary: str | None = None
    currency: str | None = None
    description: str | None = None
    job_summary: str | None = None
    skills: list[str] | None = None
    industry: str | None = None
    benefits: str | None = None
    recruiter: str | None = None
    recruiter_url: str | None = None
    company_logo: str | None = None
    company_size: str | None = None
    application_url: str | None = None
    easy_apply: bool | None = None
    posted_date: datetime | None = None
    scraped_timestamp: datetime | None = None
    apify_run_id: str | None = None
    raw_json: dict[str, Any] = Field(default_factory=dict)

    @field_validator("job_title", "company_name", "location", "country", "workplace_type", "employment_type", "experience_level", "salary", "currency", "description", "job_summary", "industry", "benefits", "recruiter", "recruiter_url", "company_logo", "company_size", "application_url", "apify_run_id", "source_type", "post_text", "post_author_name", "post_author_role", "poster_designation", "poster_role_category", "application_method", "application_email", "application_platform", "application_form_url", "application_url_type", "detection_method", "extraction_method", "extraction_quality", "image_url", "ocr_text", "ocr_extraction_status", mode="before")
    @classmethod
    def normalize_optional_string(cls, value: Any) -> str | None:
        if value is None:
            return None
        if isinstance(value, str):
            cleaned = value.strip()
            return cleaned or None
        return str(value)

    @field_validator("linkedin_job_url", "company_url", "application_url", "recruiter_url", "post_url", "post_author_profile_url", "application_form_url", mode="before")
    @classmethod
    def validate_url(cls, value: Any) -> str | None:
        if value is None:
            return None
        if isinstance(value, str):
            cleaned = value.strip()
            if not cleaned:
                return None
            return cleaned
        return str(value)

    @field_validator("skills", "application_methods", "application_emails", "application_urls", "image_urls", "hashtags", mode="before")
    @classmethod
    def normalize_skills(cls, value: Any) -> list[str] | None:
        if value is None:
            return None
        if isinstance(value, str):
            items = [item.strip() for item in value.split(",") if item.strip()]
            return list(dict.fromkeys(items)) or None
        if isinstance(value, list):
            return list(dict.fromkeys(str(item).strip() for item in value if str(item).strip())) or None
        return None

    @field_validator("easy_apply", mode="before")
    @classmethod
    def normalize_easy_apply(cls, value: Any) -> bool | None:
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


class ActorResponse(BaseModel):
    """Envelope returned by the Apify actor run."""

    model_config = ConfigDict(arbitrary_types_allowed=True)

    jobs: list[LinkedInJob] = Field(default_factory=list)
    response_time_seconds: float | None = None

    @field_validator("jobs", mode="before")
    @classmethod
    def normalize_jobs(cls, value: Any) -> list[dict[str, Any]] | list[LinkedInJob]:
        if value is None:
            return []
        if isinstance(value, dict):
            return [value]
        if isinstance(value, list):
            return value
        return []

    @model_validator(mode="before")
    @classmethod
    def coerce_job_dicts(cls, value: Any) -> Any:
        if isinstance(value, dict):
            jobs = value.get("jobs")
            if isinstance(jobs, list):
                normalized_jobs: list[dict[str, Any]] = []
                for job in jobs:
                    if isinstance(job, dict):
                        if "linkedin_job_url" not in job and "linkedinJobUrl" in job:
                            job = {**job, "linkedin_job_url": job["linkedinJobUrl"]}
                        normalized_jobs.append(job)
                value = {**value, "jobs": normalized_jobs}
        return value


class Job(LinkedInJob):
    """Backward-compatible alias for the job model."""
