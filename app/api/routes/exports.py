import os
from pathlib import Path
from fastapi import APIRouter
from fastapi.responses import FileResponse
from app.exporter import ExportService

router = APIRouter()


@router.get("/export/csv")
async def export_csv():
    export_dir = Path("/tmp/data/csv")
    export_dir.mkdir(parents=True, exist_ok=True)
    temp_path = export_dir / "jobs_export.csv"

    service = ExportService()
    service.export_csv(temp_path)

    return FileResponse(
        path=temp_path,
        media_type="text/csv",
        filename="linkedin_jobs.csv"
    )


@router.get("/export/excel")
async def export_excel():
    export_dir = Path("/tmp/data/excel")
    export_dir.mkdir(parents=True, exist_ok=True)
    temp_path = export_dir / "jobs_export.xlsx"

    service = ExportService()
    service.export_excel(temp_path)

    return FileResponse(
        path=temp_path,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        filename="linkedin_jobs.xlsx"
    )


@router.get("/export/json")
async def export_json():
    export_dir = Path("/tmp/data/json")
    export_dir.mkdir(parents=True, exist_ok=True)
    temp_path = export_dir / "jobs_export.json"

    service = ExportService()
    service.export_json(temp_path)

    return FileResponse(
        path=temp_path,
        media_type="application/json",
        filename="linkedin_jobs.json"
    )
