import argparse
from datetime import datetime, timezone
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import settings
from app.scheduler import JobScheduler
from main import run_pipeline

# 1. Initialize stats dict and global scheduler instance
global_scheduler_stats = {
    "jobs_executed": 0,
    "last_run": None
}

global_scheduler = JobScheduler()

# Register event listener to count job runs
from apscheduler.events import EVENT_JOB_EXECUTED, EVENT_JOB_ERROR


def scheduler_listener(event):
    global_scheduler_stats["jobs_executed"] += 1
    global_scheduler_stats["last_run"] = datetime.now(timezone.utc)


global_scheduler._scheduler.add_listener(
    scheduler_listener,
    EVENT_JOB_EXECUTED | EVENT_JOB_ERROR
)

# Register default scraping job using interval from settings
default_args = argparse.Namespace(
    keywords=None,
    location=None,
    limit=None,
    remote=None,
    hybrid=None,
    onsite=None,
    days=None,
    experience=None,
    company=None,
    schedule=True,
    interval=None,
    run_once=False,
    stats=False,
    export=None,
    output=None
)
global_scheduler.register_job(
    run_pipeline,
    default_args,
    interval_minutes=settings.scraper_interval_minutes
)

# 2. Import routes (imported after initializing global variables)
from app.api.routes import health, jobs, statistics, exports, scheduler

# 3. Create FastAPI application
app = FastAPI(
    title="LinkedIn Job Scraper REST API",
    description="Production-ready REST API for the LinkedIn Job Scraper backend.",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json"
)

# 4. Configure CORS
origins = [
    "http://localhost:3000",
    "http://127.0.0.1:3000",
]
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 5. Configure custom middlewares
from app.middleware.timing import TimingMiddleware
from app.middleware.logging import APILoggingMiddleware

app.add_middleware(TimingMiddleware)
app.add_middleware(APILoggingMiddleware)

# 6. Configure global exception handlers
from app.middleware.exception_handler import setup_exception_handlers
setup_exception_handlers(app)

# 7. Register routers
app.include_router(health.router, prefix="/api", tags=["health"])
app.include_router(jobs.router, prefix="/api", tags=["jobs"])
app.include_router(statistics.router, prefix="/api", tags=["statistics"])
app.include_router(exports.router, prefix="/api", tags=["exports"])
app.include_router(scheduler.router, prefix="/api", tags=["scheduler"])


@app.on_event("startup")
def startup_event():
    # Only start background scheduler if configured as enabled
    if settings.scraper_enabled:
        global_scheduler.start()


@app.on_event("shutdown")
def shutdown_event():
    if global_scheduler._scheduler.running:
        global_scheduler.stop()
