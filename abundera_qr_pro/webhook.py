from __future__ import annotations

import hashlib
import hmac
import time
from typing import Optional

DEFAULT_TOLERANCE_SECONDS = 300


class WebhookVerificationError(Exception):
    """Raised when a webhook signature cannot be verified."""


def verify_webhook_signature(
    *,
    signature: str,
    body: str | bytes,
    secret: str,
    tolerance_seconds: int = DEFAULT_TOLERANCE_SECONDS,
    now: Optional[float] = None,
) -> bool:
    """Verify a Stripe-compatible webhook signature.

    The ``X-Abundera-Signature`` header has the form ``t=<unix_ts>,v1=<hex>``.
    This function recomputes HMAC-SHA256 of ``f"{t}.{body}"`` with ``secret``
    and compares in constant time. Raises ``WebhookVerificationError`` on any
    mismatch or if the timestamp is outside ``tolerance_seconds``.

    Returns True on success.
    """
    parts = {}
    for p in signature.split(","):
        k, _, v = p.partition("=")
        parts[k] = v
    t = parts.get("t")
    v1 = parts.get("v1")
    if not t or not v1:
        raise WebhookVerificationError("invalid signature header")

    try:
        ts = int(t)
    except ValueError as e:
        raise WebhookVerificationError("invalid timestamp") from e

    now_s = int(now if now is not None else time.time())
    if abs(now_s - ts) > tolerance_seconds:
        raise WebhookVerificationError("signature timestamp outside tolerance")

    if isinstance(body, bytes):
        body_str = body.decode("utf-8")
    else:
        body_str = body

    signed = f"{t}.{body_str}".encode("utf-8")
    expected = hmac.new(secret.encode("utf-8"), signed, hashlib.sha256).hexdigest()
    if not hmac.compare_digest(expected, v1):
        raise WebhookVerificationError("signature mismatch")
    return True
