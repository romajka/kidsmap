from __future__ import annotations

import hashlib
import hmac

from django.conf import settings

from catalog.services.reactions import ensure_session_key


HASH_VERSION = "v1"


def _hash(value: str) -> str:
    key = str(getattr(settings, "ANALYTICS_IDENTITY_HASH_KEY", "") or "").encode("utf-8")
    if not key:
        raise RuntimeError("ANALYTICS_IDENTITY_HASH_KEY is required for local analytics")
    digest = hmac.new(key, value.encode("utf-8"), hashlib.sha256).hexdigest()
    return f"{HASH_VERSION}:{digest}"


def analytics_identity_for_request(request) -> tuple[str, str]:
    session_key = ensure_session_key(request) or ""
    session_hash = _hash(f"session:{session_key}")
    if getattr(request.user, "is_authenticated", False):
        visitor_hash = _hash(f"user:{request.user.pk}")
    else:
        visitor_hash = _hash(f"anonymous:{session_key}")
    return visitor_hash, session_hash


def classify_device(request) -> str:
    user_agent = str(request.META.get("HTTP_USER_AGENT") or "").lower()
    if any(token in user_agent for token in ("bot", "crawler", "spider", "headless")):
        return "bot"
    if any(token in user_agent for token in ("mobile", "android", "iphone")):
        return "mobile"
    if user_agent:
        return "desktop"
    return "unknown"
