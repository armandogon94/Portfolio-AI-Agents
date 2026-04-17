"""HMAC share-token tests (slice-27, DEC-24)."""

import time

import pytest

from src.exceptions import ValidationError


@pytest.mark.unit
class TestShareToken:
    def test_mint_and_verify_roundtrip(self):
        from src.services.share_token import mint, verify

        token = mint("task-123", secret="s3cret", ttl_seconds=3600)
        assert verify(token, secret="s3cret") == "task-123"

    def test_tampered_token_fails(self):
        from src.services.share_token import mint, verify

        token = mint("task-123", secret="s3cret", ttl_seconds=3600)
        # Flip the first character of the task_id portion.
        tampered = token[:-5] + "XXXXX"
        with pytest.raises(ValidationError, match="signature"):
            verify(tampered, secret="s3cret")

    def test_expired_token_raises(self):
        from src.exceptions import AppError
        from src.services.share_token import mint, verify

        token = mint("task-123", secret="s3cret", ttl_seconds=-1)
        # ttl_seconds=-1 means expired a second ago.
        time.sleep(0.01)
        with pytest.raises(AppError) as exc_info:
            verify(token, secret="s3cret")
        assert exc_info.value.status_code == 410

    def test_rotated_secret_invalidates_prior_tokens(self):
        from src.services.share_token import mint, verify

        token = mint("task-123", secret="original", ttl_seconds=3600)
        with pytest.raises(ValidationError):
            verify(token, secret="rotated")
