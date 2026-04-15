"""URL and PDF ingest service.

Fetches a URL or PDF, extracts clean text, and returns it for RAG ingestion.
Includes SSRF protection to block requests to private/internal IP ranges.

See DECISIONS.md DEC-15 for the choice of httpx+bs4 over headless browser.
"""

import ipaddress
import logging
import socket
from urllib.parse import urlparse

import httpx

from src.exceptions import ValidationError

logger = logging.getLogger(__name__)

# RFC 1918 + loopback + link-local private ranges
_PRIVATE_NETWORKS = [
    ipaddress.ip_network("10.0.0.0/8"),
    ipaddress.ip_network("172.16.0.0/12"),
    ipaddress.ip_network("192.168.0.0/16"),
    ipaddress.ip_network("127.0.0.0/8"),
    ipaddress.ip_network("169.254.0.0/16"),
    ipaddress.ip_network("::1/128"),
    ipaddress.ip_network("fc00::/7"),
    ipaddress.ip_network("fe80::/10"),
]


def _is_private_ip(host: str) -> bool:
    """Return True if host resolves to a private/internal IP address."""
    try:
        addr = ipaddress.ip_address(host)
    except ValueError:
        try:
            resolved = socket.gethostbyname(host)
            addr = ipaddress.ip_address(resolved)
        except OSError:
            return False  # can't resolve — let httpx handle the error naturally
    return any(addr in net for net in _PRIVATE_NETWORKS)


def _validate_url(url: str) -> None:
    """Raise ValidationError if the URL is not safe to fetch."""
    parsed = urlparse(url)
    if parsed.scheme not in ("http", "https"):
        raise ValidationError(f"URL scheme '{parsed.scheme}' is not allowed. Use http or https.")
    host = parsed.hostname or ""
    if not host:
        raise ValidationError("URL must include a valid hostname.")
    if _is_private_ip(host):
        raise ValidationError("Requests to private or internal IP addresses are not allowed.")


class IngestService:
    """Fetches URLs/PDFs and extracts clean text for RAG ingestion."""

    async def fetch_url(self, url: str) -> str:
        """
        Fetch a URL and return clean extracted text.

        Raises:
            ValidationError: If the URL is unsafe (bad scheme, private IP).
            ValidationError: If the fetch fails or content is empty.
        """
        _validate_url(url)

        try:
            async with httpx.AsyncClient(
                timeout=30.0,
                follow_redirects=True,
                headers={"User-Agent": "AI-Agent-Ingest/1.0"},
            ) as client:
                response = await client.get(url)
                response.raise_for_status()
        except httpx.HTTPStatusError as e:
            raise ValidationError(f"URL fetch failed with HTTP {e.response.status_code}: {url}")
        except httpx.RequestError as e:
            raise ValidationError(f"URL fetch failed: {e}")

        content_type = response.headers.get("content-type", "")
        if "pdf" in content_type or url.lower().rstrip("?#").endswith(".pdf"):
            text = self._extract_pdf(response.content)
        else:
            text = self._extract_html(response.text)

        text = text.strip()
        if not text:
            raise ValidationError("No text content could be extracted from the URL.")

        return text

    def _extract_html(self, html: str) -> str:
        """Strip HTML tags and return readable text."""
        from bs4 import BeautifulSoup

        soup = BeautifulSoup(html, "html.parser")
        for tag in soup(["script", "style", "nav", "footer", "header", "aside"]):
            tag.decompose()
        return " ".join(soup.get_text(separator=" ").split())

    def _extract_pdf(self, content: bytes) -> str:
        """Extract text from PDF bytes."""
        import io

        from pypdf import PdfReader

        reader = PdfReader(io.BytesIO(content))
        pages = [page.extract_text() or "" for page in reader.pages]
        return "\n".join(pages)
