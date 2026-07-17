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
        # Mapping contract (per verified error message and your instruction):
        #   remote=true  -> ["1"]
        #   hybrid=true  -> ["2"]
        #   onsite=true  -> ["3"]
        workplace_types: list[str] = []
        if self.remote:
            workplace_types.append("1")
        if self.hybrid:
            workplace_types.append("2")
        if self.onsite:
            workplace_types.append("3")

        payload = {
            "searchKeywords": self.keyword,
            "location": self.location,
            "country": self.country,
            "remote": workplace_types or None,  # actor schema: array
            "employmentType": self.employment_type,
            "experienceLevel": self.experience_level,
            "datePosted": self.date_posted,
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
    raw_json: dict[str, Any] = Field(default_factory=dict)

    @field_validator("job_title", "company_name", "location", "country", "workplace_type", "employment_type", "experience_level", "salary", "currency", "description", "job_summary", "industry", "benefits", "recruiter", "recruiter_url", "company_logo", "company_size", "application_url", mode="before")
    @classmethod
    def normalize_optional_string(cls, value: Any) -> str | None:
        if value is None:
            return None
        if isinstance(value, str):
            cleaned = value.strip()
            return cleaned or None
        return str(value)

    @field_validator("linkedin_job_url", "company_url", "application_url", "recruiter_url", mode="before")
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

    @field_validator("skills", mode="before")
    @classmethod
    def normalize_skills(cls, value: Any) -> list[str] | None:
        if value is None:
            return None
        if isinstance(value, str):
            items = [item.strip() for item in value.split(",") if item.strip()]
            return list(dict.fromkeys(items))
        if isinstance(value, list):
            return list(dict.fromkeys(str(item).strip() for item in value if str(item).strip()))
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
