"""HTTP and WebSocket latency middleware."""
import time
from typing import Callable

from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
import structlog

logger = structlog.get_logger("latency")


class LatencyMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        start = time.perf_counter()
        response = await call_next(request)
        ms = round((time.perf_counter() - start) * 1000, 2)
        logger.info(
            "http_latency",
            path=request.url.path,
            method=request.method,
            status=response.status_code,
            latency_ms=ms,
        )
        return response
