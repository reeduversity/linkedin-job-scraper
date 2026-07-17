from fastapi import APIRouter
from app.repository import JobRepository
from app.schemas.responses import StandardResponse

router = APIRouter()


@router.get("/statistics", response_model=StandardResponse)
async def get_statistics():
    repository = JobRepository()
    stats = repository.get_statistics()
    return StandardResponse(
        success=True,
        message="Statistics retrieved successfully",
        data=stats
    )
