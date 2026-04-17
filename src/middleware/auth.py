"""API key authentication middleware.

See DECISIONS.md DEC-01 for rationale (API key header, not JWT).
"""

import hmac

from fastapi import Request
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint
from starlette.responses import Response

from src.config.settings import settings

# Paths that never require authentication.
# /docs, /redoc, /openapi.json are public in development only —
# they are disabled (docs_url=None) in production (see main.py I9).
# /workflows is a read-only registry lookup used by the dashboard launcher (slice-21).
PUBLIC_PATHS = {"/health", "/docs", "/openapi.json", "/redoc", "/workflows"}


class ApiKeyMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next: RequestResponseEndpoint) -> Response:
        # Skip auth for public paths
        if request.url.path in PUBLIC_PATHS:
            return await call_next(request)
        # Twilio webhooks use X-Twilio-Signature instead of the API key (slice-26).
        if request.url.path.startswith("/voice/twiml/"):
            return await call_next(request)
        # Share links are public-by-design; the HMAC token is the authN (slice-27, DEC-24).
        if request.url.path.startswith("/share/"):
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
