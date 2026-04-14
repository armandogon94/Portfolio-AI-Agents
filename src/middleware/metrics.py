"""Request metrics middleware."""

from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint
from starlette.requests import Request
from starlette.responses import Response


class MetricsMiddleware(BaseHTTPMiddleware):
    def __init__(self, app, collector):
        super().__init__(app)
        self.collector = collector

    async def dispatch(self, request: Request, call_next: RequestResponseEndpoint) -> Response:
        try:
            response = await call_next(request)
            self.collector.record_request(request.url.path, response.status_code)
            return response
        except Exception:
            self.collector.record_request(request.url.path, 500)
            raise
