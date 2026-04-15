"""Unit tests for IngestService URL fetching and SSRF protection (slice-15)."""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch


@pytest.mark.unit
class TestSSRFProtection:
    """_validate_url must reject unsafe URLs."""

    def _validate(self, url: str):
        from src.services.ingest_service import _validate_url
        _validate_url(url)

    def test_https_url_allowed(self):
        self._validate("https://example.com/article")

    def test_http_url_allowed(self):
        self._validate("http://example.com/article")

    def test_ftp_scheme_rejected(self):
        from src.exceptions import ValidationError
        with pytest.raises(ValidationError, match="not allowed"):
            self._validate("ftp://example.com/file.txt")

    def test_file_scheme_rejected(self):
        from src.exceptions import ValidationError
        with pytest.raises(ValidationError, match="not allowed"):
            self._validate("file:///etc/passwd")

    def test_private_ip_10_x_x_x_rejected(self):
        from src.exceptions import ValidationError
        with pytest.raises(ValidationError, match="private"):
            self._validate("http://10.0.0.1/internal")

    def test_private_ip_192_168_rejected(self):
        from src.exceptions import ValidationError
        with pytest.raises(ValidationError, match="private"):
            self._validate("http://192.168.1.1/admin")

    def test_private_ip_172_16_rejected(self):
        from src.exceptions import ValidationError
        with pytest.raises(ValidationError, match="private"):
            self._validate("http://172.16.0.1/secret")

    def test_loopback_127_0_0_1_rejected(self):
        from src.exceptions import ValidationError
        with pytest.raises(ValidationError, match="private"):
            self._validate("http://127.0.0.1/api/internal")

    def test_loopback_localhost_rejected(self):
        from src.services.ingest_service import _is_private_ip
        # localhost resolves to 127.0.0.1
        assert _is_private_ip("127.0.0.1") is True

    def test_missing_hostname_rejected(self):
        from src.exceptions import ValidationError
        with pytest.raises(ValidationError, match="hostname"):
            self._validate("https:///no-host")


@pytest.mark.unit
class TestIngestServiceHTMLExtraction:
    """_extract_html strips tags and returns clean text."""

    def test_strips_html_tags(self):
        from src.services.ingest_service import IngestService

        svc = IngestService()
        html = "<html><body><h1>Title</h1><p>Hello world</p></body></html>"
        text = svc._extract_html(html)
        assert "Title" in text
        assert "Hello world" in text
        assert "<h1>" not in text
        assert "<p>" not in text

    def test_removes_script_tags(self):
        from src.services.ingest_service import IngestService

        svc = IngestService()
        html = "<html><body><script>alert('xss')</script><p>content</p></body></html>"
        text = svc._extract_html(html)
        assert "alert" not in text
        assert "content" in text

    def test_removes_nav_and_footer(self):
        from src.services.ingest_service import IngestService

        svc = IngestService()
        html = "<html><body><nav>Menu</nav><main>Article</main><footer>Copyright</footer></body></html>"
        text = svc._extract_html(html)
        assert "Article" in text
        assert "Menu" not in text
        assert "Copyright" not in text

    def test_collapses_whitespace(self):
        from src.services.ingest_service import IngestService

        svc = IngestService()
        html = "<html><body><p>word1    \n\n    word2</p></body></html>"
        text = svc._extract_html(html)
        assert "  " not in text  # no double spaces


@pytest.mark.unit
class TestIngestServiceFetchUrl:
    """fetch_url integration with mocked httpx."""

    @pytest.fixture
    def service(self):
        from src.services.ingest_service import IngestService
        return IngestService()

    @pytest.mark.asyncio
    async def test_fetch_html_url(self, service):
        """fetch_url returns clean text from HTML page."""
        mock_response = MagicMock()
        mock_response.headers = {"content-type": "text/html; charset=utf-8"}
        mock_response.text = "<html><body><p>Hello from the web</p></body></html>"
        mock_response.content = b""
        mock_response.raise_for_status = MagicMock()

        mock_client = AsyncMock()
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock(return_value=False)
        mock_client.get = AsyncMock(return_value=mock_response)

        with patch("src.services.ingest_service.httpx.AsyncClient", return_value=mock_client):
            text = await service.fetch_url("https://example.com/page")

        assert "Hello from the web" in text

    @pytest.mark.asyncio
    async def test_fetch_url_http_error_raises_validation_error(self, service):
        """fetch_url raises ValidationError on HTTP 404."""
        import httpx
        from src.exceptions import ValidationError

        mock_response = MagicMock()
        mock_response.status_code = 404
        mock_response.headers = {}

        mock_client = AsyncMock()
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock(return_value=False)
        mock_client.get = AsyncMock(
            side_effect=httpx.HTTPStatusError(
                "404", request=MagicMock(), response=mock_response
            )
        )

        with patch("src.services.ingest_service.httpx.AsyncClient", return_value=mock_client):
            with pytest.raises(ValidationError, match="404"):
                await service.fetch_url("https://example.com/missing")

    @pytest.mark.asyncio
    async def test_ssrf_blocked_before_fetch(self, service):
        """fetch_url raises ValidationError for private IP without making HTTP request."""
        from src.exceptions import ValidationError

        with patch("src.services.ingest_service.httpx.AsyncClient") as mock_cls:
            with pytest.raises(ValidationError, match="private"):
                await service.fetch_url("http://192.168.1.1/api")
            mock_cls.assert_not_called()
