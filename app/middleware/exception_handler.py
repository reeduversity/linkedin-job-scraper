import os
from datetime import datetime, timezone
from fastapi import FastAPI, Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException

from app.apify_client import (
    ApifyAuthenticationError,
    ApifyConfigurationError,
    ApifyTimeoutError,
)
from app.config_validator import ConfigurationError
from app.database import DatabaseError
from app.validation import ValidationError as AppValidationError


def log_exception_to_api_log(request: Request, exc: Exception, status_code: int) -> None:
    timestamp = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")
    log_line = (
        f"{timestamp} - ERROR - {request.method} {request.url} - "
        f"Status: {status_code} - Error: {exc.__class__.__name__}: {str(exc)}\n"
    )
    log_path = "logs/api.log"
    try:
        os.makedirs("logs", exist_ok=True)
        with open(log_path, mode="a", encoding="utf-8") as f:
            f.write(log_line)
    except Exception:
        pass


def setup_exception_handlers(app: FastAPI) -> None:
    @app.exception_handler(RequestValidationError)
    async def request_validation_error_handler(request: Request, exc: RequestValidationError):
        status_code = status.HTTP_400_BAD_REQUEST
        log_exception_to_api_log(request, exc, status_code)
        errors = exc.errors()
        err_msg = "; ".join([f"{'.'.join(str(l) for l in e['loc'])}: {e['msg']}" for e in errors])
        return JSONResponse(
            status_code=status_code,
            content={
                "success": False,
                "message": "Request Validation Error",
                "error": err_msg,
                "code": status_code,
            },
        )

    @app.exception_handler(AppValidationError)
    async def app_validation_error_handler(request: Request, exc: AppValidationError):
        status_code = status.HTTP_400_BAD_REQUEST
        log_exception_to_api_log(request, exc, status_code)
        return JSONResponse(
            status_code=status_code,
            content={
                "success": False,
                "message": "Validation Error",
                "error": str(exc),
                "code": status_code,
            },
        )

    @app.exception_handler(DatabaseError)
    async def database_error_handler(request: Request, exc: DatabaseError):
        status_code = status.HTTP_500_INTERNAL_SERVER_ERROR
        log_exception_to_api_log(request, exc, status_code)
        # Tests expect "Database operation failed: <original>" when DatabaseError comes from repository.
        # If DatabaseError already contains that prefix, keep as-is.
        raw = str(exc)
        prefix = "Database operation failed: "
        error_msg = raw if raw.startswith(prefix) else f"Database operation failed: {raw}"
        return JSONResponse(
            status_code=status_code,
            content={
                "success": False,
                "message": "Database Error",
                "error": error_msg,
                "code": status_code,
            },
        )


    @app.exception_handler(ApifyAuthenticationError)
    async def apify_auth_error_handler(request: Request, exc: ApifyAuthenticationError):
        status_code = status.HTTP_401_UNAUTHORIZED
        log_exception_to_api_log(request, exc, status_code)
        return JSONResponse(
            status_code=status_code,
            content={
                "success": False,
                "message": "Apify Authentication Error",
                "error": str(exc),
                "code": status_code,
            },
        )

    @app.exception_handler(ApifyConfigurationError)
    async def apify_config_error_handler(request: Request, exc: ApifyConfigurationError):
        status_code = status.HTTP_400_BAD_REQUEST
        log_exception_to_api_log(request, exc, status_code)
        return JSONResponse(
            status_code=status_code,
            content={
                "success": False,
                "message": "Apify Configuration Error",
                "error": str(exc),
                "code": status_code,
            },
        )

    @app.exception_handler(ApifyTimeoutError)
    async def apify_timeout_error_handler(request: Request, exc: ApifyTimeoutError):
        status_code = status.HTTP_504_GATEWAY_TIMEOUT
        log_exception_to_api_log(request, exc, status_code)
        return JSONResponse(
            status_code=status_code,
            content={
                "success": False,
                "message": "Apify Timeout Error",
                "error": str(exc),
                "code": status_code,
            },
        )

    @app.exception_handler(ConfigurationError)
    async def configuration_error_handler(request: Request, exc: ConfigurationError):
        status_code = status.HTTP_500_INTERNAL_SERVER_ERROR
        log_exception_to_api_log(request, exc, status_code)
        return JSONResponse(
            status_code=status_code,
            content={
                "success": False,
                "message": "Configuration Error",
                "error": str(exc),
                "code": status_code,
            },
        )

    @app.exception_handler(StarletteHTTPException)
    async def http_exception_handler(request: Request, exc: StarletteHTTPException):
        status_code = exc.status_code
        log_exception_to_api_log(request, exc, status_code)
        return JSONResponse(
            status_code=status_code,
            content={
                "success": False,
                "message": exc.detail,
                "error": exc.detail,
                "code": status_code,
            },
        )

    @app.exception_handler(Exception)
    async def general_exception_handler(request: Request, exc: Exception):
        status_code = status.HTTP_500_INTERNAL_SERVER_ERROR
        log_exception_to_api_log(request, exc, status_code)
        return JSONResponse(
            status_code=status_code,
            content={
                "success": False,
                "message": "Unexpected Server Error",
                "error": str(exc),
                "code": status_code,
            },
        )
