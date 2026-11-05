"""Shared constants and helpers for the place/event admin."""

import logging
from urllib.parse import urlparse
import re

from catalog.services.content_quality import (
    format_place_quality_errors,
)


ADMIN_DATETIME_LOCAL_FORMAT = "%Y-%m-%dT%H:%M"

DRAFT_PLACEHOLDER_NAME = "Черновик без названия"

logger = logging.getLogger("catalog.domain_admin.place")

HOME_RECOMMENDATIONS_MIN_ITEMS = 1

HOME_RECOMMENDATIONS_MAX_ITEMS = 24

def _normalized_phone(value) -> str:
    return "".join(re.findall(r"\d", value or ""))

def _normalized_url(value) -> str:
    raw = (value or "").strip().lower()
    if not raw:
        return ""
    parsed = urlparse(raw if "://" in raw else f"https://{raw}")
    host = parsed.netloc.removeprefix("www.")
    path = parsed.path.rstrip("/")
    return f"{host}{path}"

def _normalized_text(value) -> str:
    return " ".join(re.sub(r"[^\w]+", " ", (value or "").lower()).split())

def place_quality_error_labels(errors) -> str:
    return format_place_quality_errors(errors)
