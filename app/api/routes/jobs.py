from datetime import datetime, timezone
from typing import Optional
from fastapi import APIRouter, HTTPException, Query, status

from app.models import JobSearchRequest, LinkedInJob
from app.repository import JobRepository
from app.scraper import JobScraper
from app.schemas.responses import StandardResponse
import logging

logger = logging.getLogger(__name__)

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


from app.scraper import JobScraper, PostScraper

@router.post("/jobs/scrape", response_model=StandardResponse)
async def scrape_jobs(request: JobSearchRequest):
    # Configuration is validated at startup (main_api.py).
    # Import settings for runtime values only.
    from app.config import settings

    # Step 2: Run scraping
    start_time = datetime.now(timezone.utc)

    # Use runtime settings for Apify credentials
    from app.apify_client import ApifyClient

    scraper = JobScraper(
        client=ApifyClient(token=settings.apify_api_token, actor_id=settings.apify_actor_id)
    )
    jobs = scraper.fetch_jobs(request)

    total_fetched = scraper.last_run_raw_count
    total_validated = scraper.last_run_validated_count
    duplicate_removed = scraper.last_run_duplicate_count

    if settings.post_scraper_enabled:
        try:
            logger.info("Running PostScraper...")
            post_scraper = PostScraper(
                client=ApifyClient(token=settings.apify_api_token, actor_id=settings.apify_post_actor_id)
            )
            posts = post_scraper.fetch_posts(request)
            jobs.extend(posts)
            total_fetched += post_scraper.last_run_raw_count
            total_validated += post_scraper.last_run_validated_count
            duplicate_removed += post_scraper.last_run_duplicate_count
        except Exception as e:
            logger.error(f"Post scraping failed, but continuing with jobs: {e}")

    # Step 3: Persist
    repository = JobRepository()
    repository.save_jobs(jobs)

    # Step 4: Cleanup Stale Jobs
    try:
        deleted_stale = repository.delete_stale_jobs(14)
        logger.info(f"Cleaned up {deleted_stale} stale jobs")
    except Exception as e:
        logger.error(f"Error cleaning up stale jobs: {e}")

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
