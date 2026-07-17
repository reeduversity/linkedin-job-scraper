import csv
import json
from pathlib import Path
from typing import Any

import openpyxl
from openpyxl.styles import Font

from app.models import LinkedInJob
from app.repository import JobRepository


class ExportService:
    """Production-ready data export service for LinkedIn job listings."""

    def __init__(self, repository: JobRepository | None = None) -> None:
        self.repository = repository or JobRepository()

    def get_statistics(self) -> dict[str, Any]:
        """Fetch job stats from the database."""
        return self.repository.get_statistics()

    def _prepare_data(self) -> list[dict[str, Any]]:
        """Fetch all jobs from the repository and normalize them for export."""
        jobs = self.repository.get_all_jobs()
        rows = []
        for job in jobs:
            rows.append({
                "job_title": job.job_title or "",
                "company_name": job.company_name or "",
                "company_url": job.company_url or "",
                "linkedin_job_url": job.linkedin_job_url or "",
                "job_id": job.job_id or "",
                "location": job.location or "",
                "country": job.country or "",
                "workplace_type": job.workplace_type or "",
                "employment_type": job.employment_type or "",
                "experience_level": job.experience_level or "",
                "salary": job.salary or "",
                "currency": job.currency or "",
                "description": job.description or "",
                "job_summary": job.job_summary or "",
                "skills": ", ".join(job.skills) if job.skills else "",
                "industry": job.industry or "",
                "benefits": job.benefits or "",
                "recruiter": job.recruiter or "",
                "recruiter_url": job.recruiter_url or "",
                "company_logo": job.company_logo or "",
                "company_size": job.company_size or "",
                "application_url": job.application_url or "",
                "easy_apply": str(job.easy_apply) if job.easy_apply is not None else "",
                "posted_date": job.posted_date.isoformat() if job.posted_date else "",
                "scraped_timestamp": job.scraped_timestamp.isoformat() if job.scraped_timestamp else "",
            })
        return rows

    def export_csv(self, path: str | Path) -> None:
        """Export stored jobs to CSV format."""
        path = Path(path)
        if not path.parent.exists():
            raise FileNotFoundError(f"Output directory does not exist: {path.parent}")

        rows = self._prepare_data()
        headers = [
            "job_title", "company_name", "company_url", "linkedin_job_url", "job_id",
            "location", "country", "workplace_type", "employment_type", "experience_level",
            "salary", "currency", "description", "job_summary", "skills", "industry",
            "benefits", "recruiter", "recruiter_url", "company_logo", "company_size",
            "application_url", "easy_apply", "posted_date", "scraped_timestamp"
        ]

        try:
            with open(path, mode="w", newline="", encoding="utf-8") as f:
                writer = csv.DictWriter(f, fieldnames=headers)
                writer.writeheader()
                for row in rows:
                    writer.writerow({k: v for k, v in row.items() if k in headers})
        except PermissionError as exc:
            raise PermissionError(f"Permission denied to write CSV file: {path}") from exc

    def export_excel(self, path: str | Path) -> None:
        """Export stored jobs to Excel format (.xlsx)."""
        path = Path(path)
        if not path.parent.exists():
            raise FileNotFoundError(f"Output directory does not exist: {path.parent}")

        rows = self._prepare_data()
        headers = [
            "job_title", "company_name", "company_url", "linkedin_job_url", "job_id",
            "location", "country", "workplace_type", "employment_type", "experience_level",
            "salary", "currency", "description", "job_summary", "skills", "industry",
            "benefits", "recruiter", "recruiter_url", "company_logo", "company_size",
            "application_url", "easy_apply", "posted_date", "scraped_timestamp"
        ]

        wb = openpyxl.Workbook()
        ws = wb.active
        ws.title = "Jobs"

        # Freeze first row
        ws.freeze_panes = "A2"

        # Bold headers
        bold_font = Font(bold=True)
        for col_num, header in enumerate(headers, 1):
            cell = ws.cell(row=1, column=col_num, value=header)
            cell.font = bold_font

        # Write data rows
        for row_num, row_data in enumerate(rows, 2):
            for col_num, header in enumerate(headers, 1):
                ws.cell(row=row_num, column=col_num, value=row_data.get(header, ""))

        # Auto-size columns based on maximum content length
        for col in ws.columns:
            max_len = 0
            col_letter = openpyxl.utils.get_column_letter(col[0].column)
            for cell in col:
                val_str = str(cell.value or "")
                if len(val_str) > max_len:
                    max_len = len(val_str)
            ws.column_dimensions[col_letter].width = min(max(max_len + 3, 10), 50)

        try:
            wb.save(path)
        except PermissionError as exc:
            raise PermissionError(f"Permission denied to write Excel file: {path}") from exc

    def export_json(self, path: str | Path) -> None:
        """Export stored jobs to JSON format, preserving raw_json correctly."""
        path = Path(path)
        if not path.parent.exists():
            raise FileNotFoundError(f"Output directory does not exist: {path.parent}")

        jobs = self.repository.get_all_jobs()
        json_data = []
        for job in jobs:
            json_data.append({
                "job_title": job.job_title or "",
                "company_name": job.company_name or "",
                "company_url": job.company_url or "",
                "linkedin_job_url": job.linkedin_job_url or "",
                "job_id": job.job_id or "",
                "location": job.location or "",
                "country": job.country or "",
                "workplace_type": job.workplace_type or "",
                "employment_type": job.employment_type or "",
                "experience_level": job.experience_level or "",
                "salary": job.salary or "",
                "currency": job.currency or "",
                "description": job.description or "",
                "job_summary": job.job_summary or "",
                "skills": job.skills,
                "industry": job.industry or "",
                "benefits": job.benefits or "",
                "recruiter": job.recruiter or "",
                "recruiter_url": job.recruiter_url or "",
                "company_logo": job.company_logo or "",
                "company_size": job.company_size or "",
                "application_url": job.application_url or "",
                "easy_apply": job.easy_apply,
                "posted_date": job.posted_date.isoformat() if job.posted_date else None,
                "scraped_timestamp": job.scraped_timestamp.isoformat() if job.scraped_timestamp else None,
                "raw_json": job.raw_json,
            })

        try:
            with open(path, mode="w", encoding="utf-8") as f:
                json.dump(json_data, f, indent=4, ensure_ascii=False)
        except PermissionError as exc:
            raise PermissionError(f"Permission denied to write JSON file: {path}") from exc
