"""Test runner that resets process-global state between tests.

`TestCase` rolls back the database after every test, but two other pieces of
state survive and make results depend on execution order:

* **The cache.** Under `DJANGO_TESTING=1` the backend is a locmem instance
  shared by the whole process, so whatever a test leaves behind — a tracking
  rate-limit counter, an IndexNow dedupe marker — is still there for the next
  one.
* **The active language.** `LocaleMiddleware` activates a language per request
  and never restores it, so one client call to a `/ru/` URL leaves every later
  test running in Russian. Code that formats text outside a request then
  produces the wrong language.

Both are reset as each test starts, so every test begins from the same state no
matter what ran before it.
"""

import unittest

from django.conf import settings
from django.core.cache import cache
from django.test.runner import DiscoverRunner
from django.utils import translation


def _reset_global_state() -> None:
    cache.clear()
    translation.activate(settings.LANGUAGE_CODE)


def _with_state_reset(result_class):
    class StateResetResult(result_class):
        def startTest(self, test):
            _reset_global_state()
            super().startTest(test)

    StateResetResult.__name__ = f"StateReset{result_class.__name__}"
    return StateResetResult


class KidsMapTestRunner(DiscoverRunner):
    def get_resultclass(self):
        # Django returns None when it has no special result class of its own,
        # in which case unittest falls back to TextTestResult.
        return _with_state_reset(super().get_resultclass() or unittest.TextTestResult)
