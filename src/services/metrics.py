"""In-memory metrics collector.

See DECISIONS.md DEC-07 for rationale (JSON metrics, not Prometheus stack).
"""

import time
import threading


class MetricsCollector:
    def __init__(self):
        self._lock = threading.Lock()
        self._start_time = time.time()
        self._total_requests = 0
        self._error_count = 0
        self._endpoints: dict[str, int] = {}

    def record_request(self, path: str, status_code: int) -> None:
        with self._lock:
            self._total_requests += 1
            self._endpoints[path] = self._endpoints.get(path, 0) + 1
            if status_code >= 400:
                self._error_count += 1

    def snapshot(self) -> dict:
        with self._lock:
            return {
                "total_requests": self._total_requests,
                "error_count": self._error_count,
                "uptime_seconds": round(time.time() - self._start_time, 2),
                "endpoints": dict(self._endpoints),
            }
