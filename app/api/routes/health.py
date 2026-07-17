from datetime import datetime, timezone
from fastapi import APIRouter
import app.config_validator as config_validator
from app.schemas.responses import StandardResponse

router = APIRouter()


@router.get("/health", response_model=StandardResponse)
async def get_health():
    db_status = "healthy"
    try:
        config_validator.load_environment()
        env_values = config_validator.validate_required_env()
        config = config_validator.build_config(env_values)
        config_validator.verify_postgres_connection(
            config.postgres_host,
            config.postgres_port,
            config.postgres_db,
            config.postgres_user,
            config.postgres_password,
        )
    except Exception:
        db_status = "unhealthy"


    scheduler_status = "unhealthy"
    try:
        from app.main_api import global_scheduler
        if global_scheduler and global_scheduler._scheduler.running:
            scheduler_status = "healthy"
        else:
            scheduler_status = "stopped"
    except Exception:
        pass

    health_data = {
        "status": "healthy" if db_status == "healthy" else "degraded",
        "database": db_status,
        "scheduler": scheduler_status,
        "version": "1.0.0",
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }

    return StandardResponse(
        success=True,
        message="Health status retrieved successfully",
        data=health_data
    )
