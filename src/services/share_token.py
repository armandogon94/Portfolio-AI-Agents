"""HMAC-signed share tokens for read-only run pages (slice-27, DEC-24).

Token shape: base64url(``task_id|exp_unix|sig``) where
``sig = HMAC-SHA256(SHARE_SECRET, task_id|exp_unix)``.

Stateless — no database row per token. Revocation is coarse: rotate
``SHARE_SECRET`` and all outstanding tokens are invalidated at once.
"""

from __future__ import annotations

import base64
import hashlib
import hmac
import time

from src.exceptions import AppError, ValidationError

_SEPARATOR = "|"


class ShareTokenExpired(AppError):
    def __init__(self, message: str = "Share link has expired"):
        super().__init__(message, status_code=410)


def mint(task_id: str, secret: str, ttl_seconds: int = 7 * 24 * 3600) -> str:
    """Mint a signed token for ``task_id``."""
    exp_unix = int(time.time()) + int(ttl_seconds)
    payload = f"{task_id}{_SEPARATOR}{exp_unix}"
    sig = _sign(payload, secret)
    body = f"{payload}{_SEPARATOR}{sig}"
    return base64.urlsafe_b64encode(body.encode("utf-8")).decode("ascii").rstrip("=")


def verify(token: str, secret: str) -> str:
    """Verify the token and return the ``task_id``.

    Raises:
        ValidationError (403): malformed or tampered.
        ShareTokenExpired (410): past the exp_unix.
    """
    try:
        pad = "=" * (-len(token) % 4)
        decoded = base64.urlsafe_b64decode(token + pad).decode("utf-8")
    except (ValueError, UnicodeDecodeError) as exc:
        raise ValidationError("Malformed share token signature") from exc

    parts = decoded.split(_SEPARATOR)
    if len(parts) != 3:
        raise ValidationError("Malformed share token signature")
    task_id, exp_str, sig = parts
    try:
        exp_unix = int(exp_str)
    except ValueError as exc:
        raise ValidationError("Malformed share token signature") from exc

    expected = _sign(f"{task_id}{_SEPARATOR}{exp_unix}", secret)
    if not hmac.compare_digest(expected, sig):
        raise ValidationError("Invalid share token signature")

    if exp_unix < int(time.time()):
        raise ShareTokenExpired()

    return task_id


def _sign(payload: str, secret: str) -> str:
    return hmac.new(
        secret.encode("utf-8"), payload.encode("utf-8"), hashlib.sha256
    ).hexdigest()
