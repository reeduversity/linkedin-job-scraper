from __future__ import annotations

from datetime import datetime, timezone
from typing import Any
from urllib.parse import urlparse

from pydantic import ValidationError as PydanticValidationError

from app.models import Job, LinkedInJob
from app.utils import normalize_date, normalize_optional_string, normalize_salary


class ValidationError(ValueError):
    """Raised when a job record fails validation."""


def _normalize_text(value: Any) -> str | None:
    if value is None:
        return None
    if isinstance(value, str):
        cleaned = value.strip()
        return cleaned or None
    return str(value)


def _normalize_currency(value: Any) -> str | None:
    if value is None:
        return None
    if isinstance(value, str):
        cleaned = value.strip().upper()
        return cleaned or None
    return None


def _normalize_workplace_type(value: Any) -> str | None:
    if value is None:
        return None
    normalized = _normalize_text(value)
    if normalized is None:
        return None
    mapping = {
        "remote": "REMOTE",
        "hybrid": "HYBRID",
        "onsite": "ONSITE",
        "on-site": "ONSITE",
        "office": "ONSITE",
        "in-person": "ONSITE",
    }
    return mapping.get(normalized.lower(), normalized.upper())


def _normalize_employment_type(value: Any) -> str | None:
    if value is None:
        return None
    normalized = _normalize_text(value)
    if normalized is None:
        return None
    mapping = {
        "full-time": "FULL_TIME",
        "full time": "FULL_TIME",
        "part-time": "PART_TIME",
        "part time": "PART_TIME",
        "contract": "CONTRACT",
        "temporary": "TEMPORARY",
        "internship": "INTERNSHIP",
        "freelance": "FREELANCE",
        "volunteer": "VOLUNTEER",
    }
    return mapping.get(normalized.lower(), normalized.upper().replace("-", "_"))


def _normalize_experience_level(value: Any) -> str | None:
    if value is None:
        return None
    normalized = _normalize_text(value)
    if normalized is None:
        return None
    mapping = {
        "entry level": "ENTRY_LEVEL",
        "entry-level": "ENTRY_LEVEL",
        "mid level": "MID_LEVEL",
        "mid-level": "MID_LEVEL",
        "senior": "SENIOR",
        "lead": "LEAD",
        "manager": "MANAGER",
        "director": "DIRECTOR",
    }
    return mapping.get(normalized.lower(), normalized.upper().replace("-", "_"))


def _normalize_skills(value: Any) -> list[str] | None:
    if value is None:
        return None
    if isinstance(value, str):
        items = [item.strip() for item in value.split(",") if item.strip()]
    elif isinstance(value, list):
        items = [str(item).strip() for item in value if str(item).strip()]
    else:
        return None
    return list(dict.fromkeys(items))


def _is_valid_url(value: Any) -> bool:
    if value is None:
        return False
    if not isinstance(value, str):
        return False
    cleaned = value.strip()
    if not cleaned:
        return False
    parsed = urlparse(cleaned)
    return parsed.scheme in {"http", "https"} and bool(parsed.netloc)


def _coerce_payload(payload: Any) -> dict[str, Any]:
    if isinstance(payload, dict):
        data = dict(payload)
    elif isinstance(payload, (LinkedInJob, Job)):
        data = payload.model_dump(exclude_none=False)
    else:
        raise ValidationError("Job must be a mapping, LinkedInJob, or Job instance")

    if "linkedin_job_url" not in data and "linkedinJobUrl" in data:
        data["linkedin_job_url"] = data["linkedinJobUrl"]
    if "company_name" not in data and "companyName" in data:
        data["company_name"] = data["companyName"]
    if "job_title" not in data and "title" in data:
        data["job_title"] = data["title"]
    if "company_url" not in data and "companyUrl" in data:
        data["company_url"] = data["companyUrl"]
    if "application_url" not in data and "applicationUrl" in data:
        data["application_url"] = data["applicationUrl"]
    if "job_id" not in data and "jobId" in data:
        data["job_id"] = data["jobId"]
    if "workplace_type" not in data and "workplaceType" in data:
        data["workplace_type"] = data["workplaceType"]
    if "employment_type" not in data and "employmentType" in data:
        data["employment_type"] = data["employmentType"]
    if "experience_level" not in data and "experienceLevel" in data:
        data["experience_level"] = data["experienceLevel"]
    if "posted_date" not in data and "postedDate" in data:
        data["posted_date"] = data["postedDate"]
    if "company_size" not in data and "companySize" in data:
        data["company_size"] = data["companySize"]
    if "company_logo" not in data and "companyLogo" in data:
        data["company_logo"] = data["companyLogo"]
    if "recruiter_url" not in data and "recruiterUrl" in data:
        data["recruiter_url"] = data["recruiterUrl"]
    if "easy_apply" not in data and "easyApply" in data:
        data["easy_apply"] = data["easyApply"]
    if "job_summary" not in data and "jobSummary" in data:
        data["job_summary"] = data["jobSummary"]
    if "raw_json" not in data:
        data["raw_json"] = {}
    return data


def validate_job(job: LinkedInJob | Job | dict[str, Any]) -> LinkedInJob:
    """Validate and normalize a job payload before storage or export."""
    payload = _coerce_payload(job)

    try:
        parsed = LinkedInJob.model_validate(payload)
    except PydanticValidationError as exc:
        raise ValidationError(f"Pydantic validation failed: {exc}") from exc

    data = parsed.model_dump(exclude_none=False)

    title = _normalize_text(data.get("job_title"))
    company = _normalize_text(data.get("company_name"))
    linkedin_url = _normalize_text(data.get("linkedin_job_url"))
    company_url = _normalize_text(data.get("company_url"))
    application_url = _normalize_text(data.get("application_url"))

    if not title:
        raise ValidationError("job_title is required")
    if not company:
        raise ValidationError("company_name is required")
    if not linkedin_url or not _is_valid_url(linkedin_url):
        raise ValidationError("linkedin_job_url is invalid")
    if company_url is not None and not _is_valid_url(company_url):
        raise ValidationError("company_url is invalid")
    if application_url is not None and not _is_valid_url(application_url):
        raise ValidationError("application_url is invalid")

    return LinkedInJob(
        job_title=title,
        company_name=company,
        company_url=company_url,
        linkedin_job_url=linkedin_url,
        job_id=_normalize_text(data.get("job_id")),
        location=_normalize_text(data.get("location")),
        country=_normalize_text(data.get("country")),
        workplace_type=_normalize_workplace_type(data.get("workplace_type")),
        employment_type=_normalize_employment_type(data.get("employment_type")),
        experience_level=_normalize_experience_level(data.get("experience_level")),
        salary=normalize_salary(data.get("salary")),
        currency=_normalize_currency(data.get("currency")),
        description=_normalize_text(data.get("description")),
        job_summary=_normalize_text(data.get("job_summary")),
        skills=_normalize_skills(data.get("skills")),
        industry=_normalize_text(data.get("industry")),
        benefits=_normalize_text(data.get("benefits")),
        recruiter=_normalize_text(data.get("recruiter")),
        recruiter_url=_normalize_text(data.get("recruiter_url")),
        company_logo=_normalize_text(data.get("company_logo")),
        company_size=_normalize_text(data.get("company_size")),
        application_url=application_url,
        easy_apply=data.get("easy_apply"),
        posted_date=normalize_date(data.get("posted_date")),
        scraped_timestamp=data.get("scraped_timestamp") or datetime.now(timezone.utc),
        apify_run_id=_normalize_text(data.get("apify_run_id")),
        source_type=_normalize_text(data.get("source_type")) or "JOB_LISTING",
        post_url=_normalize_text(data.get("post_url")),
        post_text=_normalize_text(data.get("post_text")),
        post_author_name=_normalize_text(data.get("post_author_name")),
        post_author_profile_url=_normalize_text(data.get("post_author_profile_url")),
        post_author_role=_normalize_text(data.get("post_author_role")),
        application_method=_normalize_text(data.get("application_method")),
        application_methods=data.get("application_methods"),
        application_email=_normalize_text(data.get("application_email")),
        application_platform=_normalize_text(data.get("application_platform")),
        raw_json=data.get("raw_json") or {},
    )


def validate_jobs(jobs: list[LinkedInJob | Job | dict[str, Any]]) -> list[LinkedInJob]:
    """Validate a list of jobs and return only valid records."""
    validated: list[LinkedInJob] = []
    for job in jobs:
        try:
            validated.append(validate_job(job))
        except ValidationError:
            continue
    return validated
