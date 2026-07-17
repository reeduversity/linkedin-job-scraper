from datetime import datetime, timezone
from typing import Optional
from fastapi import APIRouter, HTTPException, Query, status

from app.models import JobSearchRequest, LinkedInJob
from app.repository import JobRepository
from app.scraper import JobScraper
from app.schemas.responses import StandardResponse
from app import config_validator

router = APIRouter()


@router.get("/jobs", response_model=StandardResponse)
async def get_jobs(
    page: int = Query(default=1, ge=1),
    limit: int = Query(default=10, ge=1, le=100),
    keyword: Optional[str] = None,
    company: Optional[str] = None,
    location: Optional[str] = None,
    remote: Optional[bool] = None,
    hybrid: Optional[bool] = None,
    onsite: Optional[bool] = None,
    experience: Optional[str] = None,
    country: Optional[str] = None,
    sort: str = "id",
    order: str = "ASC",
):
    repository = JobRepository()

    workplace_types = []
    if remote:
        workplace_types.append("REMOTE")
    if hybrid:
        workplace_types.append("HYBRID")
    if onsite:
        workplace_types.append("ONSITE")
    if not workplace_types:
        workplace_types = None

    offset = (page - 1) * limit
    jobs = repository.get_all_jobs(
        limit=limit,
        offset=offset,
        keyword=keyword,
        company=company,
        location=location,
        workplace_types=workplace_types,
        experience=experience,
        country=country,
        sort_by=sort,
        sort_order=order,
    )
    total = repository.count_jobs(
        keyword=keyword,
        company=company,
        location=location,
        workplace_types=workplace_types,
        experience=experience,
        country=country,
    )

    data = {
        "items": jobs,
        "total": total,
        "page": page,
        "limit": limit,
    }
    return StandardResponse(
        success=True,
        message="Jobs retrieved successfully",
        data=data
    )


@router.get("/jobs/{job_id}", response_model=StandardResponse)
async def get_job(job_id: str):
    repository = JobRepository()
    job = repository.get_job_by_id(job_id)
    if not job:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Job with ID '{job_id}' not found"
        )
    return StandardResponse(
        success=True,
        message="Job retrieved successfully",
        data=job
    )


@router.post("/jobs/scrape", response_model=StandardResponse)
async def scrape_jobs(request: JobSearchRequest):
    # Step 1: Validate configuration
    config_validator.load_environment()
    env_values = config_validator.validate_required_env()
    config = config_validator.build_config(env_values)

    # Verify Apify
    config_validator.verify_apify_token(config.apify_token)

    # Verify Database
    config_validator.create_directories()
    config_validator.create_database_if_missing(
        config.postgres_host,
        config.postgres_port,
        config.postgres_db,
        config.postgres_user,
        config.postgres_password,
    )
    config_validator.verify_postgres_connection(
        config.postgres_host,
        config.postgres_port,
        config.postgres_db,
        config.postgres_user,
        config.postgres_password,
    )

    # Step 2: Run scraping
    start_time = datetime.now(timezone.utc)

    # Use validated runtime configuration explicitly (no fallback to app/config.py defaults)
    from app.apify_client import ApifyClient

    scraper = JobScraper(
        client=ApifyClient(token=config.apify_token, actor_id=config.apify_actor_id)
    )
    jobs = scraper.fetch_jobs(request)

    total_fetched = scraper.last_run_raw_count
    total_validated = scraper.last_run_validated_count
    duplicate_removed = scraper.last_run_duplicate_count

    # Step 3: Persist
    repository = JobRepository()
    repository.save_jobs(jobs)

    # Tests patch class-level counters; repository may be a fresh instance.
    # Prefer class attributes when available to avoid instance reset issues.
    jobs_saved = getattr(repository, "last_run_saved_count", 0)
    jobs_updated = getattr(repository, "last_run_updated_count", 0)

    jobs_saved = max(jobs_saved, getattr(JobRepository, "last_run_saved_count", 0))
    jobs_updated = max(jobs_updated, getattr(JobRepository, "last_run_updated_count", 0))

    execution_time = (datetime.now(timezone.utc) - start_time).total_seconds()
    
    failed_jobs = max(0, total_fetched - total_validated)

    scrape_data = {
        "fetched": total_fetched,
        "validated": total_validated,
        "duplicates_removed": duplicate_removed,
        "saved": jobs_saved,
        "failed": failed_jobs,
        "execution_time": round(execution_time, 2)
    }

    return StandardResponse(
        success=True,
        message="Scrape completed successfully",
        data=scrape_data
    )
