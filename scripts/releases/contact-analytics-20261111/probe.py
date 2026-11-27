"""Read-only production-settings probe; no real user or analytics transport."""
import json
import os
from types import SimpleNamespace

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")
import django
django.setup()
from django.conf import settings
from django.contrib.auth.models import AnonymousUser
from django.test import RequestFactory, override_settings
from catalog.context_processors import _google_analytics_context

assert not settings.DEBUG and not getattr(settings, "TESTING", False)
assert settings.GOOGLE_ANALYTICS_MEASUREMENT_ID
factory = RequestFactory()
checks = 0


def check(expected, host="kidsmap.az", path="/ru/", staff=False, superuser=False, preview=False):
    global checks
    request = factory.get(path, HTTP_HOST=host)
    request.user = (SimpleNamespace(is_staff=staff, is_superuser=superuser)
                    if staff or superuser else AnonymousUser())
    request.site_preview = preview
    actual = _google_analytics_context(request)
    assert actual["google_analytics_enabled"] is expected, (host, path, staff, superuser, preview)
    assert bool(actual["google_analytics_measurement_id"]) is expected
    checks += 1


with override_settings(ALLOWED_HOSTS=["*"]):
    for prefix in ("/", "/az/", "/ru/", "/en/"):
        check(True, path=prefix)
        for suffix in ("admin/", "admin/editor/", "i18n/setlang/"):
            check(False, path=prefix + suffix)
    for host in ("localhost", "127.0.0.1", "[::1]", "testserver", "admin.kidsmap.az", "preview.kidsmap.az"):
        check(False, host=host)
    for staff, superuser in ((True, False), (False, True), (True, True)):
        check(False, staff=staff, superuser=superuser)
    check(False, preview=True)
    for path in ("/auth/login/", "/ru/auth/register/", "/en/account/favorites/"):
        check(True, path=path)
    with override_settings(TESTING=True):
        check(False)
    with override_settings(DEBUG=True):
        check(False)
print(json.dumps({"collection_boundary_checks": checks, "status": "PASS"}))
