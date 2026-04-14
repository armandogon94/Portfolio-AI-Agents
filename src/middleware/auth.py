"""API key authentication middleware.

See DECISIONS.md DEC-01 for rationale (API key header, not JWT).
"""

import hmac

from fastapi import Request
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint
from starlette.responses import Response

from src.config.settings import settings

# Paths that never require authentication
PUBLIC_PATHS = {"/health", "/docs", "/openapi.json", "/redoc"}


class ApiKeyMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next: RequestResponseEndpoint) -> Response:
        # Skip auth for public paths
        if request.url.path in PUBLIC_PATHS:
            return await call_next(request)

        # Skip auth if no API_KEY is configured (dev mode)
        if not settings.api_key:
            return await call_next(request)

        # Validate the X-API-Key header using constant-time comparison
        api_key = request.headers.get("X-API-Key", "")
        if not hmac.compare_digest(api_key, settings.api_key):
            return JSONResponse(
                status_code=401,
                content={
                    "error": "AuthenticationError",
                    "detail": "Invalid or missing API key",
                    "status_code": 401,
                },
            )

        return await call_next(request)
