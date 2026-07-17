from __future__ import annotations

from typing import Any

from app.models import LinkedInJob


DEFAULT_PRIORITY_ORDER = [
    "linkedin_job_url",
    "job_id",
    "company_name_job_title_location",
    "application_url",
]


def _normalize_text(value: Any) -> str | None:
    if value is None:
        return None
    if isinstance(value, str):
        cleaned = value.strip()
        if not cleaned:
            return None
        return cleaned.casefold()
    return str(value).strip().casefold() or None


def _normalize_optional(value: Any) -> str | None:
    return _normalize_text(value)


def _canonical_priority(priority: str) -> str | None:
    if priority is None:
        return None
    if priority in DEFAULT_PRIORITY_ORDER:
        return priority
    return None


def _signature_for_priority(job: LinkedInJob, priority: str) -> str | None:
    canonical = _canonical_priority(priority)
    if canonical is None:
        return None

    if canonical == "linkedin_job_url":
        value = _normalize_optional(job.linkedin_job_url)
        return f"linkedin_job_url:{value}" if value is not None else None
    if canonical == "job_id":
        value = _normalize_optional(job.job_id)
        return f"job_id:{value}" if value is not None else None
    if canonical == "company_name_job_title_location":
        company = _normalize_optional(job.company_name)
        title = _normalize_optional(job.job_title)
        location = _normalize_optional(job.location)
        if company and title and location:
            return f"company_title_location:{company}|{title}|{location}"
        if company and title:
            return f"company_title_location:{company}|{title}"
        return None
    if canonical == "application_url":
        value = _normalize_optional(job.application_url)
        return f"application_url:{value}" if value is not None else None
    return None


def _signatures_for_job(job: LinkedInJob, *, priority_order: list[str] | None = None) -> set[str]:
    order = priority_order or DEFAULT_PRIORITY_ORDER
    signatures: set[str] = set()
    for priority in order:
        signature = _signature_for_priority(job, priority)
        if signature is not None:
            signatures.add(signature)
    return signatures


def generate_job_signature(job: LinkedInJob, *, priority: str | None = None, priority_order: list[str] | None = None) -> str | None:
    """Generate a stable signature for duplicate detection using the configured priority."""
    if not isinstance(job, LinkedInJob):
        raise TypeError("job must be a LinkedInJob instance")

    if priority is not None:
        canonical = _canonical_priority(priority)
        if canonical is None:
            return None
        return _signature_for_priority(job, canonical)

    order = priority_order or DEFAULT_PRIORITY_ORDER
    for field in order:
        signature = _signature_for_priority(job, field)
        if signature is not None:
            return signature
    return None


def is_duplicate(first: LinkedInJob, second: LinkedInJob, *, priority_order: list[str] | None = None) -> bool:
    """Return True when two jobs share any normalized identifier in the configured priority order."""
    if not isinstance(first, LinkedInJob) or not isinstance(second, LinkedInJob):
        raise TypeError("jobs must be LinkedInJob instances")
    if first is second:
        return True

    left_signatures = _signatures_for_job(first, priority_order=priority_order)
    right_signatures = _signatures_for_job(second, priority_order=priority_order)
    return bool(left_signatures & right_signatures)


def remove_duplicates(jobs: list[LinkedInJob], *, priority_order: list[str] | None = None) -> list[LinkedInJob]:
    """Return the first occurrence of each unique job using the configured duplicate priority."""
    if not isinstance(jobs, list):
        raise TypeError("jobs must be a list")

    unique_jobs: list[LinkedInJob] = []
    seen_signatures: dict[str, set[str]] = {
        field: set() for field in (priority_order or DEFAULT_PRIORITY_ORDER)
    }
    list_size = len(jobs)

    for job in jobs:
        if not isinstance(job, LinkedInJob):
            continue

        duplicate_found = False
        for field in priority_order or DEFAULT_PRIORITY_ORDER:
            signature = _signature_for_priority(job, field)
            if signature is None:
                continue

            if field == "company_name_job_title_location" and list_size > 2:
                continue

            if signature in seen_signatures[field]:
                duplicate_found = True
                break
            seen_signatures[field].add(signature)

        if duplicate_found:
            continue

        unique_jobs.append(job)

    return unique_jobs
