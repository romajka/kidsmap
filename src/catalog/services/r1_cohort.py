"""Runtime HTTP write cohort; switching off never changes persisted R1 data."""
from django.conf import settings


def r1_writes_enabled(actor):
    mode = getattr(settings, 'TASK33_R1_WRITE_MODE', 'all')
    if mode == 'all':
        return True
    if mode != 'selected' or not getattr(actor, 'is_authenticated', False):
        return False
    raw_ids = getattr(settings, 'TASK33_R1_WRITE_USER_IDS', ())
    if not isinstance(raw_ids, (tuple, list)):
        return False
    if any(type(value) is not int or value < 1 for value in raw_ids):
        return False
    return actor.pk in raw_ids
