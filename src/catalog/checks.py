from django.conf import settings
from django.core.checks import Error, register
from django.utils.dateparse import parse_datetime


@register()
def analytics_configuration_check(app_configs, **kwargs):
    errors = []
    if getattr(settings, "OWNER_ANALYTICS_ENABLED", False):
        if not getattr(settings, "LOCAL_ANALYTICS_STORAGE_ENABLED", False):
            errors.append(Error("Owner analytics requires local analytics collection.", id="catalog.E103"))
        collection_start = str(getattr(settings, "ANALYTICS_COLLECTION_STARTED_AT", "") or "").strip()
        if not collection_start or parse_datetime(collection_start) is None:
            errors.append(Error("Owner analytics requires ANALYTICS_COLLECTION_STARTED_AT.", id="catalog.E104"))
    if not getattr(settings, "LOCAL_ANALYTICS_STORAGE_ENABLED", False):
        return errors
    if not str(getattr(settings, "ANALYTICS_IDENTITY_HASH_KEY", "") or "").strip():
        errors.append(Error("Local analytics requires ANALYTICS_IDENTITY_HASH_KEY.", id="catalog.E101"))
    retention = getattr(settings, "ANALYTICS_RAW_EVENT_RETENTION_DAYS", None)
    if not isinstance(retention, int) or retention < 1:
        errors.append(Error("Local analytics requires a positive ANALYTICS_RAW_EVENT_RETENTION_DAYS.", id="catalog.E102"))
    return errors
