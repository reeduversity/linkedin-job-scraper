import os
import time
from datetime import datetime, timezone
from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import Response


class APILoggingMiddleware(BaseHTTPMiddleware):
    def __init__(self, app, log_dir: str = "logs") -> None:
        super().__init__(app)
        self.log_path = os.path.join(log_dir, "api.log")
        os.makedirs(log_dir, exist_ok=True)

    async def dispatch(self, request: Request, call_next) -> Response:
        start_time = time.time()
        timestamp = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")

        response: Response = await call_next(request)

        process_time = time.time() - start_time
        method = request.method
        url = str(request.url)
        status_code = response.status_code

        log_line = f"{timestamp} - {method} {url} - Status: {status_code} - Duration: {process_time:.4f}s\n"

        try:
            with open(self.log_path, mode="a", encoding="utf-8") as f:
                f.write(log_line)
        except Exception:
            pass

        return response
