from datetime import datetime
from fastapi import APIRouter, BackgroundTasks, status
from app.schemas.responses import StandardResponse

router = APIRouter()


@router.get("/scheduler/status", response_model=StandardResponse)
async def get_scheduler_status():
    from app.main_api import global_scheduler, global_scheduler_stats

    running = False
    interval = None
    next_run = None

    if global_scheduler:
        running = global_scheduler._scheduler.running
        job = global_scheduler._scheduler.get_job("scraping_job")
        if job:
            # APScheduler Job API differs across versions; keep this robust for tests.
            next_run = getattr(job, "next_run_time", None) or None
            # Some versions may expose run times via internal methods.
            if next_run is None:
                try:
                    times = job._get_run_times(start_time=None, end_time=None)  # type: ignore[attr-defined]
                    next_run = next(times, None)
                except Exception:
                    next_run = None

            if job.trigger and hasattr(job.trigger, "interval"):
                interval = int(job.trigger.interval.total_seconds() / 60)


    data = {
        "running": running,
        "interval": interval,
        "next_run": next_run.isoformat() if next_run else None,
        "jobs_executed": global_scheduler_stats["jobs_executed"],
        "last_run": global_scheduler_stats["last_run"].isoformat() if global_scheduler_stats["last_run"] else None,
    }
    return StandardResponse(
        success=True,
        message="Scheduler status retrieved successfully",
        data=data
    )


@router.post("/scheduler/start", response_model=StandardResponse)
async def start_scheduler():
    from app.main_api import global_scheduler
    if not global_scheduler:
        return StandardResponse(
            success=False,
            message="Scheduler not initialized",
            data={}
        )
    if not global_scheduler._scheduler.running:
        global_scheduler.start()
        message = "Scheduler started successfully"
    else:
        message = "Scheduler is already running"

    return StandardResponse(
        success=True,
        message=message,
        data={}
    )


@router.post("/scheduler/stop", response_model=StandardResponse)
async def stop_scheduler():
    from app.main_api import global_scheduler
    if not global_scheduler:
        return StandardResponse(
            success=False,
            message="Scheduler not initialized",
            data={}
        )
    if global_scheduler._scheduler.running:
        global_scheduler.stop()
        message = "Scheduler stopped successfully"
    else:
        message = "Scheduler is already stopped"

    return StandardResponse(
        success=True,
        message=message,
        data={}
    )


@router.post("/scheduler/run-once", response_model=StandardResponse)
async def run_scheduler_once(background_tasks: BackgroundTasks):
    import argparse
    from main import run_pipeline

    args = argparse.Namespace(
        keywords=None,
        location=None,
        limit=None,
        remote=None,
        hybrid=None,
        onsite=None,
        days=None,
        experience=None,
        company=None,
        schedule=False,
        interval=None,
        run_once=True,
        stats=False,
        export=None,
        output=None
    )

    background_tasks.add_task(run_pipeline, args)

    return StandardResponse(
        success=True,
        message="Scraping pipeline triggered successfully in the background",
        data={}
    )
