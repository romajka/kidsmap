"""Isolate optional analytics writes from business transactions and responses."""
import logging
from django.db import DatabaseError, transaction

logger = logging.getLogger(__name__)


def persist_analytics(write, **payload) -> bool:
    try:
        with transaction.atomic():
            write(**payload)
    except DatabaseError:
        # Never include query text, identities or provider payloads in this log.
        logger.warning("Optional analytics persistence unavailable")
        return False
    return True
