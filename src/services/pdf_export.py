"""WeasyPrint-backed PDF export for run reports (slice-27, DEC-23)."""

from __future__ import annotations

import logging
import os
import platform
from pathlib import Path
from typing import Any

from jinja2 import Environment, FileSystemLoader, select_autoescape

logger = logging.getLogger(__name__)

# Apple Silicon Homebrew libs live under /opt/homebrew/lib. WeasyPrint
# shells out to libgobject/pango/etc at import time; setting this env var
# BEFORE importing weasyprint lets ctypes find them. Docker images (apt-
# installed libs) aren't affected.
if platform.system() == "Darwin":
    os.environ.setdefault("DYLD_FALLBACK_LIBRARY_PATH", "/opt/homebrew/lib")

from weasyprint import HTML  # noqa: E402  — intentionally after env shim

TEMPLATES_DIR = Path(__file__).parent.parent / "templates"
_env = Environment(
    loader=FileSystemLoader(str(TEMPLATES_DIR)),
    autoescape=select_autoescape(["html"]),
)


def render_run_html(
    *,
    task_id: str,
    topic: str,
    domain: str | None,
    result: str,
    events: list[dict[str, Any]] | None = None,
    status: str = "completed",
    duration_seconds: float = 0.0,
    disclaimer: str | None = None,
) -> str:
    """Render the read-only run-report HTML.

    Fields are whitelisted — the caller chooses what to surface. webhook_url,
    raw tool arguments, and env config must never be passed in.
    """
    template = _env.get_template("run_report.html")
    return template.render(
        task_id=task_id,
        topic=topic,
        domain=domain,
        result=result,
        events=events or [],
        status=status,
        duration_seconds=round(duration_seconds, 2),
        disclaimer=disclaimer,
    )


def render_run_pdf(**kwargs: Any) -> bytes:
    """Render a run report as PDF bytes."""
    html = render_run_html(**kwargs)
    return HTML(string=html).write_pdf()
